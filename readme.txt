Smart frequency cycler for spdxl/dxlAPRS radiosonde decoder
by Wojtek SP9WPN
Licence: BSD

Default configuration is for spdxl, read relevant section below if using
original dxlAPRS.

Script uses /tmp/sonde.csv, APRS data and csv files from sonde-monitoring
websites to generate sdrtst configs to follow nearby sondes. It also
blind-scans frequency range to find unknown signals.  If a sonde is landing
nearby, a special "landing mode" is entered: scanning stops and constant
reception of landing sonde starts.

Please check the example config file (config.cfg) and edit as required.


usage: freq_cycler.py [-h] [-csv <url> | -no-external-csv] [-udplog <file>]
                      [-aprslog <IP:port>] [-remote <url>] [-slave]
                      [-aprsscan] [-c <num>] [-bc <num|percent%>] [-no-blind]
                      [-f <kHz> <kHz>] [-bflush] [-ppm <ppm>] [-agc <0|1>]
                      [-gain <gain|auto>] [-bw <kHz>] [-v | -vv | -q]
                      config output

positional arguments:
  config            configuration file (input)
  output            sdrtst config file to write to

optional arguments:
  -h, --help          show help message and exit
  -csv <url>          URL of data from external server (see below)
  -no-external-csv    disable reading CSV from external sites
  -udplog <file>      read APRS data udpgate4 log
  -aprslog <IP:port>  read APRS data from TCP connection
  -remote <url>       URL of remote control (override) file
  -slave              do not read file/web/APRS data (for multi-SDR operation,
                      see below)
  -aprsscan           enable extra 70cm APRS reception cycles
  -c <num>            RTL max open channels (default: 4)
  -bc <num|percent%>  channels reserved for blind-scanning (default: 25% of max
                      channels
  -no-blind           disable blind-scanning
  -f <kHz> <kHz>      frequency range (for multi-SDR operation, default 400000
                      406000)
  -bflush             enable buffer flush cycles (see below)
  -ppm <ppm>          RTL PPM correction
  -agc <0|1>          RTL AGC switch (default: 1 - enabled)
  -gain <gain|auto>   tuner gain setting
                      ('auto' or 0.0, 0.9, 1.4 ... 48.0, 49.6)
  -bw <kHz>           RTL max badwidth (default: 1900)
  -v                  verbose mode
  -vv                 verbose with timestamps
  -q                  quiet mode (show only errors)



                     * * *  Landing mode  * * *

One of the main features of freq_cycler is the landing mode. If a descending
sonde is detected withing the range defined in the config file, freq_cycler
starts landing mode. In this mode:
 - frequency cycling is stopped, unless another landing is detected,
 - alternate sdrtst templates will be used, if defined LdgSdrtstTemplate. This
   may reduce AFC (and use spreading described below), disable squelch etc.
 - additional frequency "spread" (frequencies around original QRG) can be added
   to mitigate transmitter drift, eg. LdgModeFreqSpread="-2 6 2" for 403.000 MHz
   will add listeners every 2 kHz from -2 to +6 kHz, ie.: 402.998, 403.002,
   403.004, 403.006
 
Landing mode ends after sonde is no longer heard or stops descending for time
defined as SignalTimeout.



                     * * *  Using with original dxlAPRS  * * *

If you're using original dxlAPRS, three extra steps have to be followed:

1. dxlAPRS does not provide /tmp/sonde.csv, so to extract information about
locally received sondes, freq_cycler needs to read log by local udpgate4. You
pgate4, ie. -l 0:/tmp/udpgate.log
Use -udplog <file> parameter to point freq_cycler to this log file.

2. As dxlAPRS does not decode PilotSondes, remove relevant section from the
config file [sonde_pilotsonde].

3. Original sdrtst config lines do not use "AFC offset", so you have to remove
SECOND element from SdrtstTemplate line in the config file.



                     * * *  Reading CSV data from the web  * * *

To share data between stations, script reads CSV-formatted list of detected
sondes from dedicated websites. New data is checked every 3 minutes. Use
-csv argument to provide URL with this data. It can be used more than once to
use multiple sources.
When -csv is not used, default list of URLs is as follow:
 * http://api.wettersonde.net/sonde_csv.php

To disable this feature completely, use -no-external-csv



                     * * *  Remote control override  * * *

The -remote argument points to URL which is checked each 90 seconds. If it is
non-empty, this file is directly copied as sdrtst configuration. During this time,
freq_cycler ceases to perform it's normal cycles. The file expires after 60
minutes or when it's no longer valid.
Two special lines may appear in the remote control file. First is eg. "#E:1562511131"
and contains file creation time (as UNIX epoch) which will be used for expiration.
Second is eg. "#G:52.1,17.4,150", which limits remote file range to 150km radius from
coordinates 52.1 017.4.



                     * * *  Tips for multi-SDR setup  * * *

Use single config file and run one instance of freq_cycler.py for every
receiver. All instances should be called with -slave option, except one which
will act as master.

Use separate output files for each sdrtst process.

You need to enable "Database" option in the config file, so all processes can
share the database. It is highly recommended to use ramdisk for database.

You can use -f option to limit frequency range for each receiver, this will
optimise coverage of band. Ranges can overlap.

Script running as slave ignores -csv, -udplog and -aprslog arguments.



                     * * *  Auto-channels  * * *

This feature sets number of available channels according to core temperature
for Raspberry Pi. The "Sensor" defines source of data. If it is an executable
(like /opt/vc/bin/vcgencmd measure_temp), it is launched and temperature is
read from output. Ordinary files (like /sys/class/thermal/thermal_zone0/temp)
are read directly. Number of channels is adjusted proportionally between
defined LowTemp and HighTemp.



                     * * *  APRS scanning  * * *

This feature allows your station to work both sondes and APRS 70cm. Extra
"APRS cycles" will be introduced which tune SDR to 432.500 frequency. You have
to redirect soundstream to software APRS decoder like direwolf.
This redirection can be made with sondeudp -D option indicating a FIFO
named pipe, which will be read by software modem. This stream is raw
single-channel (mono) during APRS cycle.
Script monitors APRS log and if something is received, longer APRS cycles
may be used.
Installation howto is in the aprs_cycles_howto.md file.



                     * * *  Sondeudp buffers flushing cycles  * * *

In older versions of dxlAPRS and spdxl (prior 22.04.2020), if number of
channels became reduced, data in dropped ones were held in sondeudp buffer
until this channel was populated again. This caused "out of order" frames being
decoded much later than they were actually received.

If you cannot upgrade to latest dxlAPRS or spdxl, use -bflush option, which
will add add a short (1.3 second) "flush cycle" using frequency outside sonde
band every time number of channels is reduced.



                     * * *  Examples  * * *

Single SDR, force PPM correction of -20, 7 channels, verbose mode:
  freq_cycler.py -ppm -20 -c 7 -v config.cfg /tmp/sdrcfg.txt

Single SDR, original dxlAPRS:
  freq_cycler.py -c 5 -udplog /tmp/dxlAPRS/log/gate.log config.cfg /tmp/sdrcfg.txt

Two SDRs, 10 channels per SDR, split band in two:
  freq_cycler.py -c 10 -f 400000 403000        config.cfg /tmp/sdrcfg0.txt
  freq_cycler.py -c 10 -f 403000 406000 -slave config.cfg /tmp/sdrcfg1.txt

Four SDRs, 5 channels pers SDR, only one dedicated to blind-scanning:
  freq_cycler.py -c 5 -no-blind -f 400000 402000        config.cfg /tmp/sdrcfg0.txt
  freq_cycler.py -c 5 -no-blind -f 402000 404000 -slave config.cfg /tmp/sdrcfg1.txt
  freq_cycler.py -c 5 -no-blind -f 404000 406000 -slave config.cfg /tmp/sdrcfg2.txt
  freq_cycler.py -c 5 -bc 5     -f 400000 406000 -slave config.cfg /tmp/sdrcfg3.txt



                     * * *  Understanding output  * * *

Unless -q is used, script will print out each new set of frequencies. You may
notice some prefixes used: plus (+) indicates the frequency is one of the
"known" you have set up in config file. Hash (#) is used for frequencies where
a live sonde is heard by other stations (see "Reading CSV...") and caret
(^) indicates sonde heard by your receiver.  Bang (!) means landing mode is
active for this frequency - frequencies won't be changed until the signal is
considered lost. A frequency without a prefix is a blind-scanning frequency.

Frequencies have also suffixes to indicate special sonde types - 'p' is for
PilotSonde, 'm' is for M10/M20, 'a' for ATMS. All other (RS41, RS92, DFM, MP3...)
have no suffix.

Asterisk with a number after channel data indicates that more than one sdrtst
entry has been created for it, due multiple templates or landing mode "spread".



                     * * *  Acknowledgements  * * *

APRS connection and parsing - original code by Tomasz SQ7BR.

