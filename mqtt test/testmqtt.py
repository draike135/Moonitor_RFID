import random
import time
from paho.mqtt import client as mqtt_client
import json
import base64
import firebase_admin
from firebase_admin import credentials, firestore


#FUNCIONA:
#mosquitto_sub -h eu1.cloud.thethings.network -p 1883 -d -t "v3/eitt2024@ttn/devices/eui-70b3d57ed00678df/up" -u "eitt2024" -P "NNSXS.7H4R2QX7P3QPBNJHKO4Y5GZQ7D3M64LW5LLSULA.L3JVZYKVKNYKGVJQPQ75BI2RDFRJXKYPCTCMRA6LY2CXDSQQONEA"mosquitto_sub -h eu1.cloud.thethings.network -p 1883 -d -t "v3/eitt2024@ttn/devices/eui-70b3d57ed00678df/up" -u "eitt2024" -P "NNSXS.7H4R2QX7P3QPBNJHKO4Y5GZQ7D3M64LW5LLSULA.L3JVZYKVKNYKGVJQPQ75BI2RDFRJXKYPCTCMRA6LY2CXDSQQONEA"




broker = 'eu1.cloud.thethings.network'
port = 1883
topic = "v3/eitt2024@ttn/devices/eui-70b3d57ed00678df/up"

client_id = f'python-mqtt-{random.randint(0, 1000)}'
username = 'eitt2024'
password = 'NNSXS.7H4R2QX7P3QPBNJHKO4Y5GZQ7D3M64LW5LLSULA.L3JVZYKVKNYKGVJQPQ75BI2RDFRJXKYPCTCMRA6LY2CXDSQQONEA'


cred = credentials.Certificate(r'C:\Users\ASUS\Desktop\EITT\Prototype\new\mqtt test\iot-alarm-app-165dc-firebase-adminsdk-jl2nt-a9bfb0be4c.json')

# Initialize the Firebase app
firebase_admin.initialize_app(cred, {
    'projectId': 'iot-alarm-app-165dc',  # replace with your actual project ID
})

# Get a reference to the Firestore service
db = firestore.client()



def on_message(client, userdata, msg):
    print("MESSAGE")
    print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
    json_string =msg.payload.decode()
    # Parse the JSON string
    data = json.loads(json_string)
    # Extract the frm_payload
    frm_payload = data['uplink_message']['frm_payload']
    # Extract the time from the rx_metadata list
    time = data['uplink_message']['rx_metadata'][0]['time']
    # Print the extracted values
    print("frm_payload:", base64.b64decode(frm_payload).decode('utf-8'))
    print("time:", time[0:19].replace('T', ','))
    data={'date_and_time': time[0:19].replace('T', ','),
            'info': base64.b64decode(frm_payload).decode('utf-8')}
    db.collection('your_collection_name').add(data)



def on_subscribe(client, userdata, mid, granted_qos):
    print("SUBSCRIBE")

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n" % rc)

    print("client_id =",client_id)

    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def publish(client):
    msg_count = 1
    while True:
        time.sleep(1)
        msg = f"messages: {msg_count}"
        result = client.publish(topic, msg)
        # result: [0, 1]
        status = result[0]
        if status == 0:
            print(f"Send `{msg}` to topic `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")
        msg_count += 1
        if msg_count > 5:
            break


def run():
    client = connect_mqtt()

    client.on_message=on_message
    client.on_subscribe=on_subscribe
    client.subscribe(topic)

    client.loop_forever()  # Start networking daemon

    #client.loop_start()
    #publish(client)
    #client.loop_stop()


if __name__ == '__main__':
    run()