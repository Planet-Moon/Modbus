from Modbus import modbus_device as Modbus_device

def main():
    modbus_device = Modbus_device("192.168.178.107")
    modbus_device.newRegister("test",66,1)
    a = modbus_device.read("test")
    print(a)

if __name__ == '__main__':
    main()