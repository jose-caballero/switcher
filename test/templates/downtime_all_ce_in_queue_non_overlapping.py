#!/usr/bin/env python

import time
from datetime import datetime


src = open('downtime_all_ce_in_queue.json').read()

now_sec = int(time.time())

extra_start_1 = 3600
extra_end_1 = 7200 
future_start_1_sec = now_sec + extra_start_1
future_end_1_sec = now_sec + extra_end_1
time_start_1_utc_str = datetime.utcfromtimestamp(future_start_1_sec).strftime('%FT%H:%M:%S')
time_end_1_utc_str = datetime.utcfromtimestamp(future_end_1_sec).strftime('%FT%H:%M:%S')

extra_start_2 = 21600
extra_end_2 = 25200 
future_start_2_sec = now_sec + extra_start_2
future_end_2_sec = now_sec + extra_end_2
time_start_2_utc_str = datetime.utcfromtimestamp(future_start_2_sec).strftime('%FT%H:%M:%S')
time_end_2_utc_str = datetime.utcfromtimestamp(future_end_2_sec).strftime('%FT%H:%M:%S')

src = src.format(STARTTIME1=time_start_1_utc_str,
                 ENDTIME1=time_end_1_utc_str,
                 STARTTIME2=time_start_2_utc_str,
                 ENDTIME2=time_end_2_utc_str)
print(src)






