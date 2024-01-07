import asyncio
import time
import threading
def checksum(packet):
    checksum = 0
    for ch in packet:
        checksum = (checksum >> 1) + ((checksum & 1) << 15)
        checksum += ch
        checksum &= 0xffff
    # trim checksum to single byte
    checksum &= 0xff
    return hex(checksum) 
class SerialDriver:
    """
    Base class representing a high-level serial driver.
    """

    def __init__(self, interval = 1):
        self.heartBeatTime = time.time()
        self.interval = interval
        t = threading.Thread(target=self.run)
        t.daemon = True
        t.start()
        self.killStatus = False
        self.thrusters = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.tBuffer = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.mdata = b"\x00"
        

    async def send(self, data: bytes) -> None:
        # set internal data to sent data
        self.mdata = data

    async def receive(self) -> bytes:
        # check if initial two bytes are valid.
        print("Output running!")
        if (hex(self.mdata[0]) != "0x47" or hex(self.mdata[1]) != "0x44"):
            return 
        print("Valid ID!")
        # check if incoming message is valid
        if (checksum(self.mdata[:-1]) != hex(self.mdata[-1])):
            # invalid checksum.
            print("Invalid checksum")
            return
        
       
        # branch behavior based on incoming message
        print(1)
        if (hex(self.mdata[2]) == "0x2"):
            print(2)
            outData = b"\x47\x44\x03"
            if(not self.killStatus):
                print(3)
                pass
            else:
                outData += b"\01"
        elif (hex(self.mdata[2]) == "0x4"):
            #heartbeat recieved, simply return after setting the new time
            self.heartBeatTime = time.time()
            self.killStatus = False
            print(5)
            return
        elif (hex(self.mdata[2]) == "0x5"):
            outData = b"\x47\x44"
            if(not self.killStatus):
                outData += b"\x01"
            else:
                outData += b"\x00"
            self.killStatus = False
        elif (hex(self.mdata[2]) == "0x6"):
            outData = b"\x47\x44"
            if(self.killStatus):
                outData += b"\x01"
            else:
                outData += b"\x00"
            self.killStatus = True
        elif (hex(self.mdata[2]) == "0x7"):
            outData = b"\x47\x44"
        elif (hex(self.mdata[2]) == "0x00" or hex(self.mdata[2]) == "0x01"):
            outData = b"\x47\x44\x01"
        else:
            # message is invalid. do nothing.
            print(4)
            return
        
        #append checksum to the end of the message  
        outCheck = checksum(outData)
        outCheck = int(outCheck, 16)
        outData += outCheck.to_bytes(1)

        for byte in outData:
            print(hex(byte))
        print(6)
        return outData
    def run(self):
        #implement the timer function for heartbeat
        
        while(True):
            if(time.time() - self.heartBeatTime >= 1):
                self.killStatus = True
            if (self.killStatus):
                for thruster in self.thrusters:
                    thruster = 0.0
            else:
                self.thrusters = self.tBuffer
                      
        

async def main():
    driver = SerialDriver()

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
    # 0x36 - checksum
    assert await driver.receive() == b"\x47\x44\x03\x36"

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
    time.sleep(100)
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


if __name__ == "__main__":
    asyncio.run(main())
