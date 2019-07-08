## Setting up your station to receive both radiosondes and APRS on 432.500 ##

1. Firstly, you need a software APRS decoder. My choice is direwolf. It is available in Raspbian
as a binary package, so just run:
   ```
   $ sudo apt-get update
   $ sudo apt-get install direwolf
   ```
   You can also build it from sources: https://github.com/wb2osz/direwolf

2. Prepare direwolf config file. As we are not repeating packets, it's very simple one. Save it as direwolf.conf in your
home directory (eg. /home/pi/direwolf.conf)
  
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

   IGFILTER m/10
   ```

3. Create a named pipe (FIFO):
   `$ mkfifo /home/pi/direwolf.fifo`

4. Compile the stream copy program from freq_cycler suite:
   `$ gcc aprs_stream_copy.c -o aprs_stream_copy`

5. Restart sondeudp with additional parameter `-D /home/pi/direwolf.fifo`.
   Please mind that sondeudp will **_freeze_** until another process reads from the pipe!

6. Start direwolf via helper program:

   `$ freq_cycler/aprs_stream_copy /tmp/freq_cycler_aprs_cycle.tmp /home/pi/direwolf.fifo - | \
   direwolf -c /home/pi/direwolf.conf -L /var/log/direwolf/direwolf.log -r 24000 -qhd -t 0`

   Make sure "24000" is the same as in sdrtst and sondeudp

7. Adjust parameters in `[aprs_cycles]` section config.cfg to your liking.

8. Restart freq_cycler.py with extra `-aprsscan` argument.

9. For normal operation, incorporate above changes to your startup script.