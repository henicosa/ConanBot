from flask import Flask, Response, render_template, jsonify, request, abort
from flask_basicauth import BasicAuth

import schedule
import time
import subprocess

import json
import logging

def read_json(path):
    with open(path) as f:
        return json.load(f)

app = Flask(__name__)

# Configure the Flask app logger
file_handler = logging.FileHandler('app/log/server.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s', "%Y-%m-%d_%H:%M:%S"))
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)



secrets = read_json("secrets/secrets.json")
settings = read_json("application.json")

app.config['BASIC_AUTH_USERNAME'] = secrets['username']
app.config['BASIC_AUTH_PASSWORD'] = secrets['password']

basic_auth = BasicAuth(app)

program_status = "not running"

'''
-----------------------------------------------------

Section for App-specific functions

-----------------------------------------------------
'''

from icalendar import Calendar, Event

def start():
    global program_status
    time.sleep(5)

    # code for app-specific function goes here
    subprocess.Popen(["python", "app/main.py"]) 
    print("Calendar initialized")
    program_status = "success"

    return True


@app.route('/calendar/view/<calendar>')
def return_calendar_view(calendar):
    return render_template('calendar JSON.html',  calendar_url="/calendar/json/" + calendar)

@app.route('/calendar/subscribe/<calendar>')
def return_calendar_subscription(calendar):
    with open('app/' + calendar + '.ics', 'r') as f:
        ics_file = f.read()
    return Response(ics_file, mimetype='text/calendar')

@app.route('/calendar/json/<calendar>')
def return_calendar_json(calendar):
    with open('app/' + calendar + '.json', 'r') as f:
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


@app.route('/about')
def about():
    return render_template('appinfo.html', appinfo=settings)

@app.route('/secret')
@basic_auth.required
def secret_page():
    return "You have access to the secret page!"

@app.route('/status')
def status():
    global program_status
    return jsonify(status=program_status)

'''
-----------------------------------------------------
Logs
'''

@app.route('/logs/application')
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

@app.route('/logs/server')
@basic_auth.required
def server_logs():
    log_messages = []
    with open('app/log/server.log', 'r') as logfile:
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

'''
-----------------------------------------------------

Define error handlers

-----------------------------------------------------
'''

@app.errorhandler(451)
def page_unavailable_for_legal_reasons(error):
    errorinfo = {"code": 451,
                "explanation_de": "Sorry. Diese Seite ist aus rechtlichen Gründen nicht verfügbar.",
                "explanation_en": "Sorry. This site is not accessible for legal reasons."}
    return render_template('error.html', appinfo=settings, error=errorinfo), 451


@app.errorhandler(404)
def page_not_found_error(error):
    errorinfo = {"code": 404,
                 "explanation_de": "Sorry. Diese Seite gibt es nicht. Oder sie gab es mal und jetzt fehlt sie.",
                 "explanation_en": "Sorry. This site does not exist. Or it existet and is gone now."}
    return render_template('error.html', appinfo=settings, error=errorinfo), 404


'''
-----------------------------------------------------

Application start up

-----------------------------------------------------
'''

with app.app_context():
    if settings["autostart_enabled"]:
        print("Autostarting application...")
        app.logger.info("Autostarting application...")
        app_running = start()
        if app_running:
            program_status = "success"
        else:
            program_status = "failed"

if __name__ == '__main__':
    app.run()