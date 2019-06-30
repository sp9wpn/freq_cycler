#!/usr/bin/python2
# -*- coding: UTF-8 -*-

import time
import csv
import os


def ps(row):
  try:
    t = int(row[8])
  except:
    return None

  if (t+1800 < time.time()):
    return None

  if (t+5 >= time.time()):
    ttime = "live"
  else:
    ttime = time.strftime("%-M:%S",time.gmtime(time.time()-t))

  if (float(row[5]) > 0):
    vss = u"↑"
  elif (float(row[5]) < 0):
    vss = u"↓"
  else:
    vss = u" "

  if (abs(float(row[5])) >= 9.95):
    vs = "%3d" % abs(round(float(row[5]))) + vss
  else:
    vs = "%3.1f" % abs(float(row[5])) + vss

  print (u"%5s%9s %7.4f %7.4f %5dm %s %7.3f" %
	(ttime, row[0], float(row[1]), float(row[2]), int(row[3]), vs, float(row[7])))


_=os.system("clear")
while True:
  try:
    csvreader = csv.reader(open('/tmp/sonde.csv', 'rb'), delimiter=';', quoting=csv.QUOTE_NONE)
    _=os.system("clear")
    for row in sorted(csvreader, key=lambda row: row[0]):
      ps(row)
  except:
    pass

  time.sleep(2.5)
