# AWS IoT, IoT 1-Click Enterprise Button, and Raspberry Pi SenseHat Demo

![AWS IoT, IoT 1-Click Enterprise Button, and Raspberry Pi SenseHat Demo architecture](architecture.png "AWS IoT, IoT 1-Click Enterprise Button, and Raspberry Pi SenseHat Demo architecture")

## Raspberry Pi Setup

### AWS IoT Service

Copy the `aws-iot.service` file to `/etc/systemd/system/aws-iot.service`:

`sudo cp ./aws-iot.service /etc/systemd/system/`

Enable the service:

`sudo systemctl enable aws-iot.service`

Start the service:

`sudo systemctl status aws-iot.service`

Check the status of the service:

`sudo systemctl status aws-iot.service`
