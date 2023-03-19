"""Grove I2C Motor Controller Driver for Raspberry PI & MicroPython"""

from meerkat.base import time
from meerkat.data import Meta, CSVWriter, JSONWriter

class GroveMotor:

    def __init__(self, i2c_bus, bus_addr=0x0F, output='csv', name='Grove Motor Driver'):
        """Initialize Target device on i2c bus.

        Parameters
        ----------
        i2c_bus : meerkat.base.I2C or meerkat.base.STEMMA_I2C instance
        bus_addr : int, i2c bus number of this Target device
        """
        
        # i2c bus
        self.bus = i2c_bus
        self.bus.bus_addr = bus_addr

        # PWM clock frequency
        self.frequency = 31372

        # speed can be -255 to 255
        self.motor_1_speed = 0
        self.motor_2_speed = 0

        # direction of DC motor
        self.direction = ""

        # driver mode, 'dc' or 'step'
        self.mode = "dc"

        # phase of the motor being used, only applies in stepper mode
        self.phase = None

        # step code initialize
        self.step_codes_cw = None
        self.step_codes_ccw = None

        # motor phase steps, default to 2 phase
        self.set_phase(phase=2)

        # number of steps commanded
        self.steps = 0

        # running total steps, for positioning microsteps
        self.step_count = 0

        # information about this device
        self.metadata = Meta(name=name)
        self.metadata.description = ('I2C DC and stepper motor controller')
        self.metadata.urls = 'http://wiki.seeedstudio.com/Grove-I2C_Motor_Driver_V1.3/'
        self.metadata.manufacturer = 'Seeed Studio'
        
        self.metadata.header    = ['description', 'freq',
                                   'm1_speed', 'm2_speed', 'm_direction',
                                   'mode', 'phase', 'steps']
        self.metadata.dtype     = ['str', 'int', 'int', 'int', 'str', 'str', 'int', 'int']
        self.metadata.accuracy  = None
        self.metadata.precision = None
        
        self.metadata.bus_n = bus_n
        self.metadata.bus_addr = hex(bus_addr)
        
        self.writer_output = output
        self.csv_writer = CSVWriter(metadata=self.metadata, time_source='std_time_ms')
        self.json_writer = JSONWriter(metadata=self.metadata, time_source='std_time_ms')
        
    def get_info(self):
        pid = self.bus.read_register_16bit(0x00)
        return pid

    def set_phase(self, phase=2):
        """Set the phase of the stepper motor being used.
        Defaults to a 2 phase.

        Parameters
        ----------
        phase : int, either 2 or 4 for the phase of the motor design
        """

        if phase == 4:
            # 4 phase motor
            self.step_codes_cw  = [0b0001, 0b0011, 0b0010, 0b0110,
                                   0b0100, 0b1100, 0b1000, 0b1001]
            self.step_codes_ccw = [0b1000, 0b1100, 0b0100, 0b0110,
                                   0b0010, 0b0011, 0b0001, 0b1001]
            self.phase = 4
        else:
            # default to 2 phase motor
            self.step_codes_cw  = [0b0001, 0b0101, 0b0100, 0b0110,
                                   0b0010, 0b1010, 0b1000, 0b1001]
            self.step_codes_ccw = [0b1000, 0b1010, 0b0010, 0b0110,
                                   0b0100, 0b0101, 0b0001, 0b1001]
            self.phase = 2

    def set_frequency(self, f_Hz=31372):
        """Set the frequency of the PWM cycle where
            cycle length = 510
            system_clock = 16MHz

        Available frequencies in Hz: 31372, 3921, 490, 122, 30

        Parameters
        ----------
        f_Hz : int, frequencey in Hertz (Hz).  Default is 31372
        """
        freq_mapper = {31372: 0x01, 3921: 0x02, 490: 0x03, 122: 0x04, 30: 0x05}
        self.frequency = freq_mapper[f_Hz]
        self.bus.write_n_bytes([0x84, self.frequency, 0x01])

    def set_speed(self, motor_id, motor_speed):
        """Set the speed (duty cycle) of motor

        Parameters
        ----------
        motor_id : int, either 1 or 2 where 1 = J1 and 2 = J5 on the board
        motor_speed : int, between -255 and 255 where > 0 is clockwise
        """
        assert (motor_speed > -256) & (motor_speed < 256)
        if motor_id == 1:
            self.motor_1_speed = motor_speed
        if motor_id == 2:
            self.motor_2_speed = motor_speed

        self.bus.write_n_bytes([0x82, self.motor_1_speed, self.motor_2_speed])

    def stop(self, motor_id=None):
        """Stop one or both motors.  Alias for set_speed(motor_id, motor_speed=0).

        Parameters
        ----------
        motor_id : int, (optional) 1 or 2 where 1 = J1 and 2 = J5 on the board.
            If not set, defaults to stopping both.
        """

        if (motor_id == 1) or (motor_id == 2):
            self.set_speed(motor_id=motor_id, motor_speed=0)
        else:
            self.set_speed(motor_id=1, motor_speed=0)
            self.set_speed(motor_id=2, motor_speed=0)

    def set_direction(self, code='cw'):
        """Set the direction of one or both motors in dc mode.

        Accepted string command codes are:
            'cw' : clockwise
            'ccw' : counter clockwise
            'm1m2cw' : motor 1 and motor 2 clockwise
            'm1m2cc' : motor 1 and motor 2 counter clockwise
            'm1cw_m2ccw' : motor 1 clockwise and motor 2 counter clockwise
            'm1ccw_m2cw' : motor 1 counter clockwise and motor 2 clockwise

        Parameters
        ----------
        code : str, command code, default is 'cw'
        """
        direction_mapper = {'cw': 0x0a, 'ccw': 0x05,
                            'm1m2cw': 0x0a, 'm1m2cc': 0x05,
                            'm1cw_m2ccw': 0x06, 'm1ccw_m2cw': 0x09}
        self.direction = direction_mapper[code]
        self.bus.write_n_bytes([0xaa, self.direction, 0x01])

    def set_mode(self, mode_type="dc"):
        if (mode_type == "full_step") or (mode_type == "micro_step"):
            self.set_speed(motor_id=1, motor_speed=255)
            self.set_speed(motor_id=2, motor_speed=255)
            self.mode = mode_type
        else:
            self.mode = "dc"

    def step_full(self, steps, delay=0.0001, verbose=False):
        """Stepper motor motion in full steps
        (four steps per step commanded)

        Parameters
        ----------
        steps : int, number of motor steps where
            positive numbers are clockwise
            negative numbers are counter clockwise
        delay : float, seconds to delay between step commands,
            default is 0.0001 seconds which smooths operation on the pi
        verbose : bool, print debug statements
        """

        self.steps = steps

        if steps > 0:
            step_codes = self.step_codes_cw
            self.direction = "step_cw"
        if steps < 0:
            step_codes = self.step_codes_ccw
            self.direction = "step_ccw"
        if steps == 0:
            self.stop()
            return

        self.set_mode(mode_type="full_step")  # set speed to 255, i.e. full current

        for _ in range(abs(steps)):
            for sc in step_codes:
                if verbose: print("{0:04b}".format(sc))
                self.bus.write_n_bytes([0xaa, sc, 0x01])
                time.sleep(delay)

        self.stop()  # set speed to 0, i.e. current off

    def step_micro(self, steps, delay=0.0001, verbose=False):
        """Stepper motor motion in micro steps
        (one step per step commanded)

        Parameters
        ----------
        steps : int, number of motor steps where
            positive numbers are clockwise
            negative numbers are counter clockwise
        delay : float, seconds to delay between step commands,
            default is 0.0001 seconds which smooths operation on the pi
        verbose : bool, print debug statements
        """

        self.steps = steps

        if steps > 0:
            step_codes = self.step_codes_cw
            self.direction = "step_cw"
        if steps < 0:
            step_codes = self.step_codes_ccw
            self.direction = "step_ccw"
        if steps == 0:
            self.stop()
            return

        self.set_mode(mode_type="micro_step")  # set speed to 255, i.e. full current

        for _ in range(abs(steps)):
            if verbose: print("n >>", _)
            ix = self.step_count * 2
            if verbose: print("ix >> ", ix)
            for sc in step_codes[ix:ix + 2]:
                if verbose: print("bin >> {0:04b}".format(sc))
                self.bus.write_n_bytes([0xaa, sc, 0x01])
                time.sleep(delay)
            self.step_count = (self.step_count + 1) % 4

        self.stop()  # set speed to 0, i.e. current off

    def get(self, description='no_description'):
        """Get formatted output.

        Parameters
        ----------
        description : char, description of data sample collected

        Returns
        -------
        data : list, data that will be saved to disk with self.write containing:
            description : str
        """
        return [description, self.frequency,
                self.motor_1_speed, self.motor_2_speed,
                self.direction, self.mode,
                self.phase, self.steps]

    def publish(self, description='no_description'):
        """Format output and save to file, formatted as either .csv or .json.

        Parameters
        ----------
        description : char, description of data sample collected

        Returns
        -------
        None, writes to disk the following data:
            description : str, description of sample
        """
        return self.json_writer.publish(self.get(description=description))

    def write(self, description='no_description'):
        """Format output and save to file, formatted as either .csv or .json.

        Parameters
        ----------
        description : char, description of data sample collected

        Returns
        -------
        None, writes to disk the following data:
            description : str, description of sample
        """
        wr = {"csv": self.csv_writer,
              "json": self.json_writer}[self.writer_output]
        wr.write(self.get(description=description))
