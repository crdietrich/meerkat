Adafruit Occidentalis v0.3 Setup for Duwamish Lighthouse
(Specifics for Pi Model B, rev1)
Colin Dietrich 2015

1. Download Raspbian version >= 3.18
	https://www.raspberrypi.org/downloads/
2. Write to SD card
3. Download Adafruit Raspberry Pi Finder
	https://github.com/adafruit/Adafruit-Pi-Finder#adafruit-raspberry-pi-finderbootstrap
4. Run 	Pi Finder
	Write Down:
		IP Address, Port
	Enter:
		SSH User: pi
		SSH Password: alphapi
		Hostname: blacktie
	Ignore for Now:
		Wifi SSID
		Wifi Password
	Select Install the WebIDE
	
	Click "Bootstrap!" button
	
	Let it run for awhile...
5. Open in a terminal (Win=PuTTy)
	IP Address, Port
	At login SSH User, SSH Password
6. Since this is >3.18, Device Tree is happening.  Read this:
	https://www.raspberrypi.org/forums/viewtopic.php?t=97314
	tldr:
		sudo raspi-config
		
	Note: With a (my original raspberry-pi, ID it!), the only line that needed to be enabled was:
	dtparam=i2c0=on
7. Check availablity of i2c sensors
	~ $ sudo i2cdetect -y 0
	
8. Enable nework file sharing
	Should have been configured correctly by the Adafruit boostrap and this will already be set in smb.conf
	[pihome]
		comment= Pi Home
		path=/home/pi
		browseable=Yes
		writeable=Yes
		only guest=no
		create mask=0777
		directory mask=0777
		public=no
			
	Read this:
	http://theurbanpenguin.com/wp/?p=2415
		
9. Create SMB user/password
	~ $ sudo smbpasswd -a pi
	...and enter the password twice.
	You should get:
	Added user pi.
10. Map network drive
	In Windows7: 
		Right click on computer, Map Network Drive or Network Places (currently set to Blacktie)
			