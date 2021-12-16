import paho.mqtt.client as mqtt
import base64
import json
import time
import io
from PIL import Image
import picamera

from classifiers import *
from classifyable import *
from MotionDetector import MotionDetector

flag_motion = False
flag_presence = False
flag_intrusion = flag_motion and flag_presence

base_text = "Basement Vantage Point"
addendum_motion = "SENSED MOTION"
addendum_presence = "SENSED PRESENCE"
addendum_intrusion = "ALERT!!! POSSIBLE INTRUSION!!!"

client = mqtt.Client("Sentry")
transport_resolution = (224, 224) # Ship images of this size

'''
Take two snaps in rapid succession for motion detection.
'''
def make2takes():
    '''
    Takes two snaps with the pi camera and returns classifyable objects
    for use with classifiers.py and MotionDetector.py only.
    '''
    first = Classifyable()
    second = Classifyable()
    
    first.set_snap()
    second.set_snap()
    
    return first, second

def ship_payload(client, sender, subject, b64):
    payload = json.dumps({"From": sender, 
                    "Subject": subject, 
                    "Message": b64.decode('ascii')})
    client.publish("Surveillance/MainDoor", payload)
    return payload
'''
Specify the callbacks. Use with loop_start() and loop_stop() 
methods of MQTT client object. 
Ref: http://www.steves-internet-guide.com/mqtt-python-callbacks/
'''
def on_connect(client, userdata, flags, rc):
    print("Connected with result code {}.".format(rc))

def on_disconnect(client, userdata, rc):
    print("Establishing connection .. ")
    client.connect("192.168.1.254")

def on_subscribe(client, userdata, mid, granted_qos):
    print("Subscribed.")

def on_unsubscribe(client, userdata, mid):
    pass

def on_publish(client, userdata, mid):
    print("Sent message with id {}.".format(mid))

def on_message(client, userdata, message):
    #print("Received message\n{}\non topic {}.".format(str(message.payload.decode('utf-8')), message.topic))
    print("Received message on topic {}.".format(message.topic))
def on_log(client, userdata, level, buf):
    pass

client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_subscribe = on_subscribe
client.on_publish = on_publish
client.on_message = on_message

print("Establishing connection .. ")
client.connect("192.168.1.254")

client.loop_start()  # Start the thread to listen for events and trigger callbacks

print("Subscribing to topic {} ..".format("Surveillance/MainDoor"))
client.subscribe("Surveillance/MainDoor")

tic = time.time()
delta = 30  # Pause for this duration (in seconds) between update

while(True):
    f, s = make2takes()

    # Sense motion
    Sur = MotionDetector(f, s, showme=False)
    base, compare, diff, level, clean, mask, res = Sur.sense()
    flag_motion = True if sum(res.values()) > 4500 else False

    # Sense presence
    labs2 = './Assets/labelmap.txt'
    mod2  = './Assets/detect.tflite'
    cnet = Coco(labs2, mod2, s)
    original, drawn, ret = cnet.classify_snap(threshold=0.4)
    flag_presence = True if dict(ret).get("person") else False

    # Set alert
    subject_line = base_text
    subject_line += " "
    toc = time.time()
    if flag_presence:
        buffered_bytes = BytesIO() # For base64 encoding
        drawn.resize((transport_resolution)).save(buffered_bytes, 'jpeg')
        b64 = base64.b64encode(buffered_bytes.getvalue())
        if flag_motion:
            subject_line += addendum_intrusion
        else:
            subject_line += addendum_presence
        payload = ship_payload(client, "RPi3", subject_line, b64)     
    elif flag_motion:
        subject_line += addendum_motion
        payload = ship_payload(client, "RPi3", subject_line, s.tobase64enc())
    elif (toc-tic) > delta:
        tic = toc
        payload = ship_payload(client, "RPi3", subject_line, s.tobase64enc())
    else:
        None

time.sleep(6)
client.loop_stop()
