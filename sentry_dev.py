import paho.mqtt.client as mqtt
import base64
import json
import time
import io
import os
from PIL import Image
import picamera

from classifiers import *
from classifyable import *
from MotionDetector import MotionDetector

uid = os.getenv("USERID")
pwd = os.getenv("PASSWD")
ipaddress = os.getenv("MQTTIP", "192.168.1.219")
delta = float(os.getenv("DELTA", 60))
topic = os.getenv("TOPIC", "Surveillance/MainDoor")

flag_motion = False
flag_presence = False
flag_intrusion = flag_motion and flag_presence

'''
Ref: https://stackoverflow.com/questions/42838221/python-paho-mqtt-loops-persistan-connection-to-broker#42931904

    while True:
        client = mqtt.Client()
        client.loop_start()
        client.message_callback_add('$SYS/broker/load/messages/received/1min', messages_received)
        client.on_connect = on_connect
        client.connect("test.mosquitto.org", 1883, 60)
        sleep(3)
        client.disconnect()
        client.loop_stop()
        sleep(10)

See also: http://www.steves-internet-guide.com/mqtt-clean-sessions-example

CODE FOR PUB-SUB IS IN FOREVER-WHILE LOOP AS SUGGESTED IN STACKOVERFLOW POST.
'''

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

def ship_payload(client, b64, sender, subject, flag_motion, flag_presence):
    payload = json.dumps({"From": sender, 
                    "Subject": subject, 
                    "Message": b64.decode('ascii'),
                    "Motion": flag_motion,
                    "Presence": flag_presence
                    })
    client.publish(topic=topic, payload=payload, qos=0, retain=True)
    return payload

'''
Specify the callbacks. Use with loop(timeout) method of MQTT client object. 
Ref: http://www.steves-internet-guide.com/mqtt-python-callbacks/
'''
def on_connect(client, userdata, flags, rc):
    print("Connected with result code {}!".format(rc))

def on_disconnect(client, userdata, rc):
    print("Disconnected!")

def on_subscribe(client, userdata, mid, granted_qos):
    print("Subscribed!")

def on_unsubscribe(client, userdata, mid):
    pass

def on_publish(client, userdata, mid):
    print("Published payload with id {}!".format(mid))

def on_message(client, userdata, message):
    #print("Received message\n{}\non topic {}.".format(str(message.payload.decode('utf-8')), message.topic))
    print("Received message on topic {}.".format(message.topic))

def on_log(client, userdata, level, buf):
    pass

tic = time.time()

while(True):
    print("Setting up connection to broker at {}".format(ipaddress))
    client = mqtt.Client(client_id="Sentry")
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.on_publish = on_publish 
    client.on_subscribe = on_subscribe
    client.username_pw_set(uid, pwd)
    client.connect(ipaddress)
 
    print("Subscribing to topic {} ..".format(topic))
    client.subscribe(topic) 

    f, s = make2takes()
    b64 = s.tobase64enc()

    # Sense motion
    print("Sensing motion ..")
    Sur = MotionDetector(f, s, showme=False)
    base, compare, diff, level, clean, mask, res = Sur.sense()
    flag_motion = True if sum(res.values()) > 4500 else False

    # Sense presence
    print("Sensing presence ..")
    labs2 = './Assets/labelmap.txt'
    mod2  = './Assets/detect.tflite'
    cnet = Coco(labs2, mod2, s)
    original, drawn, ret = cnet.classify_snap(threshold=0.5)
    flag_presence = True if dict(ret).get("person") else False

    # Set alert
    toc = time.time()
    if flag_presence or flag_motion:
        buffered_bytes = BytesIO() # For base64 encoding
        drawn.resize((transport_resolution)).save(buffered_bytes, 'jpeg')
        b64 = base64.b64encode(buffered_bytes.getvalue())
        payload = ship_payload(client, b64, "RPi3", "Vantage", flag_motion, flag_presence)
    elif (toc-tic) > delta:
        tic = toc
        payload = ship_payload(client, b64, "RPi3", "Vantage", flag_motion, flag_presence)
    else:
        None
    
    client.loop(3) # All callbacks executed in blocking mode
    client.disconnect()

