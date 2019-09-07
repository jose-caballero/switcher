#!/usr/bin/env python

import time
from datetime import datetime


src = open('downtime_one_ce.json').read()

now_sec = int(time.time())
extra_start = 3600
extra_end = 72000 
future_start_sec = now_sec + extra_start
future_end_sec = now_sec + extra_end
time_start_utc_str = datetime.utcfromtimestamp(future_start_sec).strftime('%FT%H:%M:%S')
time_end_utc_str = datetime.utcfromtimestamp(future_end_sec).strftime('%FT%H:%M:%S')

src = src.format(STARTTIME=time_start_utc_str,
                 ENDTIME=time_end_utc_str)
print(src)
