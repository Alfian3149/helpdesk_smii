import os
from email.message import EmailMessage
import ssl
import smtplib


email_sender = 'emgmt@smii.co.id'
email_password = 'Smii3mgmt'
email_receiver = 'alfianpical3149@gmail.com'

subject = 'test Email SMII'
body = """
only testing email

"""

em = EmailMessage()
em['From'] = email_sender
em['To'] = email_receiver
em['Subject'] = subject

em.set_content(body)

context = ssl.create_default_context()

with smtplib.SMTP_SSL('mail.smii.co.id', 465, context=context) as smtp:
   smtp.login(email_sender, email_password)
   smtp.sendmail(email_sender, email_receiver, em.as_string())