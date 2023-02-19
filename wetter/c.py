#!/usr/bin/python -u

import os
import sys
import re
import subprocess
import socket
import time
import sqlite3
import argparse
import signal
try:
    from urllib.request import urlopen		#py3
except ImportError:
    from urllib2 import urlopen			#py2
import csv
import email.utils
from datetime import datetime
import calendar
import codecs
from threading import Event




def read_csv(file):
  if not "://" in file:
    file = "file://" + file

  print(file)
  external = False

  csvreader = csv.reader(codecs.iterdecode(urlopen(file), 'utf-8'), delimiter=';', quoting=csv.QUOTE_NONE)
  print("reading "+file)

  for r in csvreader:
    i_ser = r[0]

    if i_ser == 'Serial':
      continue

    try:
      i_time = (datetime.strptime(r[1], '%Y-%m-%dT%H:%M:%S') - datetime(1970,1,1)).total_seconds()
    except:
      i_time = 0

    while i_time > time.time() + 600:
      i_time -= 3600

    print("  %-9s IN: %s    OUT: %s (%d)" % (i_ser, r[1], time.strftime('%H:%M:%S', time.localtime(i_time)), i_time) )


read_csv('/home/vvk/freq_cycler/wetter/api.txt')
