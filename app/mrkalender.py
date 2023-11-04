import feedparser
import datetime
import pytz
from icalendar import Calendar, Event, vDatetime
import os

import icaltools
import conanbot

def get_rss_items(url):
    feed = feedparser.parse(url)
    return feed.entries

def generate_mr_compare_calendar():
    ical_links = ["https://cloud.bau-ha.us/remote.php/dav/public-calendars/aQZoW4z6d8o8g7M4?export", "https://time.ludattel.de/calendar/subscribe/mrkalender"]
    conanbot.generate_joint_calendar(ical_links, "Kombinierter MR Kalender", "mrcompare")


def generate_mr_calendar():
    # Use the URL of the RSS feed of your choice:
    items = get_rss_items("https://social.bau-ha.us/@mr_door_status.rss")

    items = sorted(items, key=lambda x:x['published_parsed'])

    # Define the UTC timezone
    utc = pytz.UTC

    filtered_list = []
    current_start_item = None
    for item in items:
        if "OFFEN" in item["summary"]:
            current_start_item = item
        elif "GESCHLOSSEN" in item["summary"] and current_start_item != None:
            dtstart = utc.localize(datetime.datetime(*current_start_item["published_parsed"][:6]))
            dtend = utc.localize(datetime.datetime(*item["published_parsed"][:6]))
            filtered_list.append([dtstart, dtend])
            current_start_item = None

    events = icaltools.create_ical_events_from_timespans(filtered_list, "maschinenraum offen")

    # test if mrkalender.ics exists
    # if yes, read it and compare with new events
    # if no, write new events to mrkalender.ics
    # if events are different, write new events to mrkalender.ics

    if os.path.isfile("mrkalender.ics"):
        with open("mrkalender.ics", 'rb') as f:
            old_cal = Calendar.from_ical(f.read())
        old_events = old_cal.walk('vevent')
        events = icaltools.unite_events(events, old_events)

    cal = Calendar()
    cal.add('prodid', '-//MR Usage Calendar//m18.uni-weimar.de//')
    cal.add('version', '2.0')
    cal.add('X-COLOR', '#FFC0CB')
    cal.add('timezone', {'tzid': 'UTC'})
    for event in events:
        cal.add_component(event)
    with open("mrkalender.ics", 'wb') as f:
        f.write(cal.to_ical())

