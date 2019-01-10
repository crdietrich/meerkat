# Meerkat Development Roadmap

The overall goal of Meerkat is to streamline hardware data collection using Python, enabling rapid reliable deployment of
embedded systems.

## Priorities
1. Spatial and temporal data: GPS and Time.  All IoT data must be space and time stamped, so GPS and RTC must be available first.
1. Power measurement.  INA219 and related, as well as ADC + resistor method for simple power profiling.  When implementing new sensors, if similar enough but one is more power efficient, the lower power sensor should be implemented first.
1. Preference on bus based sensors for flexibility and common electrical connections.  Analog sensors only where no digital version is available - if so, electrical circuit implementation must be included in code source.

## General Concepts
1. Numpy Docstring style
1. Base attribute class for all devices, exposing common information and methods
1. Class attributes identical within a type of measurement - allowing hardware swapping without refactor
1. Serialization of data using JSON
1. Parser to Pandas
1. Parent Class methods for direct visualization - see Vega project http://vega.github.io/

## TODOs and Thoughts
1. MicroPython includes links to a few devices, check licenses and fork?
1. Inventory of devices available for prototyping
1. MicroPython hardware available has few variations, all have UART, SPI & I2C
1. External hook for watchdog, RTC
1. Device side web visualization of data
1. Command line tools

## Devices to consider
1. All on MicroPython website
1. INA21x current chips - fork ina21x and refactor
1. Atlas scientific - fork and refactor lighthouse i2c repos
1. General NMEA gps - fork (pynmea2)[https://github.com/Knio/pynmea2] library
1. CO2 sensors
1. More specific using ADC

## The name
Meerkats are small animals from Africa that work in groups - kind of like hardware connected to a microcontroller.
