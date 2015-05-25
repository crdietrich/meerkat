"""Terminal for accessing Atlas Scientific i2c sensors
Based on the Atlas Scientific supplied command line interface
Colin Dietrich 2015
"""

import time
import string

import atlas_rpi_i2c


# instance all sensors, not particularly safe, no checks done...
do = atlas_rpi_i2c.atlas_i2c(address=0x61, bus=0)
# ox = atlas_rpi_i2c.atlas_i2c(address=0x62, bus=0)
ph = atlas_rpi_i2c.atlas_i2c(address=0x63, bus=0)
ec = atlas_rpi_i2c.atlas_i2c(address=0x64, bus=0)

def help():
    """Overly verbose help string printing"""

    print("Atlas Scientific Multi-sensor control terminal")
    print("Command pass-through to individual sensors is done via comma")
    print("delimitation with the following format:")
    print("")
    print("$ device,command,parameter")
    print("")
    print("where:")
    print("    device : 2 character sensor code (do,ph,ec)")
    print("    command,parameter : sensor command and parameters described")
    print("        in the Atlas Scientific data sheets")
    print("")
    print("Note: Any commands entered are passed to the board via I2C except:")
    print("    Poll,xx.x,yy command continuously polls every xx.x seconds for")
    print("    yy samples.  If yy is omitted, sampling continues until ctrl-c.")
    print("")
    print("    Where xx.x is longer than the timeout for each sensor:")
    print("        DO = %0.2f seconds" %  do.long_timeout)
    print("        pH = %0.2f seconds" %  ph.long_timeout)
    print("        EC = %0.2f seconds" %  ec.long_timeout)
    print("")
    print("Pressing ctrl-c will stop the program and return to the terminal.")

# main loop
while True:

    # terminal raw input
    input = raw_input("Enter command $ ")

    # option to quit cleanly
    if input.upper() == "Q":
        print("Response >> Quiting...")
        break

    # get some help
    if input.upper().startswith("HELP"):
        help()
        continue

    # break input into command pieces
    command = string.split(input, ",")

    # identify which sensor communicate with
    if (command[0].upper().startswith("DO")):
        device = do
    elif (command[0].upper().startswith("PH")):
        device = ph
    elif (command[0].upper().startswith("EC")):
        device = ec
    else:
        print("Response >> No device code passed to terminal (do, ph, ec)")
        continue

    # catch a command string without enough commands and parameters
    if len(command) <= 1:
        print("Response >> Please enter a command,parameter pair. $ help for details.")
    else:
        # look for continuous polling command
        if command[1].upper().startswith("POLL"):
            delay_time = float(command[2])

            # check for polling time being too short
            # change it to the minimum timeout if too short
            if delay_time < device.long_timeout:
                print("Response >> Polling time is shorter than timeout, "
                      "setting polling time to %0.2f" %  device.long_timeout)
                delay_time =  device.long_timeout

            # get the information of the board you're polling
            info = string.split(device.query("I"), ",")[1]

            # handle optional 4th burst command
            burst = False
            if len(command) == 4:
                burst = True
                try:
                    c_end = int(command[3])
                except:
                    print("Response >> Burst value not an integer. "
                          "$ help for details.")
            else:
                print("Response >> Please enter a command,parameter pair. "
                      "$ help for details.")

            print("Response >> Polling %s sensor every %0.2f seconds, "
                  "press ctrl-c to stop polling" % (info, delay_time))

            # continuously poll the sensor
            try:
                c = 0
                while True:
                    print(device.query("R"))
                    time.sleep(delay_time - device.long_timeout)

                    # if a limited number of samples were requested
                    if burst:
                        c += 1
                        if c > c_end:
                            print("Response >> Burst complete.")
                            break

            except KeyboardInterrupt: # catches the ctrl-c command, which breaks the loop above
                print("Response >> Continuous polling stopped")

        # if not a special keyword, pass commands straight to board
        else:
            print(device.query(",".join(command[1:])))


