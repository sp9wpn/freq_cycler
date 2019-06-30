#!/usr/bin/python2 -u

# by Wojtek SP9WPN
# v1.7 (30.06.2019)
# BSD licence

import os
import sys
import re
import subprocess
import socket
import time
import sqlite3
import argparse
import ConfigParser
import signal
import urllib
import csv
import Queue
from math import sin, cos, sqrt, atan2, radians
from threading import Thread
from threading import Event


def verbose(t):
  if args.v:
    print t


default_external_urls = [
	'http://radiosondy.info/export/csv_live.php',
	'http://skp.wodzislaw.pl/sondy/last.php'
	]


argparser = argparse.ArgumentParser(description='Smart frequency cycler for dxlAPRS radiosonde decoder.')
mut_excl_group1 = argparser.add_mutually_exclusive_group()
mut_excl_group1.add_argument('-csv', metavar='<url>', action='append', help='URL of data from external server (default: see readme)')
mut_excl_group1.add_argument('-no-external-csv', action='store_true', help='disable reading CSV from external sites')

argparser.add_argument('-udplog', metavar='<file>', help='read APRS data udpgate4 log')
argparser.add_argument('-aprs', metavar='<IP:port>', action='append', help='read APRS data from TCP connection')

argparser.add_argument('-slave', action='store_true', help='do not read file/web/APRS data (for multi-SDR operation)')
argparser.add_argument('-c', metavar='<num>', help='RTL max open channels (default: 4)', default=4)
argparser.add_argument('-bc', metavar='<num|percent%>', help='channels reserved for blind-scanning (default: 25%% of max channels')
argparser.add_argument('-no-blind', action='store_true', help='disable blind-scanning')
argparser.add_argument('-f', metavar='<kHz>', nargs=2, type=int, help='frequency range (for multi-SDR operation, default 400000 406000)')
argparser.add_argument('-ppm', metavar='<ppm>', type=int, help='RTL PPM correction')
argparser.add_argument('-agc', metavar='<0|1>', help='RTL AGC switch (default: 1 - enabled)', choices=('0','1'), default=1)
argparser.add_argument('-gain', metavar='<gain|auto>', help='RTL gain setting')
argparser.add_argument('-bw', metavar='<kHz>', type=int, help='RTL max badwidth (default: 1900)', default=1900)

mut_excl_group3 = argparser.add_mutually_exclusive_group()
mut_excl_group3.add_argument('-v', action='store_true', help='verbose mode')
mut_excl_group3.add_argument('-q', action='store_true', help='quiet mode (show only errors)')

argparser.add_argument('config', help='configuration file (input)')
argparser.add_argument('output', help='sdrtst config file to write to')

args=argparser.parse_args()


if not os.path.isfile(args.config):
  print "ERROR: config file not found: " + args.config
  sys.exit()

try:
  config = ConfigParser.ConfigParser()   
  config.read(args.config)

except:
  print "ERROR: error reading config file: " + args.config
  sys.exit()


if config.has_option('main','Database') and config.get('main','Database'):
  dbfile = config.get('main','Database')
  verbose("using "+dbfile+" as database")
else:
  if args.slave:
    print "ERROR: -slave requires Database defined (check "+args.config+")"
    sys.exit()
  dbfile = ":memory:"



sonde_types = { 0: 'sonde_standard',				# RS41, RS92, DFM
                1: 'sonde_pilotsonde',
                2: 'sonde_m10'
              }


# status:
#   0 - blind scanning freq
#   1 - known possible sondes
#   2 - nearby flying (external data)
#   3 - heard by us



q = Queue.Queue()
exit_script = Event()
stop_APRS = Event()


def thread_external_sondelist(url):
  while not exit_script.is_set():
    read_csv(url,True)
    exit_script.wait(180)


def thread_read_udpgate_log(filename):
  while not exit_script.is_set():
    try:
      file = open(filename,'r')
      file.seek(0,2)

      while not exit_script.is_set():
        try:
          line = file.readline()
          if not line:
            if file.tell() != os.stat(filename)[6]:
              break
            time.sleep(1)
          else:
            APRS_decode(line,filename)

        except:
          break

      try:
        file.close()
      except:
        pass

    except:
      pass

    print "ERROR: error accessing "+str(filename)+", trying to reopen in 20s"
    exit_script.wait(20)



def thread_read_APRS(ip,port):
  port = int(port)
  need_connect = True

  verbose ("Connecting to APRS: "+ip+":"+str(port))

  while not exit_script.is_set():
    try:
      if need_connect:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip,port))
        need_connect = False

        # APRS login
        s.sendall("user N0CALL-0 -1 filter r/%.4f/%.4f/%d\n" %
                            ( config.getfloat('main','QTHlat'),
                              config.getfloat('main','QTHlon'),
                              config.getint('main','Range') ) )

      line = s.recv(1200)

      if line:
        APRS_decode(line,'aprs')
      else:
        print "APRS connection error, reconnecting in 20s"
        need_connect = True
        exit_script.wait(20)

    except (socket.timeout, socket.error) as e:
      print "APRS connection error, reconnecting in 20s"
      verbose(e)
      need_connect = True
      s.close()
      exit_script.wait(20)




def init(z1,z2):
  global config,freq_range,qth,aprs_last_cycle

  if not os.path.isfile(args.config):
    print "ERROR: config file not found: " + args.config
    sys.exit()

  verbose("reading config: " + args.config)
  try:
    config = ConfigParser.ConfigParser()   
    config.read(args.config)

  except:
    print "ERROR: error reading config file: " + args.config
    sys.exit()


  for t,t_name in dict(sonde_types).iteritems():
    if not config.has_section(t_name):
      sonde_types.pop(t)

  if len(sonde_types) == 0:
    print "ERROR: need definitions for sonde types in config file"
    sys.exit()

  if args.f:
    freq_range = (args.f[0],args.f[1])
  else:
    freq_range = (400000,406000)				# default

  qth=(config.getfloat('main','QTHlat'),config.getfloat('main','QTHlon'))

  aprs_last_cycle = time.time()





def set_blind_channels():
  global channels,blind_channels

  if args.bc:					# number of channels reserved for blind-scanning
    if args.bc[-1] == '%':
      blind_channels = int(max(1,channels * float(args.bc[:-1])/100))
    else:
      blind_channels = min(int(args.bc),channels)
  elif channels == 1:
    blind_channels = 0
  else:
    blind_channels = int(max(1,channels * 0.25))

  if args.no_blind:
    blind_channels = 0



def add_freqs(flist,landing = False):
  global channels,blind_channels

  channels = max(1,channels)

  for f in flist:
    if len(selected_freqs) >= channels:
      break

    if (     not landing
         and len(selected_freqs) >= channels-blind_channels+1
         and f[2] != 0 ):
      continue

    if args.no_blind and f[2]==0:
      continue

    if f[0] < freq_range[0] or f[0] > freq_range[1]:
      continue

    if len(selected_freqs) > 0:
      if (    f[0] - args.bw >= min([t[0] for t in selected_freqs])
           or f[0] + args.bw <= max([t[0] for t in selected_freqs]) ):
        continue

    selected_freqs.add((f[0],f[1]))



def mark_freqs_checked(freqs):
  for f in freqs:
    dbc.execute("""UPDATE freqs SET last_checked = datetime('now')
	WHERE freq = ? and type = ?""",(f[0],f[1]))

  db.commit()



def mark_landing_mode(freqs):
  for f in freqs:
    dbc.execute("""UPDATE freqs SET landing_mode = ?
		WHERE freq = ?
		  AND type = ?
	  	  AND landing_mode = '/:/AVAIL/:/' """,(args.output,f[0],f[1]))
    if ( dbc.rowcount > 0
         and not args.q ):
      print ("Entering landing mode: (%.3f)" % (f[0]/1000.0))

  db.commit()


def write_sdrtst_config(freqs):
  oldmask = os.umask (000)
  try:
    tmp=open(args.output+'.tmp','w')

    if args.ppm != None:
      tmp.write('p 5 '+str(args.ppm)+"\n")

    tmp.write('p 8 '+str(args.agc)+"\n")

    if args.gain:
      if args.gain == 'auto':
        tmp.write('p 3 1'+"\n")
      else:
        tmp.write('p 3 0'+"\n")
        tmp.write('p 4 '+ "%d" % (float(args.gain) * 10) +"\n")

  except:
    os.umask (oldmask)
    print "ERROR: error writing tmp file: " + args.output + ".tmp"
    return 0

  new_freqs = set()

  for f in sorted(freqs):
    if f[1] not in sonde_types:
      continue

    tmp.write("f %.3f" % (int(f[0])/1000.0))
    tmp.write(" "+' '.join(config.get(sonde_types[f[1]],'SdrtstTemplate').strip('"').split())+"\n")
    new_freqs.add((f[0],f[1]))

  os.umask (oldmask)
  tmp.close()

  try:
    os.rename(args.output+'.tmp',args.output)
  except:
    print "ERROR: error writing file: " + args.output + ".tmp"
    return 0


  if not args.q:
    txt = "New freqs:"

    for nf in sorted(new_freqs):
      status = db.execute("""SELECT max(status), landing_mode, serial
				FROM freqs
				WHERE freq = ?
				  AND type = ?
				  AND (	status_expire IS NULL
				     OR status_expire >= datetime('now') )
				ORDER BY landing_mode DESC, status DESC
				LIMIT 1""",
                       (nf[0],nf[1])).fetchone()

      if status[1] != None:
        txt += '  !'
      elif status[0] == 3:
        txt += '  ^'
      elif status[0] == 2:
        txt += '  #'
      elif status[0] == 1:
        txt += '  +'
      else:
        txt += '   '

      txt += "%.3f" % (int(nf[0])/1000.0)

      if nf[1] == 1:
        txt += 'p'
      elif nf[1] == 2:
        txt += 'm'
      else:
        txt += ' '

    print txt



def write_sdrtst_config_aprs():
  oldmask = os.umask (000)
  try:
    tmp=open(args.output+'.tmp','w')

    if args.ppm != None:
      tmp.write('p 5 '+str(args.ppm)+"\n")

    tmp.write('p 8 '+str(args.agc)+"\n")

    if args.gain:
      if args.gain == 'auto':
        tmp.write('p 3 1'+"\n")
      else:
        tmp.write('p 3 0'+"\n")
        tmp.write('p 4 '+ "%d" % (float(args.gain) * 10) +"\n")

  except:
    os.umask (oldmask)
    print "ERROR: error writing tmp file: " + args.output + ".tmp"
    return 0

  tmp.write(config.get('aprs_cycles','AprsSdrtstConfig').strip('"')+"\n")

  os.umask (oldmask)
  tmp.close()

  try:
    os.rename(args.output+'.tmp',args.output)
  except:
    print "ERROR: error writing file: " + args.output + ".tmp"
    return 0



def calc_distance(p1,p2):
  r = 6373.0

  lat1 = radians(float(p1[0]))
  lon1 = radians(float(p1[1]))
  lat2 = radians(float(p2[0]))
  lon2 = radians(float(p2[1]))

  dlon = lon2 - lon1
  dlat = lat2 - lat1

  a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
  c = 2 * atan2(sqrt(a), sqrt(1 - a))

  distance = r * c
  return int(distance)


def sonde_type_from_serial(s):
  if s.isdigit():
    if s[0:2] == '16' or s[0:2] == '17' or s[0:2] == '18' or s[0:2] == '19' or s[0:2] == '00':
      return 0					# DFM (standard)
    else:
      return 2					# M10
  elif s[0:1] == 'P' and not s[1:2].isdigit():
    return 1					# pilotSonde
  elif s[0:1] == 'B' and not s[1:2].isdigit():
    return 1					# pilotSonde
  elif s[0:1] == 'G' and not s[1:2].isdigit():
    return 1					# pilotSonde
  elif s[0:3] == 'DFM':
    return 0					# DFM
  else:
    return 0					# standard


def read_csv(file,external = False):
  global extra_wait

  try:
    csvreader = csv.reader(urllib.urlopen(file), delimiter=';', quoting=csv.QUOTE_NONE)
    verbose("reading "+file)
  except:
    return None

  for r in csvreader:
    try:
      sonde_type = sonde_type_from_serial(r[0])
      if sonde_type not in sonde_types:
        continue

      try:
        qrg=int(float(r[7])*1000)
      except:
        continue

      try:
        if (     external == False
             and qrg == 0
             and r[8].isdigit()
             and (time.time()-int(r[8]) <= min(config.getint('main','CycleInterval'),5)) ):
          extra_wait = 52
      except:
        pass

      try:
        if int(r[8])+(config.getint('main','SignalTimeout') * 60) < time.time():
          continue

        status_expire = int(r[8]) + config.getint('main','SignalTimeout') * 60

      except:
        status_expire = int(time.time() + config.getint('main','SignalTimeout') * 60)
        pass

      distance = calc_distance((r[1],r[2]),qth)
      if external and distance > config.getint('main','Range'):
        continue

      try:
        vs=float(r[5])
      except:
        vs=0.0

      # serial, freq, type, status, last_alt, status_expire, distance, vs
      if external:
        q.put((r[0],qrg,sonde_type,2,int(r[3]),status_expire,distance,vs))
      else:
        q.put((r[0],qrg,sonde_type,3,int(r[3]),status_expire,distance,vs))
      verbose(" ..  %-9s  %8.5f  %8.5f  %5dm  %5.1fm/s  %.3fMHz" % (r[0], float(r[1]), float(r[2]), int(r[3]), vs, qrg/1000.0 ))

    except:
      continue
 


def APRS_decode(line,source=''):
  line.strip()

  try:
    if (line and line.find(":;")>-0):
      line_parts=line.split(":;")
      if (source != 'aprs' and line_parts[0].find(" U:")==-1):
        return None

      info=line_parts[1]

      #L4340196 *220443h5120.90N/01952.39EO182/001/A=000743!wJ(!Clb=-0.6m/s f=404.50MHz BK=Off

      sonde_id=info[:9].strip()
      lat=float(info[17:19])+float(info[19:21])/60+float(info[22:24])/60/100
      lon=float(info[26:29])+float(info[29:31])/60+float(info[32:34])/60/100

      if not ( info[25:26] == '/' and info[35:36] == 'O' ):
        return None						# not /O (balloon)

      m=re.search('(?<=A=)\w+',info)
      if m:
        alt=int(int(m.group(0))/3.2808)
      else:
        return None

      m=re.search('\sf=([0-9]{3}\.[0-9]+)(MHz)?',info)
      if m:
        qrg=m.group(1)
      else:
        m=re.search('\s([0-9\.]+)MHz',info)
        if m:
          qrg=m.group(1)
        else:
          return None

      qrg=int(float(qrg)*1000.0)

      m=re.search('(?<=Clb=)(-?[0-9.])+',info)
      if m:
        vs=float(m.group(0))
      else:
        return None

      sonde_type = sonde_type_from_serial(sonde_id)
      if sonde_type not in sonde_types:
        return None

      distance = calc_distance((lat,lon),qth)
      status_expire = int(time.time() + config.getint('main','SignalTimeout') * 60)

      # serial, freq, type, status, last_alt, status_expire, distance, vs
      q.put((sonde_id,qrg,sonde_type,3,alt,status_expire,distance,vs))
      verbose("%s:  %-9s  %8.5f  %8.5f  %5dm  %5.1fm/s  %.3fMHz" % (source, sonde_id, lat, lon, alt, vs, qrg/1000.0 ))

  except:
    pass



def last_aprs_log_update():
  try:
    aprslog = config.get('aprs_cycles','AprsLog')

    if os.path.isdir(aprslog):
      lastupdate=0
      for file in os.listdir(aprslog):
        lastupdate=max(lastupdate,os.path.getmtime(aprslog+"/"+file))
    elif os.path.isfile(aprslog):
      lastupdate=os.path.getmtime(aprslog)

    return int(lastupdate)
  except:
    return -1


def auto_channels():
  global channels, blind_channels
  try:
    script = config.get('auto_channels','Sensor')

    if os.access(script.split()[0], os.X_OK):
      data = subprocess.check_output(script.split(' '))
    else:
      ac_file = open(script.split()[0],'r')
      data = ac_file.read(64)
      ac_file.close()

    m=re.search('([0-9]+)',data)
    temp=int(m.group(1))
    if temp > 1000:
      temp = temp / 1000

    if temp <= config.getint('auto_channels','LowTemp'):
      new_channels = config.getint('auto_channels','MaxChannels')
    elif temp >= config.getint('auto_channels','HighTemp'):
      new_channels = config.getint('auto_channels','MinChannels')
    else:
      new_channels = ( config.getint('auto_channels','MaxChannels')
                       - ( temp - config.getint('auto_channels','LowTemp') )
                       / (   ( config.getint('auto_channels','HighTemp')-config.getint('auto_channels','LowTemp') )
                           / ( config.getint('auto_channels','MaxChannels')-config.getint('auto_channels','MinChannels') ) ) )
   
    if new_channels != channels:
      verbose("auto_channels: temp=%d'C, adjusting channels to %d" % (temp, new_channels))
      channels = new_channels
      set_blind_channels()

  except:
    pass




def graceful_exit(z1,z2):
  exit_script.set()


init(None,None)
signal.signal(signal.SIGUSR1,init)
for sig in ('TERM', 'INT', 'HUP'):
  signal.signal(getattr(signal, 'SIG'+sig), graceful_exit);


if not args.slave:
  if args.no_external_csv:
    args.csv = ()
  elif args.csv == None:
    args.csv = default_external_urls


  for url in args.csv:
    t = Thread(target=thread_external_sondelist, args=(url,))
    t.daemon = True
    t.start()
    time.sleep(0.05)


  if args.aprs:
    for aprs_ip in args.aprs:
      if ':' in aprs_ip:
        (ip,port) = aprs_ip.split(':')
      else:
        ip = aprs_ip
        port = 14580

      if not ip:
        ip = '127.0.0.1'

      t = Thread(target=thread_read_APRS, args=(ip,port))
      t.daemon = True
      t.start()
      time.sleep(0.05)


  if args.udplog:
    t = Thread(target=thread_read_udpgate_log, args=(args.udplog,))
    t.daemon = True
    t.start()



extra_wait = False
channels = int(args.c)
set_blind_channels()


landing_freqs=set()
selected_freqs=set()

base_freq = 0

# connect / create database
try:
  db = sqlite3.connect(dbfile)

except:
  print "ERROR: cannot open database"
  sys.exit()

finally:
  dbc = db.cursor()
  dbc.execute("PRAGMA journal_mode = wal")

# populate database
if not args.slave:
  try:
    dbc.execute("""CREATE TABLE IF NOT EXISTS freqs (
		freq		int NOT NULL,
		serial		varchar(16),
		type		int NOT NULL,
		last_checked	datetime NOT NULL DEFAULT '1970-01-01 00:00:00',
		last_alt	int,
		status		int NOT NULL DEFAULT 0,
		landing_mode	varchar,
		distance	int,
		status_expire	datetime )""")

    dbc.execute("""CREATE UNIQUE INDEX freqs_serial ON freqs (serial)""")

  except:
    pass


  finally:
    def scan_range_generator(low,high,step):
      if step > 0:
        freq = low
        while freq <= high:
          yield freq
          freq += step

    verbose("populating database with frequencies to scan")
    dbc.execute("DELETE FROM freqs WHERE status <= 1")
    dbc.execute("VACUUM")
    db.commit()

    for t,t_name in sonde_types.iteritems():
      if config.has_option(t_name,'ScanStep') and not args.no_blind:
        for f in scan_range_generator(config.getint(t_name,'ScanRangeLow'),
		  config.getint(t_name,'ScanRangeHigh'),
		  config.getint(t_name,'ScanStep')):
          try:
            dbc.execute("""INSERT INTO freqs (freq, type)
			  VALUES (?,?)""",(f,t))
          except:
            pass

      if config.has_option(t_name,'Known'):
        for f in config.get(t_name,'Known').split():
          verbose("adding %.3f to known frequencies" % (float(f)/1000))
          dbc.execute("""INSERT INTO freqs (freq, type, status)
			  VALUES (?,?,'1')""",(f,t))

    db.commit()

else:									# slave mode
  try:
    while ( dbc.execute("SELECT name FROM sqlite_master WHERE name='freqs'").fetchone() == None
         or dbc.execute("SELECT COUNT(*) FROM freqs").fetchone() == 0 ):
      print "Waiting for master process to set up database..."
      time.sleep(5)

  except:
    print "ERROR: error connecting to database as slave"
    sys.exit()


# MAIN LOOP
while not exit_script.is_set():
  if not args.slave:

    read_csv('/tmp/sonde.csv')
    if extra_wait != False:
      extra_wait = int(max(0,extra_wait-config.getint('main','CycleInterval')))
      if extra_wait > 0:
        verbose("Probably new sonde detected, waiting %s more seconds for frame with QRG" % extra_wait)
        exit_script.wait(extra_wait)
        read_csv('/tmp/sonde.csv')

      extra_wait = False


    # process queue
    while not q.empty():
      # 0       1     2     3       4         5              6         7
      # serial, freq, type, status, last_alt, status_expire, distance, vs
      d = list(q.get())

      if d[1] == 0:
        continue;

      # round PilotSonde QRG to 5kHz
      if d[2] == 1:
        d[1] = int(round(d[1] / 5.0) * 5)

      try:
        dbc.execute("""INSERT INTO freqs (serial, freq, type, status, last_alt, status_expire, distance)
                       VALUES (?, ?, ?, ?, ?, datetime(?,'unixepoch'), ?)""",
                         (d[0], d[1], d[2], d[3], d[4], d[5], d[6]) )
      except:
        try:
          dbc.execute("""UPDATE freqs SET freq = ?, type = ?, status = ?,
				last_alt = ?, status_expire = max(status_expire,datetime(?,'unixepoch')), distance = ?
                          WHERE serial = ?
				AND abs(last_alt - ?) >= 20""",
                           (d[1], d[2], d[3], d[4], d[5], d[6], d[0], d[4]) )
        except:
          print "ERROR writing entry to database:"
          print d
          continue

      finally:
        # check for landing mode
        try:
          if ( dbc.rowcount > 0
               and int(d[4]) <= config.getint('landing_mode','Altitude')
               and d[7] < 0
               and d[6] < config.getint('landing_mode','Distance') ):
            dbc.execute("""UPDATE freqs SET landing_mode = '/:/AVAIL/:/'
                          WHERE serial = ?
				AND freq = ?
				AND type = ?
				AND status >= 2
				AND status_expire > datetime('now')
				AND landing_mode IS NULL""",
                           (d[0], d[1], d[2]) )
            if ( dbc.rowcount > 0
                 and not args.q ):
              print ("Sonde landing detected: " + d[0] + " (%.3f)" % (d[1]/1000.0))
            stop_APRS.set()
        except:
          print "ERROR when checking for landing:"
          print d
          pass

      db.commit()

    # clear expired entries
    dbc.execute("""UPDATE freqs SET landing_mode = NULL
			WHERE landing_mode IS NOT NULL
			  AND status_expire < datetime('now')""")
    dbc.execute("DELETE FROM freqs WHERE status_expire < datetime('now','-2 hours')")
    db.commit()



  # APRS cycle
  if config.has_option('aprs_cycles','AprsCycle'):
    try:
      if last_aprs_log_update() + 300 > time.time():
        verbose("APRS 70cm is active, using special APRS cycle times")
        aprs_cycle=config.getint('aprs_cycles','ActiveAprsCycle')
        aprs_interval=config.getint('aprs_cycles','ActiveAprsInterval')
      else:
        aprs_cycle=config.getint('aprs_cycles','AprsCycle')
        aprs_interval=config.getint('aprs_cycles','AprsInterval')

      if aprs_last_cycle + aprs_interval < time.time():
        if not args.q:
          if not args.v:
            print "APRS cycle"
          else:
            print "APRS cycle: %ds (interval %ds)" % (aprs_cycle,aprs_interval)

        write_sdrtst_config_aprs()
        aprs_last_cycle = time.time()
        stop_APRS.wait(aprs_cycle)
        if stop_APRS.is_set():
          print "stop_APRS Event still set"

    except:
      print "APRS cycles configuration error"
      pass


  if config.has_option('auto_channels','Sensor'):
    auto_channels()

  # select channels
  old_landing_freqs=landing_freqs

  landing_freqs=dbc.execute("""SELECT DISTINCT freq, type, 3
		FROM freqs
		WHERE status >= 2
			AND freq >= ?
			AND freq <= ?
			AND ( landing_mode = '/:/AVAIL/:/' OR landing_mode = ? )
			AND (	status_expire IS NULL
				OR status_expire >= datetime('now') )
		ORDER BY status DESC, distance ASC""",(freq_range[0],freq_range[1],args.output)).fetchall()

  freq_list=dbc.execute("""SELECT DISTINCT freq, type, status
		FROM freqs
		WHERE landing_mode IS NULL
			AND freq >= ?
			AND freq <= ?
			AND (	status_expire IS NULL
				OR status_expire >= datetime('now') )
		ORDER BY status DESC, last_checked, random()""",(freq_range[0],freq_range[1])).fetchall()


  if len(landing_freqs) > 0:
    if [[x[0],x[1]] for x in landing_freqs] != [[x[0],x[1]] for x in old_landing_freqs]:
      old_selected_freqs=selected_freqs
      selected_freqs=set()
      landing_lock = False
      add_freqs(landing_freqs,True)
      mark_landing_mode(selected_freqs)
      add_freqs(freq_list)

    else:
      landing_lock = True

  else:
    old_selected_freqs=selected_freqs
    selected_freqs=set()
    landing_lock = False

    if blind_channels >= 1:
      first_freq=dbc.execute("""SELECT freq, type, status
		FROM freqs
		WHERE	freq >= ?
			AND freq <= ?
			AND (	status_expire IS NULL
				OR status_expire >= datetime('now') )
		ORDER BY ABS(freq - ?), random()
		LIMIT 1""",(freq_range[0],freq_range[1],base_freq)).fetchall()
    else:
      first_freq=dbc.execute("""SELECT freq, type, status
		FROM freqs
		WHERE	freq >= ?
			AND freq <= ?
			AND status >= 1
			AND (	status_expire IS NULL
				OR status_expire >= datetime('now') )
		ORDER BY last_checked, random()
		LIMIT 1""",(freq_range[0],freq_range[1])).fetchall()

    base_freq = first_freq[0][0]
    base_freq += round(args.bw*0.75)
    if base_freq > freq_range[1]:
      base_freq = abs((base_freq - freq_range[1])) + freq_range[0]

    add_freqs(first_freq)
    add_freqs(freq_list)


  # write sdrtst config
  if landing_lock:
    verbose("landing mode active, doing nothing...")
  elif [[x[0],x[1]] for x in selected_freqs] != [[x[0],x[1]] for x in old_selected_freqs]:
    write_sdrtst_config(selected_freqs)
  elif len(selected_freqs)==0:
    write_sdrtst_config(())

  mark_freqs_checked(selected_freqs)


  # rinse and repeat
  verbose("")
  exit_script.wait(config.getint('main','CycleInterval'))


# graceful exit
verbose("exiting...")
time.sleep(0.1)
db.commit()
db.close()
print ""
