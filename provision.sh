sudo apt-get update
sudo apt-get install python3-pip jq git -y
alias pip='pip3' && echo "alias pip='pip3'" >> /home/pi/.bashrc
alias python='python3' && echo "python='python3'" >> /home/pi/.bashrc
pip3 install awscli --upgrade --user

mkdir cli-output
mkdir certificates
mkdir aws-iot
mv temperature_humidity.py ./aws-iot

THING_NAME=rpi-sense-hat
ACCOUNT_ID=$(aws sts get-caller-identity | jq -r '.Account')
IOT_ENDPOINT=$(aws iot describe-endpoint --endpoint-type iot:Data-ATS | jq -r '.endpointAddress')

aws iot create-thing --thing-name $THING_NAME > cli-output/create-thing-result.json

aws iot create-keys-and-certificate --set-as-active \
  --certificate-pem-outfile "certificates/${THING_NAME}.cert.pem" \
  --public-key-outfile "certificates/${THING_NAME}.public.key" \
  --private-key-outfile "certificates/${THING_NAME}.private.key" \
  > cli-output/create-keys-and-certificate-result.json


sed 's/{{account-id}}/'"$ACCOUNT_ID"'/g' templates/iot-policy.template > templates/iot-policy.json
aws iot create-policy \
  --policy-name "${THING_NAME}-Policy" \
  --policy-document file://templates/iot-policy.json \
  > cli-output/create-policy-result.json


aws iot attach-policy \
  --policy-name "${THING_NAME}-Policy" \
  --target $(cat cli-output/create-keys-and-certificate-result.json | jq -r '.certificateArn') \
  > cli-output/attach-policy-result.json


aws iot attach-thing-principal \
  --thing-name $THING_NAME \
  --principal $(cat cli-output/create-keys-and-certificate-result.json | jq -r '.certificateArn') \
  > cli-output/attach-thing-principal-result.json

mv certificates/"${THING_NAME}.cert.pem" aws-iot/
mv certificates/"${THING_NAME}.public.key" aws-iot/
mv certificates/"${THING_NAME}.private.key" aws-iot/

rm -r certificates

sed 's/{{aws-iot-endpoint}}/'"$IOT_ENDPOINT"'/g' templates/start.sh.template > templates/start.sh
sed -i 's/{{thing-name}}/'"$THING_NAME"'/g' templates/start.sh
mv templates/start.sh aws-iot/

sudo chmod +x aws-iot/start.sh

sudo chown -R 1000:1000 /usr/local/lib/python2.7
sudo chown -R 1000:1000 /usr/local/lib/python3.5
