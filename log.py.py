"""
log  Utilities for writing log files

FUNCTIONS
    create  - Creates a log file
    write   - Writes a message to the logfile, along with a timestamp
"""

import time
import os.path

def write(file, ID, message):
    log = open(file, 'a')
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S GMT', time.gmtime())
    line = f"{timestamp}, {ID}, {message}\n"
    log.write(line)
    log.close()

def create(folder, file):
    path = os.path.join(folder, file)
    if not os.path.isfile(path):
        log = open(path, 'wt')
        log.write('TIMESTAMP,FIRE_ID,Processing_Step_Completed\n')
        log.close()



