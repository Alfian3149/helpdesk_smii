from scheduler.models import *
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.core import mail


def my_scheduled_job():
	dataEmail = emailschedule.objects.all().filter(status='INITIAL').first()
	
	if dataEmail is not None:
		sendToEmail = dataEmail.sendToEmail
		emailSchedulesCtrls = emailSchedulesCtrl.objects.all().filter(parameter='FORCE_EMAIL', active=True).last()
		if emailSchedulesCtrls is not None:
			sendToEmail = emailSchedulesCtrls.value
		
		text_content = 'This is an important message.'
		msg = EmailMultiAlternatives(dataEmail.messageSubject, text_content, dataEmail.fromEmail, [sendToEmail])
		msg.attach_alternative(dataEmail.messageBody, "text/html")
		
		try:
			msg.send()  
			dataEmail.status = 'SENT'
			dataEmail.save()
		except Exception:
			dataEmail.status = 'FAILED'
			dataEmail.save()