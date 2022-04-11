## Install request module by running ->
#  pip3 install requests

# Replace the deviceToken key with the device Token for which you want to send push notification.
# Replace serverToken key with your serverKey from Firebase Console

# Run script by ->
# python3 fcm_python.py
#ref:
#https://medium.com/@smbhuin/push-notification-firebase-python-8a65c47d3020
#https://medium.com/devmins/firebase-cloud-messaging-api-with-python-6c0755e41eb5
#https://stackoverflow.com/questions/37490629/firebase-send-notification-with-rest-api
#https://stackoverflow.com/questions/54821182/firebase-fcm-registration-token-in-flutter

import requests
import json

serverToken = 'AAAA1K6F6W4:APA91bGnvOZgxDvHbGJzqbe_RolQmzjobxfI_G1lD_LWMeQ3Ae3B_mNJRiFxtKeEhQBScvVWaBwQB5s940diLn5IWkZxl16PsPYyS7ylaIUCu6tDmE7kcJKwOTqgpMsXxeP9Q9iS65dK'
deviceToken = 'device token here'

headers = {
        'Content-Type': 'application/json',
        'Authorization': 'key=' + serverToken,
      }

body = {
          'notification': {'title': 'Sending push form python script',
                            'body': 'New Message'
                            },
          'to':
              deviceToken,
          'priority': 'high',
        #   'data': dataPayLoad,
        }
response = requests.post("https://fcm.googleapis.com/fcm/send",headers = headers, data=json.dumps(body))
print(response.status_code)

print(response.json())
