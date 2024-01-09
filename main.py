"""
Author: Sebastian Valdes
Date: 01/08/2024
Description: This program contains a base class which represents a high-level serial driver. 
This program was written as part of an application to join the MIL at UF for Spring 2024.
This program includes code given by the template provided.
"""

# included for multithreading and ansynchronous operation
import asyncio
# used to track time for heartbeat
import time
# used to run a thread for heartbeat
import threading
# used to depack floats for thrusters.
import struct
# The following is a checksum function, which is a modified version of the wikipedia algorithm. The algorithm is modified such that the output is always 1 byte.
def checksum(packet):
    checksum = 0
    for ch in packet:
        checksum = (checksum >> 1) + ((checksum & 1) << 15)
        checksum += ch
        # trim checksum to single byte
        checksum &= 0xff
    return hex(checksum) 
# Driver Class
class SerialDriver:
    """
    Base class representing a high-level serial driver.
    """
    # Initialization of the driver
    def __init__(self, interval = 1):
        # A bool to represent the kill state of the driver
        self.killStatus = False
        # an array of floats representing the 8 thrusters.
        self.thrusters = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        # a buffer for the above thrusters, used to store the floats when the driver is turned off.
        self.tBuffer = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        # a buffer to hold the most recent message.
        self.mdata = b"\x00"
        # a variable to hold the most recent heartbeat.
        self.heartBeatTime = time.time()
        # declaration and initialization of the heartbeat() function, which is a thread controlling the heartbeat status
        self.interval = interval
        t = threading.Thread(target=self.heartbeat)
        t.daemon = True
        t.start()
        
    # The send function sends a packet to the driver. If this packet is a valid heartbeat, it will reset the heartbeat timer and unkill the driver 
    async def send(self, data: bytes) -> None:
        # set internal data to sent data
        self.mdata = data
        # heartbeat case:
        # a heartbeat can only be 1 specific message, but it requires no receive
        if (self.mdata == b"\x47\x44\x04\x1B"):
            self.heartBeatTime = time.time()
            self.killStatus = False
    # the recieve function covers functionality for responding to all packets, except heartbeat (see above)
    async def receive(self) -> bytes:
        # check if initial two bytes are valid.
        # small comment here, 4744 was an amazing class. definitely my favorite. excited to do more embedded work!
        if (hex(self.mdata[0]) != "0x47" or hex(self.mdata[1]) != "0x44"):
            return 
        # check if incoming message is valid
        if (checksum(self.mdata[:-1]) != hex(self.mdata[-1])):
            # invalid checksum.
            return
        # branch behavior based on incoming message
        # CASE: Get Kill Status
        if (hex(self.mdata[2]) == "0x2"):
            # verify length of incoming message
            if (len(self.mdata) != 4):
                return
            # set the first bytes of the outgoing message
            outData = b"\x47\x44\x03"
            # append correct byte based on current kill status.
            if(not self.killStatus):
                outData += b"\x00"
            else:
                outData += b"\x01"
        # CASE: Kill
        elif (hex(self.mdata[2]) == "0x5"):
            # verify length of incoming message
            if (len(self.mdata) != 4):
                return
            # set the first bytes of the outgoing message
            outData = b"\x47\x44"
            # append correct byte based on kill status. Cear kill status.
            if(not self.killStatus):
                outData += b"\x01"
            else:
                outData += b"\x00"
            self.killStatus = False
        # CASE: Unkill
        elif (hex(self.mdata[2]) == "0x6"):
            if (len(self.mdata) != 4):
                return
            outData = b"\x47\x44"
            # append correct byte based on kill status. Set kill status.
            if(self.killStatus):
                outData += b"\x01"
            else:
                outData += b"\x00"
            self.killStatus = True
        # CASE: Thruster adjustment
        elif (hex(self.mdata[2]) == "0x7"):
            # set initial bytes of outgoing message
            outData = b"\x47\x44"
            # Check for valid packet
            if(self.mdata[3] > 7 or self.mdata[3] < 0 or len(self.mdata) != 9 or struct.unpack('f', self.mdata[4:8])[0] > 1.0 or struct.unpack('f', self.mdata[4:8])[0] < 0.0):
                # incorrect packet: send a NACK message
                outData += b"\x01"
            else:
                # correct packet: send an ACK, and modify the thruster, if necessary
                outData += b"\x00"
                # if the device is not killed, set thrusters to new value. Update the buffer.
                if (not self.killStatus):
                    print(self.mdata[3])
                    print(self.thrusters[self.mdata[3]])
                    self.thrusters[self.mdata[3]] = struct.unpack('f', self.mdata[4:8])[0]
                    self.tBuffer[self.mdata[3]] = struct.unpack('f', self.mdata[4:8])[0]
        # CASE: ACK or NACK
        elif (hex(self.mdata[2]) == "0x00" or hex(self.mdata[2]) == "0x01"):
            outData = b"\x47\x44\x01"
        else:
            # message is invalid (or heartbeat). do nothing.
            return
        
        #append checksum to the end of the message  
        outCheck = checksum(outData)
        outCheck = int(outCheck, 16)
        # python3 requires "big" be included in this function
        outData += outCheck.to_bytes(1, "big")
        # return the message
        return outData
    
    def heartbeat(self):
        #implement the timer function for heartbeat
        # a permanent loop
        while(True):
            # if current time is greater than heartbeat by more than 1 second, set the kill status
            if(time.time() - self.heartBeatTime >= 1):
                self.killStatus = True
            # if kill status is set, the thrusters should be set to 0. if not, read from the buffer.
            if (self.killStatus):
                for thruster in self.thrusters:
                    thruster = 0.0
            else:
                self.thrusters = self.tBuffer
                      
        
# TESTING: 
# Most code here is given as a basic example by the application.
async def main():
    driver = SerialDriver()

    kill_status_packet = b"\x47\x44\x07\x04\x45\xD8\xA0\x3E\x8E"
    await driver.send(kill_status_packet)

    await driver.receive()

    # Example 1: Successful get kill status
    # 0x4744 - start of packet
    # 0x02 - packet type
    # 0x35 - checksum
    kill_status_packet = b"\x47\x44\x02\x35"
    await driver.send(kill_status_packet)
   
    # Return kill status packet
    # 0x4744 - start of packet
    # 0x03 - packet type
    # 0x00 - kill status (not set yet, we have not set it)
    # 0x1b - checksum (changed from 0x36 to account for missing byte)
    #NOTE: I changed this test case to match the above description (it was missing 0x00, and contained an incorrect checksum)
    assert await driver.receive() == b"\x47\x44\x03\x00\x1b"

    # Wait 1 second (kill will automatically trigger because no heartbeat was
    #               sent)
    await asyncio.sleep(1)
    # Example 2: Successful get kill status
    # 0x4744 - start of packet
    # 0x02 - packet type
    # 0x35 - checksum
    kill_status_packet = b"\x47\x44\x02\x35"
    await driver.send(kill_status_packet)

    # Return kill status packet
    # 0x4744 - start of packet
    # 0x03 - packet type
    # 0x01 - kill status (set because we were not sending heartbeat)
    # 0x1C - checksum
    assert await driver.receive() == b"\x47\x44\x03\x01\x1C"
    

    # Example 3: Successful thrust set packet
    # 0x4744 - start of packet
    # 0x07 - packet type
    # payload:
    # 0x04 - random thruster value
    # struct.pack("f", 0.31415) --> four bytes, speed packed as a float
    # 0x45 - byte 1 of speed
    # 0xD8 - byte 2 of speed
    # 0xA0 - byte 3 of speed
    # 0x3E - byte 4 of speed
    # 0x8E - checksum
    kill_status_packet = b"\x47\x44\x07\x04\x45\xD8\xA0\x3E\x8E"
    await driver.send(kill_status_packet)
    # Return ACK (kill is still set)
    # 0x4744 - start of packet
    # 0x00 - packet type
    # 0x33 - checksum
    assert await driver.receive() == b"\x47\x44\x00\x33"
    

    # Example 4: Finally, we can send a heartbeat! :)
    # In reality, you may want to modify this code to send heartbeats automatically,
    # so that your driver does not kill all the time. There are ways to run
    # code periodically in Python using asyncio, many of which are publicly documented
    # and in use at MIL.
    # Anyways...
    # 0x4744 - start of packet
    # 0x04 - packet type
    # 0x1B - checksum
    await driver.send(b"\x47\x44\x04\x1B")
    print("Program Complete")
if __name__ == "__main__":
    asyncio.run(main())
