import paho.mqtt.client as mqtt
import base64
import json
import time
import io
from PIL import Image
import picamera

stream = io.BytesIO()
'''
with picamera.PiCamera() as camera:
    camera.rotation = 180
    camera.resolution = (300, 300)
    camera.start_preview()
    time.sleep(2)
    camera.capture(stream, format="jpeg")

stream.seek(0)
imnbytes = stream.getvalue()
im2ship = base64.b64encode(imnbytes)
snap = Image.open(stream)
snap.show()
'''

myCam = picamera.PiCamera()
myCam.rotation = 180
myCam.resolution = (300, 300)

client = mqtt.Client("Sentry")

'''
Specify the callbacks. Use with loop_start() and loop_stop() 
methods of MQTT client object. 
Ref: http://www.steves-internet-guide.com/mqtt-python-callbacks/
'''
def on_connect(client, userdata, flags, rc):
    print("Connected with result code {}.".format(rc))

def on_disconnect(client, userdata, rc):
    print("Establishing connection .. ")
    client.connect("192.168.1.216")

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
client.connect("192.168.1.216")

client.loop_start()  # Start the thread to listen for events and trigger callbacks

print("Subscribing to topic {} ..".format("Surveillance/MainDoor"))
client.subscribe("Surveillance/MainDoor")

tic = time.time()
delta = 30  # Pause for this duration (in seconds) between updates
while(True):
    toc = time.time()
    if ((toc - tic) > delta):
        '''
        Send an image every delta seconds.
        '''
        myCam.capture(stream, format="jpeg")
        stream.seek(0)
        imnbytes = stream.getvalue()
        im2ship = base64.b64encode(imnbytes)
        payload = json.dumps({"From": "RPi3", 
                        "Subject": "Basement Vantage Point", 
                        "Message": im2ship.decode('ascii')})  # im_encoded
        tic = toc
        client.publish("Surveillance/MainDoor", payload)

time.sleep(6)
client.loop_stop()
