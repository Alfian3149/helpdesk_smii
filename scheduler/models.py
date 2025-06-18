from django.db import models

class emailschedule(models.Model):
	categoryStatus = (('INITIAL','INITIAL'),('SENT','SENT'),('FAILED','FAILED'),('TEST','TEST'))
	id = models.AutoField(primary_key = True)
	datetrans= models.DateTimeField(auto_now_add= True)
	timetrans = models.TimeField(auto_now=True)
	messageBody = models.TextField(null=True, blank=True)
	messageSubject = models.CharField(max_length=200)
	fromEmail = models.CharField(max_length=100)
	sendToEmail = models.CharField(max_length=50)
	codelink = models.CharField(max_length=20)
	status = models.CharField(max_length=10, choices=categoryStatus)
	
class emailSchedulesCtrl(models.Model):
    id = models.AutoField(primary_key = True)
    parameter = models.CharField(max_length=20)
    value = models.CharField(max_length=100)
    active = models.BooleanField(default=False, null=True, verbose_name='Is Active?')