#!/usr/bin/python
# -*- coding: UTF-8 -*-

import time
import csv
import os
import argparse
from math import sin, cos, sqrt, atan2, radians


argparser = argparse.ArgumentParser(description='Readable presentation of spdxl live data')

argparser.add_argument('-lat', metavar='<lat>', type=float, help='Station latitude', default=0)
argparser.add_argument('-lon', metavar='<lon>', type=float, help='Station longitude', default=0)

args=argparser.parse_args()

qth=(args.lat,args.lon)


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


def sortFunc(e):
  return(e[7])


def parserow(row):
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

  if (float(row[5]) < 0):
    vss = u"↓"
  else:
    vss = u" "

  if (abs(float(row[5])) >= 9.95):
    vs = "%3d" % abs(round(float(row[5]))) + vss
  else:
    vs = "%3.1f" % abs(float(row[5])) + vss

  dist = calc_distance(qth,(row[1],row[2]))

  return (ttime, row[0], float(row[1]), float(row[2]), int(row[3]), vs, float(row[7]), dist)


_=os.system("clear")
while True:
  try:
    csvreader = csv.reader(open('/tmp/sonde.csv', 'r'), delimiter=';', quoting=csv.QUOTE_NONE)
    _=os.system("clear")
    list=[]
    for row in sorted(csvreader, key=lambda row: row[0]):
      parsed=parserow(row)
      if parsed != None:
        list.append(parsed)

    list.sort(key=sortFunc)

    for l in list:
      print (u"%5s%9s %7.4f %7.4f %5dm %s %7.3f" %
	(l[0], l[1], float(l[2]), float(l[3]), int(l[4]), l[5], float(l[6])))

  except:
    pass

  time.sleep(2.5)
