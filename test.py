import time
import sys
from Adafruit_IO import MQTTClient

import threading
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import datetime


cred = credentials.Certificate(
    "./aceteam-18b6b-firebase-adminsdk-agvz2-9b3044cbe9.json"
)
firebase_admin.initialize_app(cred)
db = firestore.client()


curr = {"account": "giacat", "temp": 30, "humid": 80, "soil": 70}
local_sensor_id = [1, 10]
area="garden"
bump = 19
START = 1
END = 2
OUT = 0


AIO_FEED_IDS = ["BBC_TEMP", "BBC_HUMI", "BBC_LED"]
AIO_USERNAME = "chuong200115"
AIO_KEY = "aio_ptdx29Phh4tq7orUSDKCAYaNycz0"


def connected(client):
    print("Ket noi thanh cong...")
    for feed in AIO_FEED_IDS:
        client.subscribe(feed)


def processData():
    print("send data")
    curr['ts'] = time.localtime()
    update_env(curr)


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
    print("update")


mess = ""


def readSerial():
    processData()
    print("done update")


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

# Create a callback on_snapshot function to capture changes


def log_on_snapshot(doc_snapshot, changes, read_time):
    for change in changes:
        if change.type.name == "ADDED":
            # print(f"New sensor turn on: {change.document.id}")
            turn_on(change.document._data['sensor_id'])

        elif change.type.name == "MODIFIED":
            # print(f"Turn off sensor: {change.document.id}")
            turn_off(change.document._data['sensor_id'])

        elif change.type.name == "REMOVED":
            callback_done.set()
    callback_done.set()


def log_on_snapshot(doc_snapshot, changes, read_time):
    for change in changes:
        if change.type.name == "ADDED":
            # print(f"New sensor turn on: {change.document.id}")
            turn_on(change.document._data['sensor_id'])

        elif change.type.name == "MODIFIED":
            # print(f"Turn off sensor: {change.document.id}")
            turn_off(change.document._data['sensor_id'])

        elif change.type.name == "REMOVED":
            callback_done.set()
    callback_done.set()


def timer_on_snapshot(doc_snapshot, changes, read_time):
    for change in changes:
        print(f"New timer on: {change.document.id}")
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


# log_ref = db.collection("log_sensor").where(
#     "sensor_id", u"in", local_sensor_id)
# log_watch = log_ref.on_snapshot(log_on_snapshot)

# timer_ref = db.collection("timer")    .where(
#     "sensor_id", u"in", local_sensor_id)
# timer_watch = timer_ref.on_snapshot(timer_on_snapshot)

# env_ref = db.collection("target_env").where(
#     "sensor_id", u"==", bump)
# env_watch = env_ref.on_snapshot(env_on_snapshot)


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


# threading.Thread(target=check_timer).start()


def turn_on(sensor_id):
    print("Bat sensor so ", sensor_id)
    m = "on"
    # ser.write (( str(1) + "#") . encode () )
    # Map to port


def turn_off(sensor_id):
    print("tat sensor so ", sensor_id)
    m = "off"
    # Map to port
    # ser.write((str(0) + "#").encode())
    # turn off
    # return


def on_():
    sensor_ = {"id": "1", "state": "on"}
    update_sensor_state({"id": 1, "state": "on"})


def off_():
    sensor_ = {"id": "1", "state": "off"}
    update_sensor_state({"id": 1, "state": "off"})


def toggle_sensor(self, sensor_id):
    # map to port
    # toggle
    return


def set_env(target):
    # TODO ser.write (( str(target) + "#") . encode () )
    print(target, "humid")


def bump_manual():
    # turn off auto
    # TODO  ser.write (( str(4) + "#") . encode () )
    print("clear target")


while True:
    # input("call func: ")
    val = input("call func: ")
    if val == "0":
        readSerial()
    elif val == "1":
        turn_off(1)
    elif val == "2":
        turn_on(1)
    elif val == '3':
        off_()
    elif val == "4":
        on_()
    elif val == "5":
        print(datetime.datetime.now())
    elif val=="6":
        update_env(curr)

    # log_watch = log_ref.on_snapshot(log_on_snapshot)


def init():
    for sensor in local_sensor_id:
        update_sensor_state({"id": sensor, "state": "off"})
