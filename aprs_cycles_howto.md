## Setting up your station to receive both radiosondes and APRS on 432.500 ##

### Introduction ###
A typical radiosonde station has all the hardware ready to receive APRS on 432,500MHz.
Of course, if you have SAW filter for 400MHz this will make it unusable for 433 band, but normally
the hardware is ready to go. All we need is some extra software.

The idea is to share receiver time between sondes and APRS frequency. Normally, this is about 50/50 share, but
if activity on APRS is detected, freq_cycler will extend this time. On the other hand, sondes during landing
get Rx exclusively for them. These times are adjustable in the config file.

### How to make this work ###
1. Firstly, you need a software APRS decoder. My choice is direwolf. It is available in Raspbian
as a binary package, so just run:
   ```
   $ sudo apt-get update
   $ sudo apt-get install direwolf
   ```
   You can also build it from sources: https://github.com/wb2osz/direwolf

2. Prepare direwolf config file. As we are not repeating packets, it's very simple one. Save it as direwolf.conf
in your home directory (eg. /home/pi/direwolf.conf)
  
   (change `N0CALL` to your callsign and put your APRS-IS password where `00000` is)

   ```
   MYCALL N0CALL-10

   ADEVICE0 stdin null
   ACHANNELS 1
   CHANNEL 0
   MODEM 1200

   KISSPORT 0
   AGWPORT 0

   IGSERVER euro.aprs2.net
   IGLOGIN N0CALL 00000
   ```

3. Create a directory for direwolf logs:
   ```
   $ sudo mkdir -p /var/log/direwolf
   $ sudo chmod 777 /var/log/direwolf
   ```
   
4. Create a named pipe (FIFO):

   `$ mkfifo /home/pi/direwolf.fifo`
   
   Remember this has to be done **_before_** starting sondeudp with `-D` parameter (see par. 6)

5. Compile the stream filter program from freq_cycler suite:

   `$ gcc aprs_stream_copy.c -o aprs_stream_copy`

6. Restart sondeudp with additional parameter `-D /home/pi/direwolf.fifo`.
   Please mind that sondeudp will **_freeze_** until another process reads from the pipe!

7. Start direwolf via helper program (this is one long line):

   ```
   $ ./aprs_stream_copy /tmp/freq_cycler_aprs_cycle.tmp /home/pi/direwolf.fifo - | direwolf -c /home/pi/direwolf.conf -l /var/log/direwolf -r 24000 -qhd -t 0
   ```

   Make sure that audio sampling (here: 24000) is the same as in sdrtst and sondeudp.

8. Adjust parameters in `[aprs_cycles]` section config.cfg to your liking.

9. AprsGPIO option in the config is used to set Raspberry Pi GPIO pin high/low during APRS cycle.
   This can be used for switching antennas and filters.

10. Restart freq_cycler.py with extra `-aprsscan` argument.

11. For normal operation, incorporate actions and changes from steps 3, 4, 6, 7, 10 above into your startup script.

