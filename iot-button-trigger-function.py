'''
This is a sample Lambda function that sends an SMS on click of a
button. It needs one permission sns:Publish. The following policy
allows SNS publish to SMS but not topics or endpoints.
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "sns:Publish"
            ],
            "Resource": [
                "*"
            ]
        },
        {
            "Effect": "Deny",
            "Action": [
                "sns:Publish"
            ],
            "Resource": [
                "arn:aws:sns:*:*:*"
            ]
        }
    ]
}
SMS messaging via SNS is only available in the following AWS IoT 1-Click regions:
- US East (N. Virginia)
- US West (Oregon)
- EU (Ireland)
- Asia Pacific (Tokyo)
The following JSON template shows what is sent as the payload:
{
    "deviceInfo": {
        "deviceId": "GXXXXXXXXXXXXXXX",
        "type": "button",
        "remainingLife": 98.7,
        "attributes": {
            "projectName": "Sample-Project",
            "projectRegion": "us-west-2",
            "placementName": "Room-1",
            "deviceTemplateName": "lightButton"
        }
    },
    "deviceEvent": {
        "buttonClicked": {
            "clickType": "SINGLE",
            "reportedTime": 1521159287205
        }
    },
    "placementInfo": {
        "projectName": "Sample-Project",
        "placementName": "Room-1",
        "attributes": {
            "key1": "value1"
        },
        "devices": {
            "lightButton":"GXXXXXXXXXXXXXXX"
        }
    }
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

thingName = 'etogw4_thing'

def lambda_handler(event, context):
    logger.info('Received event: ' + json.dumps(event))

    click_type = event['deviceEvent']['buttonClicked']['clickType']

    if click_type == "SINGLE":
      ledState = "on"
    elif click_type == "DOUBLE":
      ledState = "off"

    payload = {
      'state': {
         'desired': {
            'leds': ledState
          }
      }
    }

    result = iotDataClient.update_thing_shadow(thingName=thingName, payload=json.dumps(payload))
    print('update thing shadow result:')
    pp = pprint.PrettyPrinter()
    pp.pprint(json.loads(result['payload'].read()))


    attributes = event['placementInfo']['attributes']
    phone_number = attributes['phoneNumber']
    message = attributes['message']
    for key in attributes.keys():
        message = message.replace('{{%s}}' % (key), attributes[key])
    message = message.replace('{{*}}', json.dumps(attributes))
    dsn = event['deviceInfo']['deviceId']

    message += '\n(DSN: {}, {})'.format(dsn, click_type)
    sns.publish(PhoneNumber=phone_number, Message=message)
    logger.info('SMS has been sent to ' + phone_number)
