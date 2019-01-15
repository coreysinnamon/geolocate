import re
import geopy.distance
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

class dblock:
    def __init__(self, ip = "ip", loc = "city", lat = 0, lon = 0):
      self.ip = ip
      self.loc = loc
      self.lat = lat
      self.lon = lon
      self.time = -1
      self.ping_avg = -1
      self.ping_min = -1
      self.ping_max = -1
      self.trace_routers = []
      self.trace_num = 0

def parse_file_windows(output_file):
  stages = ["date", "header", "time", "ping", "traceroute"]
  s = 0
  locblocks = []
  n = 0
  with open(output_file) as f:
    for line in f:
      if stages[s] == "date":
        date = line.split()[1]
        s += 1
      elif stages[s] == "header":
        if re.match('.*, .*(.*,.*)', line):
          ip = line.split(",")[0]
          location = line.split(",")[1].split("(")[0].strip()
          gps = line.split("(")[1]
          latitude = float(gps.split(",")[0])
          longitude = float((gps.split(",")[1][1:]).split(")")[0])
          locblocks.append(dblock(ip, location, latitude, longitude))
          s += 1
      elif stages[s] == "time":
        if re.match('.*Time:.*', line):
          locblocks[n].time = line.split()[1]
          s+=1
      elif stages[s] == "ping":
        if re.match('.*Minimum = [0-9]*ms, Maximum = [0-9]*ms, Average = [0-9]*ms.*', line):
          ping_min = line.split("ms")[0].split()[-1]
          ping_max = line.split("ms")[1].split()[-1]
          ping_avg = line.split("ms")[2].split()[-1]
          locblocks[n].ping_min = int(ping_min)
          locblocks[n].ping_max = int(ping_max)
          locblocks[n].ping_avg = int(ping_avg)
        if re.match('.*Tracing route to.*', line):
          s += 1
      elif stages[s] == "traceroute":
        if re.match('.*Request timed out.*', line):
          router_ip = "unknown"
          locblocks[n].trace_routers.append(router_ip)
        elif re.match('.*\[[0-9\.]*\]', line):
          router_ip = line.split("[")[1].split("]")[0]
          locblocks[n].trace_routers.append(router_ip)
        elif re.match('.*Trace complete.*', line):
          locblocks[n].trace_num = len(locblocks[n].trace_routers)
          s = 1
          n += 1
  return locblocks


def parse_file_linux(output_file):
  stages = ["date", "header", "time", "ping", "traceroute"]
  s = 0
  locblocks = []
  n = 0
  with open(output_file) as f:
    for line in f:
      if stages[s] == "date":
        date = line.split()[1]
        s += 1
      elif stages[s] == "header":
        if re.match('.*, .*(.*,.*)', line):
          ip = line.split(",")[0]
          location = line.split(",")[1].split("(")[0].strip()
          gps = line.split("(")[1]
          latitude = float(gps.split(",")[0])
          longitude = float((gps.split(",")[1][1:]).split(")")[0])
          locblocks.append(dblock(ip, location, latitude, longitude))
          s += 1
      elif stages[s] == "time":
        if re.match('.*Time:.*', line):
          locblocks[n].time = line.split()[1]
          s+=1
      elif stages[s] == "ping":
        #rtt min/avg/max/mdev = 78.124/78.339/78.676/0.241 ms
        if re.match('.*rtt min/avg/max/mdev =.*', line):
          ping_min = line.split("/")[3].split()[-1]
          ping_max = line.split("/")[4]
          ping_avg = line.split("/")[5]
          locblocks[n].ping_min = float(ping_min)
          locblocks[n].ping_max = float(ping_max)
          locblocks[n].ping_avg = float(ping_avg)
        if re.match('.*Tracing route to.*', line):
          s += 1
      elif stages[s] == "traceroute":
        if re.match('.*\* *\* *\*.*', line):
          router_ip = "unknown"
          locblocks[n].trace_routers.append(router_ip)
        elif re.match('.*\([0-9\.]*\).*ms.*', line):
          router_ip = line.split("(")[1].split(")")[0]
          locblocks[n].trace_routers.append(router_ip)
        elif re.match('.*Traceroute complete.*', line):
          locblocks[n].trace_num = len(locblocks[n].trace_routers)
          s = 1
          n += 1
  return locblocks

def good_block(b):
    return b.ping_min >=0

blocks_home = parse_file_windows("outputs/outPrinceton.txt")
#home AKA princeton
blocks_prin = blocks_home
blocks_cali = parse_file_linux("outputs/outCalifornia.txt")
blocks_cana = parse_file_linux("outputs/outCanada.txt")
blocks_ohio = parse_file_linux("outputs/outOhio.txt")
blocks_oreg = parse_file_linux("outputs/outOregon.txt")
blocks_virg = parse_file_linux("outputs/outVirginia.txt")

#home
here_home = (40.3560112, -74.6505434)
#home AKA princeton
here_prin = here_home

#AWS EC2 servers
#california
here_cali = (37.3388, -121.8910)
#canada
here_cana = (45.5, -73.5833)
#ohio
here_ohio = (39.9653, -83.0235)
#oregon
here_oreg = (45.8696, -119.688)
#virginia
here_virg = (39.0481, -78.0728)

#google servers

blocks_goog_cali = parse_file_linux("outputs/outGoogleCali.txt")
blocks_goog_caro = parse_file_linux("outputs/outGoogleCaro.txt")
blocks_goog_iowa = parse_file_linux("outputs/outGoogleIowa.txt")
blocks_goog_oreg = parse_file_linux("outputs/outGoogleOreg.txt")
blocks_goog_virg = parse_file_linux("outputs/outGoogleVirg.txt")

#california
here_goog_cali = (34.052235, -118.243683)
#south carolina
here_goog_caro = (33.194790, -80.010353)
#iowa
here_goog_iowa = (41.258961, -95.854362)
#oregon
here_goog_oreg = (45.598969, -121.178940)
#virginia
here_goog_virg = (39.414989, -77.607361)
