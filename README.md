# Raspberry Pi temperature alert
Monitor the CPU temperature of a Raspberry Pi, send warn emails and shut down the system if it gets too hot.

The original code comes from [here](https://gist.github.com/LeonardoGentile/7a5330e6bc55860feee5d0dd79e7965d). I modified it to send more detailed warning messages and added a nice CPU temperature graph over the past 60 days to the emails. Below
is an example email.

![Email Screenshot](https://raw.githubusercontent.com/mityax/rpi-temperature-alert/master/email-screenshot.png)

## Setup
```pip install python-simplemail```

To run this script periodically (as it is intended) type
```sudo crontab -e```
and add this line:

```*/15 * * * * python /home/pi/temperature-alert.py```

Then adjust the email credentials at the beggining of the script.

That's it. Your Pi is now save.


__Setup on systems without pip (e.g. LibreElec and OpenElec)__

To use this script on systems without pip just download [this python script](https://github.com/gerold-penz/python-simplemail/blob/master/simplemail/__init__.py), rename it to ```simplemail.py``` and place it next to ```temperature-alert.py```

## Testing the Setup
To test your setup, just type

```python temperature-alert.py 70```

This will emulate a CPU temperature of 70°C and thus send you a warn e-mail. Use 81°C to test the shutdown function.
