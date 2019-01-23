'''
The following JSON template shows what is sent as the payload:
{
    "serialNumber": "GXXXXXXXXXXXXXXXXX",
    "batteryVoltage": "xxmV",
    "clickType": "SINGLE" | "DOUBLE" | "LONG"
}

A "LONG" clickType is sent if the first press lasts longer than 1.5 seconds.
"SINGLE" and "DOUBLE" clickType payloads are sent for short clicks.

For more documentation, follow the link below.
http://docs.aws.amazon.com/iot/latest/developerguide/iot-lambda-rule.html
'''

from __future__ import print_function
import boto3
import json
import logging
import pprint

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sns = boto3.client('sns')
iotDataClient = boto3.client('iot-data')
phone_number = '15551230987'  # change it to your phone number


def lambda_handler(event, context):
    logger.info('Received event: ' + json.dumps(event))

    if event["clickType"] == "SINGLE":
      ledState = "on"
    elif event["clickType"] == "DOUBLE":
      ledState = "off"

    payload = {
      'state': {
         'desired': {
            'leds': ledState
          }
      }
    }

    result = iotDataClient.update_thing_shadow(thingName='rpi-sense-hat', payload=json.dumps(payload))
    print('update thing shadow result:')
    pp = pprint.PrettyPrinter()
    pp.pprint(json.loads(result['payload'].read()))


    message = 'Hello from your IoT Button %s. Here is the full event: %s' % (event['serialNumber'], json.dumps(event))
    sns.publish(PhoneNumber=phone_number, Message=message)
    logger.info('SMS has been sent to ' + phone_number)
