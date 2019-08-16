import cv2
import time
#from espeak import espeak
from subprocess import call
import random
import numpy as np
import threading
import requests

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

roi = (275, 309, 39 + 275, 53 + 309)

# hsv values
green_thresh_low = (40, 50, 0)
green_thresh_high = (65, 255, 255)

blue_thresh_low = (80, 50, 0)
blue_thresh_high = (135, 255, 255)

thresh_percent = 0.3

has_green_cup = False
has_blue_cup = False
last_cup_time = time.time()
last_cup_off_time = last_cup_time
did_say_thanks = True

cup_timeout = 10
spasibo_timeout = 2
alert = threading.Event()
shutdown = threading.Event()
led_address = "http://192.168.0.95/"
delay = 0.5

def speak(text):
    cmd1 = "espeak"
    cmd2 = " -vru+f4"#+str(random.randint(1,5))
    cmd3 = " -p60"#+str(random.randint(30,90))
    cmd4 = " -s"+str(random.randint(40,160))
    cmd5 = " -g"+str(random.randint(0,30))
    cmd6 = " -x -a150 \""
    cmd7 = "\" 2>/dev/null"
    cmd = cmd1 + cmd2 + cmd3 + cmd4 + cmd5 + cmd6 + text + cmd7
    call([cmd], shell=True)

def update_state(green_cup, blue_cup):
    global has_green_cup
    global has_blue_cup
    did_update_state = False
    if green_cup != has_green_cup:
        has_green_cup = green_cup
        did_update_state = True
    if blue_cup != has_blue_cup:
        has_blue_cup = blue_cup
        did_update_state = True
    if did_update_state:
        if has_green_cup:
            print "Green cup detected"
        elif has_blue_cup:
            print "Blue cup detected"
        else:
            print "No cup detected"

def turn_led_red():
    return requests.post(led_address+"red")

def turn_led_off():
    return requests.post(led_address+"off")

def led_blink():
    while not shutdown.is_set():
        if alert.is_set():
            turn_led_red()
            time.sleep(delay)
            turn_led_off()
            time.sleep(delay)

led_thread = threading.Thread(target=led_blink, name="Led blink thread")
led_thread.start()

try:
    while True:
        _, image_frame = cap.read()

        rect_img = image_frame[roi[1]:roi[3], roi[0]: roi[2]]
        rect_img = cv2.cvtColor(rect_img, cv2.COLOR_BGR2HSV)

        green_cup = cv2.inRange(rect_img, green_thresh_low, green_thresh_high)
        blue_cup = cv2.inRange(rect_img, blue_thresh_low, blue_thresh_high)

        #green_cnt = 0
        #for line in green_cup:
        #    for pixel in line:
        #        if pixel > 0:
        #            green_cnt += 1

        #blue_cnt = 0
        #for line in blue_cup:
        #    for pixel in line:
        #        if pixel > 0:
        #            blue_cnt += 1
        green_cnt = np.count_nonzero(green_cup)
        blue_cnt = np.count_nonzero(blue_cup)

        pixels_total = len(green_cup) * len(green_cup[0])
        green_pixels = float(green_cnt) / pixels_total
        blue_pixels = float(blue_cnt) / pixels_total

        if green_pixels > thresh_percent:
            update_state(True, False)
    #        has_green_cup = True
    #        has_blue_cup = False
        elif blue_pixels > thresh_percent:
            update_state(False, True)
    #        has_green_cup = False
    #        has_blue_cup = True
        else:
            update_state(False, False)
    #        has_green_cup = False
    #        has_blue_cup = False

        if has_blue_cup or has_green_cup:
            last_cup_time = time.time()
            if (last_cup_time - last_cup_off_time > spasibo_timeout) and not did_say_thanks:
                #espeak.synth('Spasibo')
                speak("[[spas;'ibV_]]")
                did_say_thanks = True
                alert.clear()
        else:
            current_time = time.time()
            if current_time - last_cup_time > cup_timeout:
                #espeak.set_parameter(espeak.Parameter.Rate, 150)
                #espeak.set_parameter(espeak.Parameter.Pitch, 50)
                #espeak.set_parameter(espeak.Parameter.Volume, 1000)
                #espeak.set_voice('ru')
                #espeak.synth("[[v;ern'I_ stAk'Vn__]]")
                speak("[[v;ern'I stAk'Vn_]]")
                last_cup_time = current_time
                last_cup_off_time = current_time
                did_say_thanks = False
                alert.set()

    #    if has_green_cup:
    #        print "Green cup detected"
    #    elif has_blue_cup:
    #        print "Blue cup detected"
    #    else:
    #        print "No cup detected"
finally:
    shutdown.set()
    cap.release()

