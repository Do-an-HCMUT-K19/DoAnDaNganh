import serial.tools.list_ports
import time
import sys
from Adafruit_IO import MQTTClient
import threading
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore


# FIREBASE CONNECTION
# Use the application default credentials
cred = credentials.Certificate(
    "./aceteam-18b6b-firebase-adminsdk-agvz2-9b3044cbe9.json"
)
firebase_admin.initialize_app(cred)
db = firestore.client()


curr = {"account": "giacat", "temp": 30, "humid": 80, "soil": 70}
local_sensor_id = [1,10,18]
area = "garden"
bump = 19
START = 1
END = 2
OUT = 0

AIO_FEED_IDS = ["BBC_TEMP", "BBC_HUMI", "BBC_LED", "BBC_SOIL"]
AIO_USERNAME = "chuong200115"
AIO_KEY = "aio_OYZl49GLNzFC8D2amK2r3KZuksWo"


def connected(client):
    print("Ket noi thanh cong...")
    for feed in AIO_FEED_IDS:
        client.subscribe(feed)


def subscribe(client, userdata, mid, granted_qos):
    print("Subcribe thanh cong...")


def disconnected(client):
    print("Ngat ket noi...")
    sys.exit(1)


def message(client, feed_id, payload):
    # print("Nhan du lieu: " + payload)
    if isMicrobitConnected:
        ser.write((str(payload) + "#").encode())


client = MQTTClient(AIO_USERNAME, AIO_KEY)
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
        if "USB Serial Device" in strPort:
            # if "com0com - serial port emulator (COM4)" in strPort:
            splitPort = strPort.split(" ")
            commPort = (splitPort[0])
    return commPort


isMicrobitConnected = False
if getPort() != "None":
    ser = serial.Serial(port=getPort(), baudrate=115200)
    isMicrobitConnected = True


def processData(data):
    data = data.replace("!", "")
    data = data.replace("#", "")
    splitData = data.split(":")
    # print(splitData)
    try:
        if splitData[1] == "TEMP":
            client.publish("bbc-temp", splitData[2])
            curr['temp'] = int(splitData[2])
        elif splitData[1] == "SOIL":
            client.publish("SOIL", splitData[2])
            # print(splitData[2])
            # TODO name & publish
            curr['soil'] = int(splitData[2])
        elif splitData[1] == "HUMI":
            client.publish("BBC_HUMI", splitData[2])
            curr['humid'] = int(splitData[2])
            curr['ts'] = firestore.SERVER_TIMESTAMP,
            update_env(curr)
            # time.sleep(10)
        elif splitData[1] == "LED":
            state="on" if splitData[2] == "1" else "off"
            client.publish("BBC_LED", splitData[2])
            update_sensor_state({"id": 1, "state": state})
            print("*")
        elif splitData[1] == "BUMP":
            state="on" if splitData[2] == "1" else "off"
            update_sensor_state({"id": 19, "state": state})
            print("*")

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


def update_env(curr):
    meta_realtime_db = {
        "account_name": curr['account'],
        "air_humidity": curr['humid'],
        "env_temperature": curr['temp'],
        "land_humidity": curr['soil'],
        "timestamp": firestore.SERVER_TIMESTAMP,
        "area":area
    }
    db.collection("realtime_db").add(meta_realtime_db)


def update_sensor_state(sensor):
    log_ref = db.collection("log_sensor").where(
        "sensor_id", "==", sensor['id'])
    latest_ref = log_ref.order_by(
        "time_start", direction=firestore.Query.DESCENDING
    ).limit(1)
    for doc in latest_ref.stream():
        last = doc
    sensor_transaction(db.transaction(), db.collection(
        "log_sensor").document(last.id), last, sensor)


@firestore.transactional
def sensor_transaction(transaction, ref, last, sensor):

    snapshot = ref.get(transaction=transaction)
    meta_sensor_log = {
        "account_name": curr['account'],
        "sensor_id": sensor['id'],
        "time_start": firestore.SERVER_TIMESTAMP,
        "duration": 0,
    }
    # add duration for 0 duration record
    if sensor['state'] == "off":
        new_duration = int(time.time() - last.to_dict()
                           ["time_start"].timestamp())

        #  - meta_sensor_log["time_start"]
        transaction.update(ref, {"duration": new_duration})

    # check dupicate
    else:
        if last.to_dict()["duration"] != 0:
            db.collection("log_sensor").add(meta_sensor_log)


callback_done = threading.Event()


def log_on_snapshot(doc_snapshot, changes, read_time):
    for change in changes:
        if change.type.name == "ADDED":
            # print(f"New sensor turn on: {change.document.id}")
            if change.document._data['duration']==-1:
                turn_on(change.document._data['sensor_id'])

        elif change.type.name == "MODIFIED":
            # print(f"Turn off sensor: {change.document.id}")
            if change.document._data['duration'] != -1:
                turn_off(change.document._data['sensor_id'])

        elif change.type.name == "REMOVED":
            callback_done.set()
    callback_done.set()

#
# def log_on_snapshot(doc_snapshot, changes, read_time):
#     for change in changes:
#         if change.type.name == "ADDED":
#             # print(f"New sensor turn on: {change.document.id}")
#             turn_on(change.document._data['sensor_id'])
#
#         elif change.type.name == "MODIFIED":
#             # print(f"Turn off sensor: {change.document.id}")
#             turn_off(change.document._data['sensor_id'])
#
#         elif change.type.name == "REMOVED":
#             callback_done.set()
#     callback_done.set()


def timer_on_snapshot(doc_snapshot, changes, read_time):
    # for change in changes:
    #     print(f"New timer on: {change.document.id}")
    callback_done.set()


def env_on_snapshot(doc_snapshot, changes, read_time):
    for change in changes:
        if change.type.name == "ADDED":
            set_env(change.document._data['land_humidity'])
        elif change.type.name == "MODIFIED":
            set_env(change.document._data['land_humidity'])
        elif change.type.name == "REMOVED":
            bump_manual()
            callback_done.set()
    callback_done.set()


log_ref = db.collection("log_sensor").where(
    "sensor_id", u"in", local_sensor_id)
log_watch = log_ref.on_snapshot(log_on_snapshot)

timer_ref = db.collection("timer")    .where(
    "sensor_id", u"in", local_sensor_id)
timer_watch = timer_ref.on_snapshot(timer_on_snapshot)

env_ref = db.collection("target_env").where(
    "sensor_id", u"==", bump)
env_watch = env_ref.on_snapshot(env_on_snapshot)


def state(sche):
    # TODO just a fake function for fast testing
    cur = time.localtime()
    print(cur.tm_sec, sche["time_of_day"])
    if cur.tm_sec == int(sche["time_of_day"].split(':')[0]):
        return START
    elif cur.tm_sec == int(sche["time_of_day"].split(':')[0])+sche['duration']:
        return END
    return OUT
    # if cur.tm_wday == encode_timestamp(sche['timestamp'])-2:
    #     if cur.tm_hour==int(sche["time_of_day"].split(':')[0]):
    #         if cur.tm_min==int(sche["time_of_day"].split(':')[1][1:2]):
    #             # _schedule.update({"last_record": curr})
    #             return START
    #             turn_on(sensor)
    #     if cur.tm_hour==int(sche["time_of_day"].split(':')[0])+sche['duration']:
    #         if cur.tm_min==int(sche["time_of_day"].split(':')[1][1:2]):
    #             return END
    # return OUT


def check_timer():
    while True:
        for sensor in local_sensor_id:
            _schedule = timer_ref.where("sensor_id", "==", sensor).stream()
            for doc in _schedule:
                sche = doc.to_dict()
                cur = state(sche)
                if cur == START:
                    if sche['state'] == 'on':
                        update_sensor_state({"id": sensor, "state": "on"})
                        turn_on(sensor)
                    else:
                        update_sensor_state({"id": sensor, "state": "off"})
                        turn_off(sensor)
                elif cur == END:
                    if sche['state'] == 'on':
                        update_sensor_state({"id": sensor, "state": "off"})
                        turn_off(sensor)
                    else:
                        update_sensor_state({"id": sensor, "state": "on"})
                        turn_on(sensor)
        time.sleep(1)


def encode_timestamp(day):
    if day == "Mon":
        return 2
    elif day == "Tue":
        return 3
    elif day == "Wed":
        return 4
    elif day == "Thu":
        return 5
    elif day == "Fri":
        return 6
    elif day == "Sat":
        return 7
    else:
        return 8

# TODO
threading.Thread(target=check_timer).start()


def turn_on(sensor_id):
    # print (" Nhan du lieu : " + payload )
    print("Bat sensor so ", sensor_id)
    ser.write((str(1) + "#") . encode())
    # Map to port
    # turn on
    return


def turn_off(sensor_id):
    # Map to port
    print("tat sensor so ", sensor_id)
    ser.write((str(0) + "#").encode())


def on_():
    sensor_ = {"id": "1", "state": "on"}
    update_sensor_state({"id": 18, "state": "on"})


def off_():
    sensor_ = {"id": "1", "state": "off"}
    update_sensor_state({"id": 18, "state": "off"})


def set_env(target):
    ser.write((str(target) + "#") . encode())
    print(target, "humid")


def bump_manual():
    # turn off auto
    # TODO  ser.write (( str(4) + "#") . encode () )
    print("clear target")


while True:
    if isMicrobitConnected:
        # ser.write((str(1) + "#").encode())
        # ser.write((str(0) + "#").encode())
        readSerial()
        # cmd=input("state")
        # if cmd ==1:
        #     turn_on(10) #sensorID fake
        #     print("on")
        # else:
        #     print("off")
    # time.sleep(1)
