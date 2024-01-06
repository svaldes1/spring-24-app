#include <bits/stdint-uintn.h>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <thread>
#include <vector>
#include "interface.h"

#define DOCTEST_CONFIG_IMPLEMENT_WITH_MAIN
#include "doctest.h"

using std::uint8_t;
using namespace std::chrono_literals;

void show(std::vector<uint8_t>& data) {
    for (auto a : data) {
        std::cout << std::hex << (uint16_t)a << " ";
    }
    std::cout << std::endl;
}

TEST_CASE("Test set killed packet") {
    SerialDriverInterface* interface = SerialDriverFactory::createSerialDriver();

    std::vector<uint8_t> kill_status_packet{0x47, 0x44, 0x02, 0x35};
    interface->send(kill_status_packet);

    std::vector<uint8_t> output;
    interface->receive(output);

    CHECK_EQ(output, std::vector<uint8_t>{0x47, 0x44, 0x03, 0x36});

    std::this_thread::sleep_for(1s);

    kill_status_packet = {0x47, 0x44, 0x02, 0x35};
    interface->send(kill_status_packet);

    interface->receive(output);

    CHECK_EQ(output, std::vector<uint8_t>{0x47, 0x44, 0x03, 0x01, 0x1c});

    kill_status_packet = {0x47, 0x44, 0x07, 0x04, 0x45, 0xd8, 0xa0, 0x3e, 0x8e};
    interface->send(kill_status_packet);

    interface->receive(output);

    CHECK_EQ(output, std::vector<uint8_t>{0x47, 0x44, 0x00, 0x33});

    kill_status_packet = {0x47, 0x44, 0x04, 0x1b};
    interface->send(kill_status_packet);
}
