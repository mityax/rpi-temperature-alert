#!/usr/bin/env python
# coding: utf-8

import os
import sys
from simplemail import Email
import json
import time
import tempfile


# Script settings:
high = 60  # If the Pi reaches this temperature, it first sends a warning email
too_high = 80  # If it reaches this temperature, it sends an email and shuts down
history_file = os.path.expanduser("~/.temperature-history.json")  # Where to save the temperature history of the last 60 days
device_name = os.uname()[1]  # This is the device's hostname. To change it, remove the '#' from the line below and insert your device name.
#device_name = "My super duper Pi"

# Sender email account:
email_smtp_server = "mail.gmx.net:587"  # Your email server
email_smtp_user = "johndoe@gmx.net"  # Your email account
email_smtp_password = "123"  # Your email password
email_use_tls = True  # Wether to use TLS encryption or not

# Recipient email adress:
email_recipient = ("jeff@gmail.com", "Jeff Doe")  # The account to send the email to


# Script
def get_cpu_temp():
    res = os.popen('vcgencmd measure_temp').readline()
    return float(res.replace("temp=","").replace("'C\n",""))


def get_system_up_time():
    res = os.popen("</proc/uptime awk '{print $1}'").readline()
    return float(res.strip())


def load_history():
    if not os.path.isfile(history_file):
        with open(history_file, "w+") as f:
            f.write("{}")
        return {}
    with open(history_file, "r") as f:
        return json.load(f)


def save_history(history):
    # remove old history; only keep 60 days of history
    for date, temp in history.items():
        if time.time() - float(date) > 60 * 24 * 60 * 60:  # discard anything older than 60 days
            del history[date]
    with open(history_file, "w+") as f:
        json.dump(history, f)


def send_mail(subject, title, message, history=None):
    email = Email()
    email.from_address = email_smtp_user
    email.from_caption = device_name
    email.recipients.add(*email_recipient)
    email.smtp_server = email_smtp_server
    email.smtp_user = email_smtp_user
    email.smtp_password = email_smtp_password
    email.use_tls = email_use_tls

    email.subject = "WARNING: %s" % subject
    additional_info = [
        ("High limit", high),
        ("Critical limit", too_high),
        ("Up time", "%.02f hours" % (get_system_up_time() / 60 / 60))
    ]
    email.message = "************** %s alert **************\n\n%s\n\n\n%s\n\n-----------------------------------\n%s" % (device_name, title.upper(), message, "\n".join("%s: %s" % i for i in additional_info))

    if history and len(history.keys()) > 1:
        path = os.path.join(tempfile.gettempdir(), time.strftime("Temperature Graph - %d.%m.%Y %H:%M.svg"))
        with open(path, "w+") as f:
            f.write(generate_history_graph(history))
        email.attachments.add_filename(path)

    return email.send()
    

def generate_history_graph(history):
    width = 1000
    height = 250
    bottom_margin = height * 0.1
    svg = ("<svg viewBox=\"0 0 {width} {height}\" xmlns=\"http://www.w3.org/2000/svg\" " +
           "xmlns:xlink=\"http://www.w3.org/1999/xlink\" " +
           "preserveAspectRatio=\"none\" width=\"{width}\" height=\"{height}\"><path fill=\"#FFD95C\" stroke=\"#E1B62F\"  d=\"").format(width=width, height=height)
    svg += "M 0 %s" % (height - bottom_margin)
    data = sorted(history.items(), key=lambda x: x[0])
    xmax = max(float(x) for x in history.keys())
    xmin = min(float(x) for x in history.keys())
    ymax = max(too_high + 0.3, max(float(y) for y in history.values()) + 0.3)
    ymin = min(float(y) for y in history.values())
    xvalues = [(float(x) - xmin) / (xmax - xmin) for x, _ in data]
    yvalues = [y / ymax for _, y in data]
    for date, temp in zip(xvalues, yvalues):
        x = round(date * width, 3)
        y = round(height - (height * 0.9 - bottom_margin) * temp, 3)
        svg += "L%s %s" % (x, y)
    svg += "L%s %s" % (width, height - bottom_margin)

    svg += "Z\"></path>"
    
    yhigh = height - (height * 0.9 - bottom_margin) * (high / ymax)
    ycritical = height - (height * 0.9 - bottom_margin) * (too_high / ymax)
    svg += '<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke: {color}; stroke-width: 1.5; stroke-dasharray: 4" />'.format(color="darkorange", x1=0, x2=width, y1=yhigh, y2=yhigh)
    svg += '<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke: {color}; stroke-width: 1.5; stroke-dasharray: 4" />'.format(color="red", x1=0, x2=width, y1=ycritical, y2=ycritical)
    
    svg += '<text x="{x}" y="{y}" fill="black" font-size="11pt">{text}</text>'.format(x=0, y=height, text=time.strftime("%d.%m.%Y", time.localtime(xmin)))
    svg += '<text x="{x}" y="{y}" fill="black" font-size="11pt">{text}</text>'.format(x=width * 0.91, y=height, text=time.strftime("%d.%m.%Y", time.localtime(xmax)))
    
    return svg + "</svg>"


if __name__ == '__main__':
    # Now we convert our value into a float number
    temp = float(sys.argv[1] if len(sys.argv) > 1 else get_cpu_temp())
    
    history = load_history()
    history[str(time.time())] = temp
    save_history(history)

    # Check if the temperature is above 60°C (you can change this value, but it shouldn't be above 70)
    if (temp > high):
        critical = False
        if temp > too_high:
            critical = True
            subject = "{} temperature {}°C. Shutting down.".format(device_name, temp)
            title = "Critical Temperature Warning!"
            message = "The CPU temperature of the Raspberry Pi is above the limit: {}°C \n\nShutting down the pi!".format(temp)
        else:
            subject = "{} temperature: {}°C ".format(device_name, temp)
            title = "Temperature Warning!"
            message = "The Raspberry Pi ({}) temperature is: {}°C".format(device_name, temp)
        
        send_mail(subject, title, message, history=history)
        
        # Critical, shut down the pi
        if critical:
            os.popen('sudo shutdown now')

    # Don't print anything otherwise. 
    # Cron will send you an email for any command that returns "any" output (so you would get another  email)
    # else:
    #   print "Everything is working fine!"
