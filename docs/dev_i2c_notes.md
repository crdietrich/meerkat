## I2C Device Method Inventory  
### ADS1115  
Raspberry Pi using smbus:
1. smbus.write_byte
2. smbus.read_i2c_block_data = 2 bytes
3. smbus.write_i2c_block_data = 2 bytes

### MCP9808  
Raspberry Pi using smbus:
1. smbus.write_byte
2. smbus.read_i2c_block_data = 2 bytes

### MPU6050
Raspberry Pi using smbus:
1. smbus.read_byte_data = 1 byte
2. smbus.write_byte_data = 1 byte
