import asyncio


class SerialDriver:
    """
    Base class representing a high-level serial driver.
    """

    def __init__(self):
        pass

    async def send(self, data: bytes) -> None:
        raise NotImplementedError

    async def receive(self) -> bytes:
        raise NotImplementedError


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
