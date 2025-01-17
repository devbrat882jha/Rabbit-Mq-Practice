import pika
import json
from app.models import User

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



connection = pika.BlockingConnection(
    pika.ConnectionParameters(host="localhost")
)
channel = connection.channel()

channel.exchange_declare(exchange='order', exchange_type='direct', durable=True)
channel.queue_declare(queue='email', durable=True)

channel.queue_bind(exchange="order", queue="email", routing_key='email')

MAILTRAP_USERNAME = "8770088b9e81bd"
MAILTRAP_PASSWORD = "c242bbaf71abb1"
MAILTRAP_SERVER = "smtp.mailtrap.io"
MAILTRAP_PORT = 587

def send_email(
        subject: str, 
        body: str, 
        to_email: str, 
        from_email: str 
        ):
    try:
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(MAILTRAP_SERVER, MAILTRAP_PORT) as server:
            server.login(MAILTRAP_USERNAME, MAILTRAP_PASSWORD)
            text = msg.as_string()
            server.sendmail(from_email, to_email, text)
            print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")


def callback(ch, method, properties, body):
    try:
       
       
        order_details=json.loads(body)
        
        data=order_details.get('data')
        order_id=data.get('order_id')
        user_id=data.get('user_id')
        event=order_details.get('event')
        user_email=data.get('email')
    
        if event=="placed":
            send_email(
                subject="Order Has been Placed",
                body=f"Your order with {order_id} has been successfully placed",
                to_email=user_email,from_email="noreply@yopmail.com")
            print(f"Email sent : Email_id {user_email}")

        elif event=="user_registered":
            send_email(
                subject="User Has been Registered",
                body=f"User wth email : {user_email} has been successfully created",
                to_email=user_email,from_email="noreply@yopmail.com")
            print(f"Email sent : Email_id {user_email}")
    except Exception as e:
             print(f"Error sending email : {e}")



    



channel.basic_consume(
    queue="email", on_message_callback=callback, auto_ack=True)


print("Waiting for messages...")

channel.start_consuming()