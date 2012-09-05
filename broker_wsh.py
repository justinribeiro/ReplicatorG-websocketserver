#!/usr/bin/python

import mosquitto
from mod_pywebsocket import msgutil

import thread
import json
import random
import string
import time

_INFO = 'info'
_CONNECTING_ = 0
_OPEN_ = 1
_CLOSING_ = 2
_CLOSE_ = 3

_status_ = _CONNECTING_

_BROKER_URL = "some_magical_mqtt_broker_host"
_BROKER_PORT = 1883
_TOPIC_BASE = "makerbot/status"

class broker():

    def __init__(self, url, port, topic, socket):
        self.url = url
        self.port = port
        self.socket = socket
        self.topic = topic
        self.clientid = ''.join(random.choice(string.ascii_letters + string.digits) for letter in xrange(23))
        self.client = mosquitto.Mosquitto(self.clientid)

        self.client.on_message = self.onMessage
        self.client.on_connect = self.onConnect
        self.client.on_subscribe = self.onSubscribe
        self.client.on_publish = self.onPublish

        self.client.connect(self.url, self.port, 60)
        self.client.subscribe(_TOPIC_BASE + "/#", 2)


    def onMessage(self, mosq, obj, msg):
        if _status_ == _OPEN_:
            string = json.dumps({"topic": msg.topic, "message": msg.payload})
            msgutil.send_message(self.socket, string)

    def onConnect(self, mosq, obj, rc):
        if rc == 0:
            string = json.dumps({"topic": self.topic + "/server", "message": "Connected to Mosquitto MQTT Broker"})
            msgutil.send_message(self.socket, string)

    def onSubscribe(self, mosq, obj, mid, granted_qos):
        if _status_ == _OPEN_:
            string = json.dumps({"topic": self.topic + "/server", "message": "Subscribed to topic"})
            msgutil.send_message(self.socket, string)

    def onPublish(self, mosq, obj, mid):
        if _status_ == _OPEN_:
            string = json.dumps({"topic": self.topic + "/server", "message": "Message published to broker"})
            msgutil.send_message(self.socket, string)

    def run(self):
        global _status_

        #keep web socket connected while mqtt is connected
        while self.client.loop() == 0:
            pass

    def requestMachineInfo(self):
        #client.publish(topic, payload=None, qos=0, retain=false)
        self.client.publish(_TOPIC_BASE + "/get", "info", 1)


def web_socket_do_extra_handshake(request):
    pass  # Always accept.


def web_socket_transfer_data(request):
    global _status_
    _status_ = _OPEN_

    instance = broker(_BROKER_URL, _BROKER_PORT, _TOPIC_BASE, request)

    arr = ()
    talk = thread.start_new_thread(instance.run, arr)
    while True:
        try:
            line = msgutil.receive_message(request).encode('utf-8')

            if line == _INFO:
                instance.requestMachineInfo()
                continue


        except Exception:
            _status_ = _CLOSING_

        time.sleep(5)

