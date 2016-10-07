# Meerkat Development Roadmap

The overall goal of Meerkat is to streamline hardware use in MicroPython, enabling rapid reliable deployment of
embedded systems running MicroPython and other devices.

## General Concepts
1. Numpy Docstring style - if we want to keep company with the SciPy stack, act like it
1. Base attribute class for all devices, exposing common information and methods
1. Class attributes identical within a type of measurement - allowing hardware swapping without refactor
1. Serialization of data based on device class
1. Parser to Pandas for serialized device data
1. ???

## TODOs and Thoughts
1. MicroPython includes links to a few devices, check licenses and fork?
1. Inventory of devices available for prototyping
1. MicroPython hardware available has few variations, all have UART, SPI & I2C
1. External hook for watchdog, RTC
1. Device side web visualization of data
1. Command line tools

## Devices to consider
1. All on MicroPython website
1. INA21x current chips
1. Atlas scientific
1. General NMEA gps
1. CO2 sensors
1. More specific using ADC

## The name
Meerkats are small, furry critters from Africa that work in groups - kind of like hardware connected to a microcontroller.
Except not as furry or cute.  Or from Africa.  Ok, I just watched Meerkat Manor and we already have an animal
theme with Python and Pandas.