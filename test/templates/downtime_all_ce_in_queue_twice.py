#!/usr/bin/env python

import time
from datetime import datetime


src = open('downtime_all_ce_in_queue_twice.json').read()

now_sec = int(time.time())

extra_start_1 = 3600
extra_end_1 = 7200 
future_start_1_sec = now_sec + extra_start_1
future_end_1_sec = now_sec + extra_end_1
time_start_1_utc_str = datetime.utcfromtimestamp(future_start_1_sec).strftime('%FT%H:%M:%S')
time_end_1_utc_str = datetime.utcfromtimestamp(future_end_1_sec).strftime('%FT%H:%M:%S')

extra_start_2 = 5400 
extra_end_2 = 9000
future_start_2_sec = now_sec + extra_start_2
future_end_2_sec = now_sec + extra_end_2
time_start_2_utc_str = datetime.utcfromtimestamp(future_start_2_sec).strftime('%FT%H:%M:%S')
time_end_2_utc_str = datetime.utcfromtimestamp(future_end_2_sec).strftime('%FT%H:%M:%S')

extra_start_3 = 7200
extra_end_3 = 10800 
future_start_3_sec = now_sec + extra_start_3
future_end_3_sec = now_sec + extra_end_3
time_start_3_utc_str = datetime.utcfromtimestamp(future_start_3_sec).strftime('%FT%H:%M:%S')
time_end_3_utc_str = datetime.utcfromtimestamp(future_end_3_sec).strftime('%FT%H:%M:%S')

extra_start_4 = 12600 
extra_end_4 = 14400
future_start_4_sec = now_sec + extra_start_4
future_end_4_sec = now_sec + extra_end_4
time_start_4_utc_str = datetime.utcfromtimestamp(future_start_4_sec).strftime('%FT%H:%M:%S')
time_end_4_utc_str = datetime.utcfromtimestamp(future_end_4_sec).strftime('%FT%H:%M:%S')


src = src.format(STARTTIME1=time_start_1_utc_str,
                 ENDTIME1=time_end_1_utc_str,
                 STARTTIME2=time_start_2_utc_str,
                 ENDTIME2=time_end_2_utc_str,
                 STARTTIME3=time_start_3_utc_str,
                 ENDTIME3=time_end_3_utc_str,
                 STARTTIME4=time_start_4_utc_str,
                 ENDTIME4=time_end_4_utc_str)
print(src)






