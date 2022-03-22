# firebase setup
from math import floor
import threading
import time
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore


# seconds = 1
# minutes = 60
# hours = 3600
# day = 86400
# week = 604800



# FIREBASE CONNECTION
# Use the application default credentials
cred = credentials.Certificate(
    "./aceteam-18b6b-firebase-adminsdk-agvz2-9b3044cbe9.json"
)
firebase_admin.initialize_app(cred)
db = firestore.client()


curr = {temp: 30, humid: 80, soil: 70}
account = "phuc"
local_sensor_id = ["1", "10"]


def update_env(self, curr):
    # TODO
    # curr.temp = readSerial()
    #
    meta_realtime_db = {
        "account_name": curr.account,
        "air_humidity": curr.humid,
        "env_temperature": curr.temp,
        "land_humidity": curr.soil,
        # TODO curr time
        "timestamp": "March 22, 2022 at 11:30:00 AM UTC+7",
    }
    db.collection("realtime_db").set(meta_realtime_db)


@firestore.transactional
def update_sensor_state(self, sensor):
    meta_sensor_log = {
        "account_name": account,
        "sensor_id": sensor.id,
        # TODO: modify later
        "time_start": time.localtime(),
        "duration": 0,
        "state": sensor.state,
    }

    transaction = db.transaction()
    log_ref = db.collection("log_sensor").where("sensor_ID", "==", sensor.id)
    # get the latest record
    latest_ref = log_ref.order_by(
        "time_start", direction=firestore.Query.DESCENDING
    ).limit(1)
    snapshot = latest_ref.get(transaction=transaction)
    new_duration = int(snapshot.get("time_start") - meta_sensor_log.time_start)

    # add duration for 0 duration record
    if sensor.state == 0:
        transaction.update(latest_ref, {"duration": new_duration})
    # check dupicate
    else:
        if latest_ref.get("duration") == 0:
            return
        else:
            db.collection("log_sensor").set(meta_sensor_log)


# Listening to database change
# Create an Event for notifying main thread.
callback_done = threading.Event()

# Create a callback on_snapshot function to capture changes
def log_on_snapshot(doc_snapshot, changes, read_time):
    # for doc in doc_snapshot:
    #     print(f"Received document snapshot: {doc.id}")
    for change in changes:
        if change.type.name == "ADDED":
            print(f"New sensor turn on: {change.document.id}")
            # TODO: call python turn on sensor_id
        elif change.type.name == "MODIFIED":
            print(f"Turn off sensor: {change.document.id}")
            # TODO: call python turn off sensor_id

        elif change.type.name == "REMOVED":
            # TODO edit print(f'Removed city: {change.document.id}')
            callback_done.set()

        toggle_sensor(change.get("sensor_id"))

    callback_done.set()


log_ref = db.collection("log_sensor").where("sensor_id", "in", local_sensor_id)

# Watch the document
log_watch = log_ref.on_snapshot(log_on_snapshot)


def timer_on_snapshot(doc_snapshot, changes, read_time):
    # for doc in doc_snapshot:
    #     print(f"Received document snapshot: {doc.id}")
    for change in changes:
        if change.type.name == "ADDED":
            print(f"New sensor turn on: {change.document.id}")
            # TODO: call python turn on sensor_id
        elif change.type.name == "MODIFIED":
            print(f"Turn off sensor: {change.document.id}")
            # TODO: call python turn off sensor_id

        elif change.type.name == "REMOVED":
            # TODO edit print(f'Removed city: {change.document.id}')
            callback_done.set()

    callback_done.set()


timer_ref = (
    db.collection("timer")
    .where("sensor_id", "in", local_sensor_id)
    .where("is_deleted", "==", False)
)
# Watch the document
timer_watch = timer_ref.on_snapshot(timer_on_snapshot)


def check_timer(self):
    """
    if outside this time range: do nothing
    if at the beginning this range: turn on, update DB
    if in the interval time: already turn on -> do nothing
    if at the end: turn off #TODO send signal to log sensor
    """
    for sensor in local_sensor_id:
        _schedule = timer_ref.where("sensor_id", "==", sensor).doc()
        nearest = nearest(_schedule)
        dur = _schedule["dur"]
        if on_time(nearest, dur, curr):
            if nearest == curr:
                # TODO turn on state
                _schedule.update({"last_record": curr})
            else:
                if on_time(nearest, dur, time(_schedule["last_update"])):
                    if curr == nearest + dur:
                        # TODO end freq
                        # send off signal
                        return


def nearest(self, _sche):
    ts = int(time(_sche["timestamp"]))
    pass_freq = floor((curr - ts) / _sche["freq"])
    return ts + _sche["dur"] * pass_freq


# def waiting_to_end(self, sche, nearest):
#     active_time = time(_schedule['last_record'])-nearest
#     return


def on_time(self, nearest, dur, _time):
    if _time - nearest <= dur:
        return True
    else:
        return False


def turn_on(self, sensor_id):
    # Map to port
    # turn on
    return


def turn_off(self, sensor_id):
    # Map to port
    # turn off
    return


def toggle_sensor(self, sensor_id):
    # map to port
    # toggle
    return
