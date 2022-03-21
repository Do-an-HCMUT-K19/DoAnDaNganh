import serial.tools.list_ports
import random
import time
import  sys
from  Adafruit_IO import  MQTTClient



# firebase setup

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore


AIO_FEED_IDS = ["BBC_TEMP", "BBC_HUMI"]
AIO_USERNAME = "chuong200115"
AIO_KEY = "aio_buCX18lizR5ZGtI9MgoZq6l0OzNr"

def  connected(client):
    print("Ket noi thanh cong...")
    for feed in AIO_FEED_IDS:
        client.subscribe(feed)

def  subscribe(client , userdata , mid , granted_qos):
    print("Subcribe thanh cong...")

def  disconnected(client):
    print("Ngat ket noi...")
    sys.exit (1)

def  message(client , feed_id , payload):
    print("Nhan du lieu: " + payload)
    if isMicrobitConnected:
        ser.write((str(payload) + "#").encode())

client = MQTTClient(AIO_USERNAME , AIO_KEY)
client.on_connect = connected
client.on_disconnect = disconnected
client.on_message = message
client.on_subscribe = subscribe
client.connect()
client.loop_background()

def getPort():
    ports = serial.tools.list_ports.comports()
    N = len(ports)
    commPort = "None"
    for i in range(0, N):
        port = ports[i]
        strPort = str(port)
        #if "USB Serial Device" in strPort:
        if "com0com - serial port emulator (COM4)" in strPort:
            splitPort = strPort.split(" ")
            commPort = (splitPort[0])
    return commPort

isMicrobitConnected = False
if getPort() != "None":
    ser = serial.Serial( port=getPort(), baudrate=115200)
    isMicrobitConnected = True


def processData(data):
    data = data.replace("!", "")
    data = data.replace("#", "")
    splitData = data.split(":")
    print(splitData)
    try:
        if splitData[1] == "TEMP":
            client.publish("bbc-temp", splitData[2])
        elif splitData[1] == "HUMI":
            client.publish("BBC_HUMI", splitData[2])
    except:
        pass

mess = ""
def readSerial():
    bytesToRead = ser.inWaiting()
    if (bytesToRead > 0):
        global mess
        mess = mess + ser.read(bytesToRead).decode("UTF-8")
        while ("#" in mess) and ("!" in mess):
            start = mess.find("!")
            end = mess.find("#")
            processData(mess[start:end + 1])
            if (end == len(mess)):
                mess = ""
            else:
                mess = mess[end+1:]

















# FIREBASE CONNECTION
# Use the application default credentials
cred = credentials.Certificate("./aceteam-18b6b-firebase-adminsdk-agvz2-9b3044cbe9.json")
firebase_admin.initialize_app(cred)
db = firestore.client()


db.collection('devices').add({'ID':'phuc'})




#Listening to database change
# Create an Event for notifying main thread.
callback_done = threading.Event()

# Create a callback on_snapshot function to capture changes
def on_snapshot(doc_snapshot, changes, read_time):
    for doc in doc_snapshot:
        print(f'Received document snapshot: {doc.id}')
    callback_done.set()

doc_ref = db.collection(u'devices').document(u'QfgPfit0CczPBxW8goul')

# Watch the document
doc_watch = doc_ref.on_snapshot(on_snapshot)




while True:
    if isMicrobitConnected:
        readSerial()

    time.sleep(1)



