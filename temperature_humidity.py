# -*- coding: utf-8 -*-
'''
/*
 * Copyright 2010-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *  http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */
 '''

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
from sense_hat import SenseHat
import logging
import time
import argparse
import json
import threading
import sys
import signal

sense = SenseHat()

class PixelsThread(threading.Thread):
    pixels = [
        [255, 0, 0], [255, 0, 0], [255, 87, 0], [255, 196, 0], [205, 255, 0], [95, 255, 0], [0, 255, 13], [0, 255, 122],
        [255, 0, 0], [255, 96, 0], [255, 205, 0], [196, 255, 0], [87, 255, 0], [0, 255, 22], [0, 255, 131], [0, 255, 240],
        [255, 105, 0], [255, 214, 0], [187, 255, 0], [78, 255, 0], [0, 255, 30], [0, 255, 140], [0, 255, 248], [0, 152, 255],
        [255, 223, 0], [178, 255, 0], [70, 255, 0], [0, 255, 40], [0, 255, 148], [0, 253, 255], [0, 144, 255], [0, 34, 255],
        [170, 255, 0], [61, 255, 0], [0, 255, 48], [0, 255, 157], [0, 243, 255], [0, 134, 255], [0, 26, 255], [83, 0, 255],
        [52, 255, 0], [0, 255, 57], [0, 255, 166], [0, 235, 255], [0, 126, 255], [0, 17, 255], [92, 0, 255], [201, 0, 255],
        [0, 255, 66], [0, 255, 174], [0, 226, 255], [0, 117, 255], [0, 8, 255], [100, 0, 255], [210, 0, 255], [255, 0, 192],
        [0, 255, 183], [0, 217, 255], [0, 109, 255], [0, 0, 255], [110, 0, 255], [218, 0, 255], [255, 0, 183], [255, 0, 74]
    ]

    def __init__(self, sense_hat):
      threading.Thread.__init__(self)
      self.sense_hat = sense_hat
      self.shutdown_flag = threading.Event()

    def next_colour(self, pix):
       r = pix[0]
       g = pix[1]
       b = pix[2]

       if (r == 255 and g < 255 and b == 0):
           g += 1

       if (g == 255 and r > 0 and b == 0):
           r -= 1

       if (g == 255 and b < 255 and r == 0):
           b += 1

       if (b == 255 and g > 0 and r == 0):
           g -= 1

       if (b == 255 and r < 255 and g == 0):
           r += 1

       if (r == 255 and b > 0 and g == 0):
           b -= 1

       pix[0] = r
       pix[1] = g
       pix[2] = b

    def run(self):
      while True:
        while not self.shutdown_flag.is_set():
          for pix in self.pixels:
            self.next_colour(pix)

          self.sense_hat.set_pixels(self.pixels)
          time.sleep(2 / 1000.0)

        self.sense_hat.clear()


pixelsThread = PixelsThread(sense)
pixelsThread.daemon = True

# Shadow Delta Listener Callback
def shadowDeltaListenerCallback(payload, responseStatus, token):
  # payload is a JSON string ready to be parsed using json.loads(...)
  # in both Py2.x and Py3.x
  print(responseStatus)
  print(payload)
  payloadDict = json.loads(payload)

  leds = str(payloadDict["state"]["leds"])

  print("++++++++DELTA++++++++++")
  print("leds: " + leds)
  print("version: " + str(payloadDict["version"]))
  print("+++++++++++++++++++++++\n\n")

  if leds == "on" and not pixelsThread.isAlive():
    pixelsThread.start()
  elif leds == "on" and pixelsThread.isAlive():
    pixelsThread.shutdown_flag.clear()
  elif leds == "off" and pixelsThread.isAlive():
    pixelsThread.shutdown_flag.set()



# Read in command-line parameters
parser = argparse.ArgumentParser()
parser.add_argument("-e", "--endpoint", action="store", required=True, dest="host", help="Your AWS IoT custom endpoint")
parser.add_argument("-r", "--rootCA", action="store", required=True, dest="rootCAPath", help="Root CA file path")
parser.add_argument("-c", "--cert", action="store", dest="certificatePath", help="Certificate file path")
parser.add_argument("-k", "--key", action="store", dest="privateKeyPath", help="Private key file path")
parser.add_argument("-id", "--clientId", action="store", dest="clientId", default="basicPubSub", help="Targeted client id")
parser.add_argument("-t", "--topic", action="store", dest="topic", default="rpi/sense_hat", help="Targeted topic")


args = parser.parse_args()
host = args.host
rootCAPath = args.rootCAPath
certificatePath = args.certificatePath
privateKeyPath = args.privateKeyPath
clientId = args.clientId
thingName = args.clientId
topic = args.topic
port = 8883

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.INFO)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Init AWSIoTMQTTClient
mqttClient = AWSIoTMQTTClient(clientId)
mqttClient.configureEndpoint(host, port)
mqttClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
mqttClient.configureAutoReconnectBackoffTime(1, 32, 20)
mqttClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
mqttClient.configureDrainingFrequency(2)  # Draining: 2 Hz
mqttClient.configureConnectDisconnectTimeout(10)  # 10 sec
mqttClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
mqttClient.connect()


# Init AWSIoTMQTTShadowClient
shadowClient = AWSIoTMQTTShadowClient('{}-{}'.format(clientId, 'shadowClient'))
shadowClient.configureEndpoint(host, port)
shadowClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTShadowClient configuration
shadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
shadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
shadowClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect to AWS IoT
shadowClient.connect()

# Create a deviceShadow with persistent subscription
deviceShadowHandler = shadowClient.createShadowHandlerWithName(thingName, True)

# Listen on deltas
deviceShadowHandler.shadowRegisterDeltaCallback(shadowDeltaListenerCallback)


def cleanup(*args):
  sense.clear()
  sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

# red = (255, 0, 0)
messageCount = 0
while True:
  humidity = sense.get_humidity()
  temp_c = sense.get_temperature()

  message = {}
  message['temperature_c'] = temp_c
  message['humidity'] = humidity
  message['sequence'] = messageCount
  messageJson = json.dumps(message)
  mqttClient.publish(topic, messageJson, 1)
  print('Published message to topic %s: %s\n' % (topic, messageJson))
  messageCount += 1

  # message = '{:.1f}C {:.1f}%H'.format(temp_c, humidity)
  # print(message)
  # sense.show_message(message, text_colour=red)
  time.sleep(10)
