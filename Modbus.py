from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.register_read_message import ReadHoldingRegistersResponse
from typing import Union
import logging
import time
import TypeConversion as TC

logger = logging.getLogger(__name__)

class Modbus_device(object):
    def __init__(self, ipAddress:str, port:str="502", unitID:int=1):
        """Create a modbus device

        Args:
            ipAddress (str): ip address of the modbus device
            port (str, optional): Port used by TCP. Defaults to "".
            unitID (int, optional): UnitID to communicate with device. Defaults to 1.
        """
        self.ipAddress:str = ipAddress
        self.port:str = port
        if self.port:
            self.client:ModbusClient = ModbusClient(self.ipAddress, port=self.port)
        else:
            self.client:ModbusClient = ModbusClient(self.ipAddress)
        self.UnitID:int = unitID
        self.connected:bool = None
        self.connect()
        self.registers:dict[str,Modbus_register] = {}
        pass

    def connect(self):
        """Connect to modbus device
        """
        retries = 10
        i = 0
        while i < retries:
            try:
                self.connected = self.client.connect()
                if self.connected:
                    break
            except:
                logger.error("ModbusError: Connection to {}:{} failed!".format(self.ipAddress, self.port))
            i += 1
            time.sleep(2)
        if not self.connected:
            logger.error("Failed to connect to modbus device {}".format(self.ipAddress))
            exit()

    def close(self):
        """Close connection to device
        """
        try:
            self.client.close()
            self.connected = False
        except:
            logger.warning("Connection could not be closed!")

    def newRegister(self, name: str, address: int, length: int, signed:bool=False, factor:float=1, type_:str="int", unit:str="") -> bool:
        """Create a new register

        Args:
            name (str): Name of the register (will be used to write and read the register)
            address (int): Address of register
            length (int): Wordlength of the register
            signed (bool, optional): True if register value is a signed integer. Defaults to False.
            factor (float, optional): Factor to calculate value from register data. Defaults to 1.
            type_ (str, optional): Datatype of the register. Possible types: int, float, bool. Defaults to "int".
            unit (str, optional): Unit string of the value, e. g. " Wh" or " °C". Defaults to "".

        Returns:
            bool: true when creation was successful
        """
        self.registers[name] = Modbus_register(address, length, signed, factor, type_, unit)
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

    def read(self, name: str) -> int:
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

    def read_value(self, name: str) -> Union[float, int, bool]:
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

    def read_string(self, name: str) -> str:
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
        string = f"{name}: {str(value)} {unit}"
        return string

    def read_all(self) -> list:
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

class Modbus_register:
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
        self.address:int = address
        self.length:int = length
        self.response:ReadHoldingRegistersResponse = ReadHoldingRegistersResponse()
        self.data:list[int] = []
        self.error = 0
        self.signed:bool = signed
        self.factor:float = factor
        self.type:str = type_
        self.unit:str = unit
        self.value = None

    def read(self, client:ModbusClient, unitID: int) -> int:
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
        except BaseException as e:
            self.error = 1
            logger.error("Error reading "+str(client)+", "+str(e))
        assert(not self.response.isError())
        return self.response

    def get_data(self, client:ModbusClient, unitID: int) -> int:
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

    def write(self, client:ModbusClient, value: int, unitID: int):
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
