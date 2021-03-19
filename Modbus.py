from pymodbus.client.sync import ModbusTcpClient as ModbusClient
import logging
import time
import TypeConversion as TC

logger = logging.getLogger(__name__)

class modbus_device(object):
    def __init__(self, ipAddress: str, port="", unitID=1):
        """Create a modbus device

        Args:
            ipAddress (str): ip address of the modbus device
            port (str, optional): Port used by TCP. Defaults to "".
            unitID (int, optional): UnitID to communicate with device. Defaults to 1.
        """
        self.ipAddress = ipAddress
        self.port = port
        if self.port:
            self.client = ModbusClient(self.ipAddress, port=self.port)
        else:
            self.client = ModbusClient(self.ipAddress)
        self.UnitID = unitID
        self.connected = None
        self.connect()
        self.registers = {}
        pass

    def connect(self):
        """Connect to modbus device
        """
        retries = 10
        i = 0
        while i < retries:
            try:
                self.connected = self.client.connect()
                break
            except:
                logger.error("ModbusError: Connection to {}:{} failed!".format(self.ipAddress, self.port))
            i += 1
            time.sleep(2)
        if not self.connected:
            exit()

    def close(self):
        """Close connection to device
        """
        try:
            self.client.close()
            self.connected = False
        except:
            logger.warning("Connection could not be closed!")

    def newRegister(self, name: str, address: int, length: int, signed=False, factor=1, type_="int", unit=""):
        """Create new register

        Args:
            name (str): Name of the register (will be used to write and read the register)
            address (int): Address of register
            length (int): Wordlength of the register
            signed (bool, optional): True if register value is a signed integer. Defaults to False.
            factor (float, optional): Factor to calculate value from register data. Defaults to 1.
            type_ (str, optional): Datatype of the register. Possible types: int, float, bool. Defaults to "int".
            unit (str, optional): Unit string of the value, e. g. " Wh" or " °C". Defaults to "".

        Returns:
            [type]: [description]
        """
        self.registers[name] = self.modbus_register(address, length, signed, factor, type_, unit)
        test = self.read(name) # Init values
        if test:
            return True
        else:
            del self.registers[name]
            return False

    def removeRegister(self, name: str):
        """Delete register from register dictionary

        Args:
            name (str): Name of the register to remove
        """
        del self.registers[name]

    def read(self, name: str):
        """Read raw data from a modbus register

        Args:
            name (str): Name of the register

        Returns:
            int: Data read from the register
        """
        try:
            return self.registers[name].get_data(self.client, self.UnitID)
        except:
            logger.error("Error reading register "+name)

    def read_value(self, name: str):
        """Read the value from a modbus register

        Args:
            name (str): Name of the register

        Returns:
            float/int/bool: Value of the register. Datatype is specified in the register.
        """
        value = 0 # default value
        try:
            value = round(float(TC.list_to_number(self.read(name), signed=self.registers[name].signed) * self.registers[name].factor), 2)
        except Exception as e:
            logger.error("Error reading value from register "+name+", Exeption: "+str(e))

        value_type = self.registers[name].type
        if value_type == "float":
            self.registers[name].value = float(value)
        elif value_type == "int":
            self.registers[name].value = int(value)
        elif value_type == "bool":
            if value == 0.0:
                self.registers[name].value = False
            else:
                self.registers[name].value = True
        return self.registers[name].value

    def write_register(self, name: str, value: int):
        """Write data to modbus register

        Args:
            name (str): Name of the register
            value (int): Data to be written
        """
        register = self.registers[name]
        try:
            register.write(self.client, value, self.UnitID)
        except:
            logger.error("Error writing register "+name+" with value "+str(value))

    def read_string(self, name: str):
        """Read the value from a modbus register with name and unit string

        Args:
            name (str): Name of the register

        Returns:
            str: String with Name + value + unit
        """
        value = self.read_value(name)
        unit = self.registers[name].unit
        if not unit:
            unit = ""
        string = name+": "+str(value)+unit
        self.registers[name].string = string
        return string

    def read_all(self):
        """Read all modbus registers

        Returns:
            list: List of all values. [[Name, value], ... ]
        """
        ret_val = []
        for i in self.registers:
            if self.registers[i].unit :
                ret_val.append([i, round(self.read_value(i),2), self.registers[i].unit])
            else:
                ret_val.append([i, round(self.read_value(i),2), ""])
            pass
        pass
        return ret_val

    class modbus_register:
        def __init__(self, address: int, length: int, signed: bool, factor: float, type_: str, unit: str):
            """Create modbus register

            Args:
                address (int): Address of the register
                length (int): Wordlength of the register
                signed (bool): True if the register is signed
                factor (float): Factor of the register data
                type_ (str): Datatype of the register data
                unit (str): Unit of the register value
            """
            self.address = address
            self.length = length
            self.response = []
            self.data = []
            self.error = 0
            self.signed = signed
            self.factor = factor
            self.type = type_
            self.unit = unit
            self.value = None

        def read(self, client, unitID: int):
            """Read the register

            Args:
                client (modbusClient): Modbusclient of a device
                unitID (int): UnitID of the device

            Returns:
                int: Data of the register
            """
            self.error = 0
            try:
                self.response = client.read_holding_registers(self.address,count=self.length, unit=unitID)
            except Exception as e:
                self.error = 1
                logger.error("Error reading "+str(client)+", "+str(e))
            assert(not self.response.isError())
            return self.response

        def get_data(self, client, unitID: int):
            """Read last data of the register and update self.data

            Args:
                client (modbusClient): Modbusclient of a device
                unitID (int): UnitID of the device

            Returns:
                int: Data of the register
            """
            self.read(client, unitID)
            try:
                self.data = self.response.registers
                return self.data
            except:
                logger.error("Error reading "+str(client.host)+", register "+str(self.address))
            pass

        def write(self, client, value: int, unitID: int):
            """Write data to the register

            Args:
                client (modbusClient): Modbusclient of a device
                value (int): Value to be written
                unitID (int): UnitID of the device

            Raises:
                Exception: [description]
            """
            value = int(value / self.factor)
            value = TC.number_to_wordList(value, self.signed, self.length)
            if isinstance(value, list):
                if not len(value) > self.length:
                    rq = client.write_registers(self.address, value, unit=unitID)
                else:
                    raise Exception("Value too long for register. length = "+str(self.length))
            else:
                rq = client.write_registers(self.address, value, unit=unitID)
            self.value = value
