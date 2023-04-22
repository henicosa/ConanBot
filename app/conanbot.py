import icalendar
import datetime
import requests
from icalendar import vRecur
from datetime import timedelta
from datetime import time as dttime
import dateutil.rrule as rrule
import pytz
from icalendar import Event, vDatetime
import icaltools
import recurring_ical_events
import schedule
import re
import time
import applog

def invert_events(events, start, end):
    free_times = find_free_times(events, start, end)
    return create_ical_events_from_timespans(free_times)


def generate_sleep_events(timespan_start, timespan_end):
    """
    This function generates a list of events with the summary "Sleeping" for each day included in the timespan.
    The events will have a start time of 22:00 of the day before and an end time of 9:00 on the current day.

    :param timespan_start: A timezone-aware datetime object representing the start of the timespan
    :param timespan_end: A timezone-aware datetime object representing the end of the timespan
    :return: A list of icalendar.Event objects
    """
    tz = timespan_start.tzinfo
    sleep_start_time = dttime(22, 0, tzinfo=tz)
    sleep_end_time = dttime(9, 0, tzinfo=tz)
    events = []
    current_day = timespan_start
    while current_day <= timespan_end:
        sleep_start = current_day.replace(hour=sleep_start_time.hour, minute=sleep_start_time.minute, tzinfo=tz) - timedelta(days=1)
        sleep_end = current_day.replace(hour=sleep_end_time.hour, minute=sleep_end_time.minute, tzinfo=tz)
        event = icaltools.new_event()
        event.add('SUMMARY', "Sleeping")
        event.add('DTSTART', sleep_start)
        event.add('DTEND', sleep_end)
        events.append(event)
        current_day += timedelta(days=1)
    return events


def create_ical_events_from_timespans(free_times):
    """
    This function takes a list of timespans and returns a list of iCalendar events.
    Each iCalendar event will have the summary "Möglicher Termin" and dtstart and dtend 
    will be set to the start and end of each timespan respectively.
    """    
    # Create an empty list to store the iCalendar events
    ical_events = []
    # Iterate over the free times
    for start, end in free_times:
        # Create a new iCalendar event
        ical_event = icaltools.new_event()
        # Set the summary of the event
        ical_event.add('summary', 'Möglicher Conan Termin')
        # Set the start time of the event
        ical_event.add('dtstart', vDatetime(start))
        # Set the end time of the event
        ical_event.add('dtend', vDatetime(end))
        ical_event.add('color', '#FFC0CB')
        ical_event.add('transp', 'TRANSPARENT')
        # Append the event to the list of iCalendar events
        ical_events.append(ical_event)
    # Return the list of iCalendar events
    return ical_events

def find_free_times_new(events, period_start, period_end):
    # sort the events by their start time
    events = sorted(events, key=lambda event: event['DTSTART'].dt)
    # Create an empty list to store the free times
    free_times = []
    current_end = period_end
    # Iterate over events
    for event in events:
        #parse dtstart and dtend to datetime objects
        event_start = event.get('dtstart').dt
        event_end = event.get('dtend').dt
        if event_start < period_end and event_end > current_end:
            if current_end < event_start:
                free_times.append((current_end, event_start))
            if current_end < event_end:
                current_end = event_end
    if current_end < period_end:
        free_times.append((current_end, period_end))
    # Return the list of free times
    return free_times

def find_free_times(events, start_time, end_time):
    # sort the events by their start time
    events = sorted(events, key=lambda event: event['DTSTART'].dt)
    # Create an empty list to store the free times
    free_times = []
    current_time = start_time
    # Iterate over events
    for event in events:
        #parse dtstart and dtend to datetime objects
        event_start = event.get('dtstart').dt
        event_end = event.get('dtend').dt
        if event_start < end_time:
            if current_time < event_start:
                free_times.append((current_time, event_start))
            if current_time < event_end:
                current_time = event_end
    if current_time < end_time:
        free_times.append((current_time, end_time))
    # Return the list of free times
    return free_times

def define_timezone_for_event(event, timezone='Europe/Berlin'):
    dtstart = event["DTSTART"].dt
    dtend = event["DTEND"].end
    if not dtstart.tzinfo:
        dtstart = pytz.timezone(timezone).localize(dtstart)
        dtend = pytz.timezone(timezone).localize(dtend)
        event = dateutil.set_event_times(event, dtstart, dtend)
        
    return event

from datetime import timedelta

def debug(event):
    print()
    print(event["SUMMARY"])
    print(event["DTSTART"].dt.strftime("(%d.%m) %A - %H:%M [%Z]"))

def get_week_boundaries(week_of_interest, timezone='Europe/Berlin'):
    year, week_number = week_of_interest
    tz = pytz.timezone(timezone)
    first_day_of_year = datetime.datetime(year,1,1, tzinfo=tz)
    # Find the first day of the week that the first day of the year falls on
    if(first_day_of_year.weekday()>3):
        first_day_of_period = first_day_of_year + timedelta(7-first_day_of_year.weekday()) 
    else:
        first_day_of_period = first_day_of_year - timedelta(first_day_of_year.weekday())
    week_offset = timedelta(days = (week_number-1)*7)
    start_of_period = first_day_of_period + week_offset
    end_of_period = first_day_of_period + week_offset + timedelta(days=7)
    return start_of_period, end_of_period

def get_two_week_boundaries(week_of_interest, timezone='Europe/Berlin'):
    year, week_number = week_of_interest
    tz = pytz.timezone(timezone)
    first_day_of_year = datetime.datetime(year,1,1, tzinfo=tz)
    # Find the first day of the week that the first day of the year falls on
    if(first_day_of_year.weekday()>3):
        first_day_of_period = first_day_of_year + timedelta(7-first_day_of_year.weekday()) 
    else:
        first_day_of_period = first_day_of_year - timedelta(first_day_of_year.weekday())
    week_offset = timedelta(days = (week_number-1)*7)
    start_of_period = first_day_of_period + week_offset
    end_of_period = first_day_of_period + week_offset + timedelta(days=14)
    return tz.localize(datetime.datetime.now()), end_of_period


def generate_free_time_calendar(ical_links):
    # specify the week of interest

    timezone = pytz.timezone("Europe/Berlin")
    now = datetime.datetime.now(timezone)
    week_of_interest = now.isocalendar()[:2]

    start_of_period, end_of_period = get_two_week_boundaries(week_of_interest)
    # Set the time to midnight (hour, minute, second, microsecond)
    midnight = timezone.localize(datetime.datetime.combine(now.date(), dttime.min))

    start_of_period = midnight

    # fetch and parse events from each link
    events = []
    vtimezones = []

    for link in ical_links:
        try:
            response = requests.get(link)
            cal = icalendar.Calendar.from_ical(response.text)
        except:
            applog.error("Could not parse calendar: " +  link)
            continue
        # start with recurring events
        events += recurring_ical_events.of(cal, components=["VEVENT"]).between(start_of_period, end_of_period)
        vtimezones += [c for c in cal.subcomponents if c.name == 'VTIMEZONE']
        for component in cal.walk():
            if component.name == "VEVENT" and not 'RRULE' in component and not icaltools.is_fullday_event(component):
                component = icaltools.make_event_timezone_aware(component, "UTC")
                start = component.get('dtstart').dt
                end = component.get('dtend').dt
                if start_of_period <= end <= end_of_period or start_of_period <= start <= end_of_period or (start < start_of_period and end > end_of_period):
                    events.append(component)

    # retrieve conan events
    conan_events = icaltools.filter_by_summary_keyword(events, "Conan")
    # ignore recurring full day events
    events = icaltools.exclude_fullday_events(events)
    # include events for sleep time
    events += generate_sleep_events(start_of_period, end_of_period)
    events = icaltools.localize_aware_events(events)
    export_calendar("invert-conan-calendar.ics", generate_new_icalendar("Invertierte Freizeit", vtimezones, events))
    # generate events inbetween the free times
    events = invert_events(events, start_of_period, end_of_period)
    # ignore all free time events with a mininmal duration
    events = icaltools.filter_by_duration(events,timedelta(minutes=150))
    # add conan events to the free time events
    events += conan_events

    return generate_new_icalendar('Detektiv Conan Freizeit', vtimezones, events)

def generate_new_icalendar(name, vtimezones, events):
    new_calendar = icalendar.Calendar()
    new_calendar.add('prodid', '-//My calendar//mxm.dk//')
    new_calendar.add('version', '2.0')
    new_calendar.add('X-WR-CALNAME', name)
    new_calendar.add('X-COLOR', '#FFC0CB')

    for vtimezone in vtimezones:
        new_calendar.add_component(vtimezone)

    # add filtered events to the new calendar
    for event in events:
        new_calendar.add_component(event)

    #icaltools.publish_events(events, "filtered_events.ics")
    applog.info("Calendar " + name + " generated!")
    return new_calendar

def parse_file(filepath):
    links = []
    with open(filepath, 'r') as f:
        for line in f:
            if not line.startswith("#"):
                match = re.search(r'(https?|webcal):\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&\/\/=]*)', line)
                if match:
                    links.append(match.group())
    links = [link.replace("webcal", "https") if link.startswith("webcal") else link for link in links]
    return links

def write_calendar():
    calendar_links = parse_file("links.txt")
    with open("conan-calendar.ics", 'wb') as f:
        f.write(generate_free_time_calendar(calendar_links).to_ical())

def export_calendar(filename, icalendar):
    with open(filename, 'wb') as f:
        f.write(icalendar.to_ical())