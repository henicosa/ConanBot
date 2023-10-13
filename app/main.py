import os

# change the working directory to the correct directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

import schedule
import time
import conanbot
import mrkalender

import applog



print("Started scheduling")
    
conanbot.write_calendar()
mrkalender.generate_mr_calendar()
conanbot.write_ludwig_calendar()
schedule.every(5).minutes.do(conanbot.write_ludwig_calendar)
schedule.every(2).hours.do(conanbot.write_calendar)
schedule.every(1).hours.do(mrkalender.generate_mr_calendar)

while True:
    try:
        schedule.run_pending()
        time.sleep(60)
    except Exception as e:
        applog.error(e)
