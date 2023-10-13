from flask import Flask, Response, render_template, jsonify
from flask_basicauth import BasicAuth
from icalendar import Calendar, Event

import schedule
import time
import subprocess

import json

def read_json(path):
    with open(path) as f:
        return json.load(f)

app = Flask(__name__)

secrets = read_json("secrets/secrets.json")
settings = read_json("application.json")
program_status = "not running"

autostart = settings['autostart']

app.config['BASIC_AUTH_USERNAME'] = secrets['username']
app.config['BASIC_AUTH_PASSWORD'] = secrets['password']

basic_auth = BasicAuth(app)

'''
-----------------------------------------------------

Section for App-specific functions

-----------------------------------------------------
'''

@app.route('/calendar/view/<calendar>')
def return_calendar_view(calendar):
    return render_template('calendar.html',  calendar_url="/calendar/subscribe/" + calendar)

@app.route('/calendar/subscribe/<calendar>')
def return_calendar_subscription(calendar):
    with open('app/' + calendar + '.ics', 'r') as f:
        ics_file = f.read()
    return Response(ics_file, mimetype='text/calendar')


@app.route('/conan-calendar.ics')
def conan_calendar_ics():
    with open('app/conan-calendar.ics', 'r') as f:
        ics_file = f.read()
    return Response(ics_file, mimetype='text/calendar')

import caldove
@app.route('/calendar/api/caldove')
def caldove_route():
    return caldove.generate_site()

@app.route('/conan-calendar')
def conan_calendar():
    return render_template('calendar.html',  calendar_url="conan-calendar.ics")


@app.route('/invert-conan-calendar.ics')
def invert_conan_calendar_ics():
    with open('app/invert-conan-calendar.ics', 'r') as f:
        ics_file = f.read()
    return Response(ics_file, mimetype='text/calendar')


@app.route('/invert-conan-calendar')
def invert_conan_calendar():
    return render_template('calendar.html',  calendar_url="invert-conan-calendar.ics")


'''
-----------------------------------------------------

Section for template functions

-----------------------------------------------------
'''

@app.route('/')
def index():
    return render_template('index.html', **read_json("application.json"))


@app.route('/secret')
@basic_auth.required
def secret_page():
    return "You have access to the secret page!"


@app.route('/status')
def status():
    global program_status
    return jsonify(status=program_status)


@app.route('/logs')
@basic_auth.required
def logs():
    log_messages = []
    with open('app/log/application.log', 'r') as logfile:
        for line in logfile:
            try:
                time, application, log_type, message = line.strip().split(' ', 3)
                log_messages.append({'time': time, 'application': application, 'type': log_type, 'message': message})
            except Exception as e:
                print("Parse Error for log event:" + line)
    log_messages = log_messages[::-1]  # Reverse the order of the messages to display the latest message first
    return render_template('logs.html', log_messages=log_messages)


@app.route('/activate', methods=['POST'])
def activate():
    global program_status
    if program_status == "success":
        return jsonify(status='already running')
    program_running = True
    if start():
        program_status = "success"
    else:
        program_status = "failed"
    return jsonify(status=program_status)


def start():
    global program_status
    time.sleep(5)

    # code for app-specific function goes here
    subprocess.Popen(["python", "app/main.py"]) 
    print("Calendar initialized")
    program_status = "success"

    return True


if __name__ == '__main__':
    print(settings["autostart"])
    app.run()

if settings["autostart"]:
    start()