import os
import json
import base64
import traceback
import smtplib
import boto3

from email.message import EmailMessage


BUCKET = os.getenv("BUCKET")
SENDER = os.getenv("SENDER")
RECEIVER = os.getenv("RECEIVER")
ACCESS_KEY = os.getenv("ACCESS_KEY")


client = boto3.client("s3")
mailserver = smtplib.SMTP_SSL('smtp.gmail.com')
mailserver.login(SENDER, ACCESS_KEY)

def upload(img_data: str, key: str, appointment_id: str) -> bool:
    try:
        client.put_object(
            Bucket=BUCKET,
            Key=appointment_id + "/" + key,
            Body=img_data,
            ContentType="image/jpeg",
        )
        print("upload")
        return True

    except Exception:
        return False


def lambda_handler(event, context):
    appointment_id = event["appointment_id"]
    claim_yn = "Yes" if event["claim_yn"] == "y" else "No"

    message = EmailMessage()
    message["From"] = SENDER
    message["To"] = RECEIVER
    
    message["Subject"] = f"[UMEDI] Registered: Appointment ID {appointment_id}"
    body = f"""
    Booking Info:
        - Hospital: {event['hospital']}
        - Speciality: {event['speciality']}
        - Date1: {event['candidate_dt1']}
        - Date2: {event['candidate_dt2']}
    User Info:
        - First Name: {event['first_name']}
        - Last Name: {event['last_name']}
        - Phone: {event['phone']}
        - Email: {event['email']}
        - Insurance Claim: {claim_yn}
        - Gender: {event['gender']}
        - Date of Birth: {event['date_of_birth']}
    """
    message.set_content(body)
    
    if event["claim_yn"] == "y":
        try:
            for index, img in enumerate(event["insurance_imgs"]):
                img_str = img.split(",")[1]
                img_data = base64.b64decode(img_str)
                key = "{}_insurance_{:03d}.jpg".format(appointment_id, index)

                message.add_attachment(
                    img_data,
                    maintype="image",
                    subtype="jpeg",
                    filename=key
                )
                upload(img_data, key=key, appointment_id=appointment_id)

            for index, img in enumerate(event["additional_imgs"]):
                img_str = img.split(",")[1]
                img_data = base64.b64decode(img_str)
                key = "{}_medical_{:03d}.jpg".format(appointment_id, index)

                message.add_attachment(
                    img_data,
                    maintype="image",
                    subtype="jpeg",
                    filename=key
                )
                upload(img_data, key=key, appointment_id=appointment_id)
        except Exception:
            traceback.print_exc()
            return {
                'statusCode': 500,
                'body': json.dumps({"message": "internal server error"})
            }            

    mailserver.send_message(message)
    return {
        'statusCode': 200,
        'body': json.dumps('saved')
    }
