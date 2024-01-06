#ifndef INTERFACE_H_
#define INTERFACE_H_

#include <cstddef>
#include <cstdint>
#include <vector>

using std::uint8_t;

class SerialDriverInterface {
   public:
    virtual void send(std::vector<uint8_t>& buffer) = 0;

    virtual void receive(std::vector<uint8_t>& buffer) = 0;

    virtual uint16_t bytes_available() = 0;
};

class SerialDriverFactory {
   public:
    static SerialDriverInterface* createSerialDriver() { return nullptr; }
};

#endif  // INTERFACE_H_
