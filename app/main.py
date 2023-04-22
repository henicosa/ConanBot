import os

# change the working directory to the correct directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

import schedule
import time
import conanbot

import applog



print("Started scheduling")
    
conanbot.write_calendar()
schedule.every(2).hours.do(conanbot.write_calendar)

while True:
    try:
        schedule.run_pending()
        time.sleep(60)
    except Exception as e:
        applog.error(e)
