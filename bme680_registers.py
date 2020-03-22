# Memory Map, see datasheet pg 28, section 5.2
CHIPID          = 0x61

REG_CHIPID      = 0xD0
COEFF_ADDR1     = 0x89
COEFF_ADDR2     = 0xE1



REG_SOFTRESET   = 0xE0
REG_CTRL_GAS    = 0x71
REG_CTRL_HUM    = 0x72
REG_STATUS      = 0x73
REG_CTRL_MEAS   = 0x74
REG_CONFIG      = 0x75




REG_STATUS        = 0x73

REG_RESET         = 0xE0

REG_ID            = 0xD0
REG_CONFIG        = 0x75

REG_CTRL_MEAS     = 0x74
REG_CTRL_HUM      = 0x72

REG_CTRL_GAS_1    = 0x71
REG_CTRL_GAS_0    = 0x70

# REG_GAS_WAIT_X  = 0x6D...0x64
REG_GAS_WAIT_0    = 0x64

# REG_RES_HEAT_X  = 0x63...0x5A
REG_RES_HEAT_0    = 0x5A

# REG_IDAC_HEAT_X = 0x59...0x50
REG_IDAC_HEAD_0   = 0x50

REG_PDATA         = 0x1F
REG_TDATA         = 0x22
REG_HDATA         = 0x25


REG_GAS_R_LSB     = 0x2B
REG_GAS_R_MSB     = 0x2A

REG_HUM_LSB       = 0x26
REG_HUM_MSB       = 0x25

REG_TEMP_xLSB     = 0x24
REG_TEMP_LSB      = 0x23
REG_TEMP_MSB      = 0x22

REG_PRESS_xLSB    = 0x21
REG_PRESS_LSB     = 0x20
REG_PRESS_MSB     = 0x1F

REG_MEAS_STATUS   = 0x1D

SAMPLERATES       = (0, 1, 2, 4, 8, 16)
FILTERSIZES       = (0, 1, 3, 7, 15, 31, 63, 127)

RUNGAS          = 0x10