import icalendar
import datetime
import requests
from icalendar import vRecur
from datetime import timedelta, datetime
import dateutil.rrule as rrule
import pytz
from pytz import timezone as pytz_timezone
from icalendar import Timezone as ical_Timezone
import uuid
from icalendar import Event, vDatetime, TimezoneStandard, TimezoneDaylight


def add_property(event, property, value):
    event[property] = value;
    return event

def prepend_description(event, text):
    if 'DESCRIPTION' in event:
        event['DESCRIPTION'] = text + " \n\n " + event["DESCRIPTION"]
    else:
        event['DESCRIPTION'] = text
    return event

def prepend_category(event, text):
    if 'CATEGORIES' in event:
        event['CATEGORIES'] = text + "," + event["CATEGORIES"]
    else:
        event['CATEGORIES'] = text
    return event

def exclude_fullday_events(events):
    filtered_events = []
    for event in events:
        if not is_fullday_event(event):
            filtered_events.append(event)
    return filtered_events

def is_fullday_event(event):
    return isinstance(event, Event) and not event.get('dtstart').params.get('VALUE') != 'DATE'

def filter_by_duration(events, duration):
    """
    This function takes a list of events and a duration and returns a filtered list where every event has a duration
    more or equal to the provided duration.

    :param events: A list of icalendar.Event objects
    :param duration: A timedelta object representing the minimum duration of the events
    :return: A list of icalendar.Event objects with a duration more or equal to the provided duration
    """
    filtered_events = list(filter(lambda event: (event['DTEND'].dt - event['DTSTART'].dt) >= duration, events))
    return filtered_events

def filter_by_summary_keyword(events, keyword):
    """
    This function takes a list of events and a keyword and returns a filtered list where every event has the keyword
    in it's event summary. The filter is not case-sensetive.

    :param events: A list of icalendar.Event objects
    :param keyword: A strinf object representing a keyword
    :return: A list of icalendar.Event objects with the keyword in it's summary
    """
    filtered_events = list(filter(lambda event: (keyword.lower() in event['SUMMARY'].lower()) if 'SUMMARY' in event else False, events))
    return filtered_events

def create_ical_events_from_timespans(free_times, summary):
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
        ical_event = new_event()
        # Set the summary of the event
        ical_event.add('summary', summary)
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

def new_event():
    event = Event()
    # Get the current date and time in UTC
    now = datetime.utcnow()

    # Add the DTSTAMP property to the event
    event.add('dtstamp', now)
    #generate a unique identifier
    uid = str(uuid.uuid4())

    # Add the UID property to the event
    event.add('uid', uid)
    return event

def publish_events(events, filepath):
    print("Published events as file")

    # create a new calendar
    new_calendar = icalendar.Calendar()
    new_calendar.add('prodid', '-//My calendar//mxm.dk//')
    new_calendar.add('version', '2.0')

    # add filtered events to the new calendar
    for event in events:
        new_calendar.add_component(event)

    # write the calendar to a file
    with open(filepath, 'wb') as f:
        f.write(new_calendar.to_ical())

    # make the file accessible via a link, for example using a web server like Apache or Nginx
    # and give the link to the user


"""

Timezones

"""
def localize_aware_events(events, timezone="Europe/Berlin"):
    tz = pytz.timezone(timezone)
    new_events = []
    for event in events:
         # Localize the DTSTART and DTEND properties
        dtstart = event['DTSTART'].dt.astimezone(tz)
        dtend = event['DTEND'].dt.astimezone(tz)

        # Remove the existing DTSTART and DTEND properties
        event.pop('DTSTART')
        event.pop('DTEND')

        # Add the localized DTSTART and DTEND properties
        event.add('DTSTART', dtstart)
        event.add('DTEND', dtend)

        event.pop('TZID', None)
        event.add('TZID', tz.zone)

        new_events.append(event)

    return new_events

def add_timezones(events, calendar):
    """
    This function goes through a list of events and adds all the unique timezones to a calendar.
    :param events: list of events
    :param calendar: icalendar Calendar object
    :return: None
    """
    timezones = set()
    # iterate through events and collect unique timezones
    for event in events:
        dtstart = event.get('dtstart').dt
        timezones.add(dtstart.tzinfo.zone)
    print(timezones)   

def make_event_timezone_aware(event, timezone="Europe/Berlin"):
    """
    This function takes a recurring event with timezone naive datetime encoded in DTSTART and DTEND properties
    and a timezone (in the form of a string) and returns a recurring event with timezone aware datetime encoded
    in DTSTART, DTEND and RRULE properties.

    :param event: An icalendar.Event object
    :param timezone: A string representing the timezone (e.g. "Europe/Berlin")
    :return: The icalendar.Event object with timezone aware datetime in DTSTART, DTEND and RRULE properties
    """
    # test if event is timezone naive
    if not is_fullday_event(event) and not event['DTSTART'].dt.tzinfo:

        # Get the timezone object
        tz = pytz.timezone(timezone)

        # Localize the DTSTART and DTEND properties
        dtstart = tz.localize(event['DTSTART'].dt)
        dtend = tz.localize(event['DTEND'].dt)

        # Remove the existing DTSTART and DTEND properties
        event.pop('DTSTART')
        event.pop('DTEND')

        # Add the localized DTSTART and DTEND properties
        event.add('DTSTART', dtstart)
        event.add('DTEND', dtend)

        # Check if the event has a RRULE property
        if 'RRULE' in event:
            # Get the original RRULE property
            rrule = event['RRULE']
            # Remove the existing RRULE property
            event.pop('RRULE')
            # Localize the UNTIL property of the RRULE if it exists
            if 'UNTIL' in rrule:
                until = tz.localize(rrule['UNTIL'][0].dt)
                rrule.pop('UNTIL')
                rrule.add('UNTIL', until)
            # Add the localized RRULE property
            event.add('RRULE', rrule)
        
    return event


def set_event_times(event, start_time, end_time):
    """
    This function takes an ical event, start time and end time, where the times are timezone-aware datetime objects.
    The function sets the start and end time of the event with respect to their timezone and returns the event.
    
    :param event: An instance of the icalendar.Event class.
    :param start_time: A timezone-aware datetime object representing the start time of the event.
    :param end_time: A timezone-aware datetime object representing the end time of the event.
    :return: The input event with the start and end times updated
    """
    event.pop('DTSTART', None)
    event.pop('DTEND', None)
    event.add('DTSTART', start_time)
    event.add('DTEND', end_time)
    if False:#start_time.tzinfo:
        event.pop('TZID', None)
        event.add('TZID', start_time.tzinfo.zone)
    return event


def create_vtimezone_component(timezone_identifier):
    # get the pytz object
    tz = pytz_timezone(timezone_identifier)

    # Define the timezone
    vtimezone = ical_Timezone()

    # Get the start and end times for standard time
    datetime.datetime.now()
    standard_start_time, standard_end_time = tz._utc_transition_times[0]
    vtimezone.add('TZID', standard_start_time.tzinfo())

    # Define the standard time
    standard = TimezoneStandard()
    standard.add('DTSTART', standard_start_time)
    standard.add('TZOFFSETFROM', tz.utcoffset(standard_start_time))
    standard.add('TZOFFSETTO', tz.utcoffset(standard_end_time))
    standard.add('TZNAME', standard_start_time.tzname())
    vtimezone.add_component(standard)

    if len(tz._utc_transition_times) > 1:
        # Get the start and end times for daylight saving time
    
        daylight_start_time, daylight_end_time = tz._utc_transition_times[1]

        # Define the daylight saving time
        daylight = TimezoneDaylight()
        standard.add('DTSTART', daylight_start_time)
        standard.add('TZOFFSETFROM', tz.utcoffset(daylight_start_time))
        standard.add('TZOFFSETTO', tz.utcoffset(daylight_end_time))
        daylight.add('TZNAME', daylight_start_time.tzname())
        vtimezone.add_component(daylight)

    return vtimezone



"""

Recurring Events Management

"""

def create_events_from_recurring_event(recurring_event, start, end):
    if not is_fullday_event(recurring_event):
        rrule_str = recurring_event.get('RRULE').to_ical().decode("utf-8").strip()
        dtstart = recurring_event.get('dtstart').dt
        rrule_obj = rrule.rrulestr(rrule_str, dtstart=dtstart)
        occurrences = list(rrule_obj.between(start, end, inc=True))
        if occurrences:
            occurrences = create_non_recurring_events(recurring_event, occurrences)
        return occurrences
    return []

def create_non_recurring_events(recurring_event, occurrences, timezone='UTC'):
    # Create an empty list to store the new non-recurring events
    non_recurring_events = []
    tz = pytz.timezone(timezone)
    # Iterate over occurrences
    for start in occurrences:
        # Create a new event by copying the recurring event
        non_recurring_event = recurring_event.copy()
        # calculate the duration of the event
        recurring_event_dt_start = recurring_event.get('dtstart').dt
        recurring_event_dt_end = recurring_event.get('dtend').dt
        duration = (recurring_event_dt_end - recurring_event_dt_start)
        # update the start and end time of the new event 
        non_recurring_event = set_event_times(non_recurring_event, start, start + duration)
        # Remove the recurrence rule
        non_recurring_event["RRULE"] = ""
        # Append the new event to the list of non-recurring events
        non_recurring_events.append(non_recurring_event)
    # Return the list of non-recurring events
    return non_recurring_events

# unite events_a and events_b so that multiple events with the same start time, end time and summary are not duplicated
def unite_events(events_a, events_b):
    events_a = sorted(events_a, key=lambda x: (x['DTSTART'].dt))
    events_b = sorted(events_b, key=lambda x: (x['DTSTART'].dt))
    for event in events_b:
        is_duplicate = False
        for event_a in events_a:
            if event_a['DTSTART'].dt == event['DTSTART'].dt and event_a['DTEND'].dt == event['DTEND'].dt and event_a['SUMMARY'] == event['SUMMARY']:
                is_duplicate = True
                break
        if not is_duplicate:
            events_a.append(event)
    return events_a
        