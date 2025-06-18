from datetime import date
from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class test(models.Model):
    id = models.AutoField(primary_key = True)
    name =models.CharField(max_length=100, null=False)


class item(models.Model):
	category = (
		('CONSUMABLES','CONSUMABLES'),
		('PERIPHERAL','PERIPHERAL')
		)
	id = models.AutoField(primary_key = True)
	item_name = models.CharField(max_length=100, null=False)
	item_type = models.CharField(max_length=100, null=False, choices=category)
	item_price = models.DecimalField(max_digits=19,decimal_places=10)
	def __str__(self):
		return str(self.item_name) 
  
"""
	def save(self,*args, **kwargs):
		if self.item_price > 4999999:
			self.item_type = 'Peripheral'
		else:
			self.item_type= 'Consumable'
		super(item,self).save(*args,**kwargs)


	def __str__(self):
		return str(self.item_name)
"""

class department(models.Model):
	id = models.AutoField(primary_key = True)
	costcentre = models.CharField(max_length=8)
	name  = models.CharField(max_length=100)
	isapprover = models.BooleanField(default=False, null=True, verbose_name='Is IT Approver?')
	approver = models.ForeignKey('employee',null=True,blank=True, on_delete=models.CASCADE,related_name='cashapprover',verbose_name='First Approver of Cash Adv')
	
	def __str__(self):
		return str(self.costcentre) + " " + str(self.name) 

class position(models.Model):
	id = models.AutoField(primary_key = True)
	name  = models.CharField(max_length=100, null=False)
	isapprover = models.BooleanField(default=False, null=True, verbose_name='Is Approver level I?')
	isapprover_last = models.BooleanField(default=False, null=True, verbose_name='Is Approver Level II?')
	headposition =  models.ForeignKey('self', null=True,blank=True, on_delete=models.CASCADE, verbose_name='Head')

	def __str__(self):
		return str(self.name)

class employee(models.Model):
	id = models.AutoField(primary_key = True)
	empid = models.CharField(max_length=18,verbose_name='NIK')
	active = models.BooleanField(default=True)
	name  = models.CharField(max_length=100)
	email = models.CharField(max_length=100)

	departments = models.ManyToManyField(department)
	position = models.ForeignKey(position, null=True, on_delete=models.CASCADE)
	user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, verbose_name='User Login')	
	phone = models.CharField(max_length=15, null=True)
	area = models.TextField(null=True,blank=True)
	head =  models.ForeignKey('self', null=True,blank=True, on_delete=models.CASCADE, verbose_name='Atasan')

	def __str__(self):
		return str(self.name) 
		#return str(self.empid) + " " + str(self.name) 

class approvalcode(models.Model):
	id = models.AutoField(primary_key = True)
	code = models.CharField(max_length=8)
	condition = models.DecimalField(max_digits=19,decimal_places=10)
	#approval_one = models.ForeignKey(position, on_delete=models.CASCADE)
	#approval_two = models.ForeignKey(position, on_delete=models.CASCADE)
	#approval_three = models.ForeignKey(position, on_delete=models.CASCADE)
	#approval_four = models.ForeignKey(position, on_delete=models.CASCADE)
	#approval_five = models.ForeignKey(position, on_delete=models.CASCADE)
	remarks = models.CharField(max_length=50)

	def __str__(self):
		return str(self.code)

class cashapprover(models.Model):
	id = models.AutoField(primary_key = True)
	approver = models.ForeignKey(employee,null=True,blank=True, on_delete=models.CASCADE,related_name='approver')
	backupapprover =  models.ForeignKey(employee, null=True,blank=True,on_delete=models.CASCADE, related_name='backupapprover', verbose_name='Backup Approver')
	approverorder =models.IntegerField(null=True, verbose_name='Order')
	remarks = models.CharField(max_length=50) 
	def __str__(self):
		return str(self.approver)

class frequest(models.Model):
	id = models.AutoField(primary_key = True)
	code = models.CharField(max_length=20)
	type = models.CharField(max_length=8, null=True)
	description = models.TextField(null=True)
	item = models.ForeignKey(item, null=True, on_delete=models.CASCADE)
	employee = models.ForeignKey(employee, null=False, on_delete=models.CASCADE)
	status = models.CharField(max_length=8, null=True, default='DELAYED')
	submitted = models.DateField(default=date.today)
	department = models.ForeignKey(department, null=True, on_delete=models.CASCADE)

	class Meta:
		verbose_name = 'Form_Request'

class crequest(models.Model):
	id = models.AutoField(primary_key = True)
	code = models.CharField(max_length=20)
	requestorid = models.ForeignKey(employee, null=True,blank=True,on_delete=models.CASCADE, related_name='requestorid')

	employee = models.ForeignKey(employee, null=False, on_delete=models.CASCADE)
	deptuser = models.ForeignKey(department, null=True,blank=True,on_delete=models.CASCADE, related_name='deptuser')
	
	#requestor_id = models.BigIntegerField(null=True)
	requestor = models.CharField(max_length=100, null=True)
	department = models.ForeignKey(department, null=True, on_delete=models.CASCADE)
	costcentre = models.CharField(max_length=20)
	proposaldate = models.DateField()
	proposalyear = models.IntegerField(null=True) 
	amount = models.DecimalField(max_digits=19,decimal_places=10)
	needdate = models.DateField()
	purpose = models.TextField(null=True)
	status = models.CharField(max_length=15, null=True, default='DELAYED')
	datecreated = models.DateField(default=date.today)
	timecreated = models.TimeField(auto_now=True)
	est_settle = models.DateField(null=True)
	def __str__(self):
		return str(self.deptuser)

	class Meta:
		verbose_name = 'Cash_Request'

class approvalcrhistory(models.Model):
	id = models.AutoField(primary_key = True)
	crequest = models.ForeignKey(crequest, null=False, on_delete=models.CASCADE)
	employee = models.ForeignKey(employee, null=False, on_delete=models.CASCADE)
	datecreated = models.DateField(default=date.today)
	status	= models.CharField(max_length=18)
	department = models.ForeignKey(department, null=False, on_delete=models.CASCADE)


class approvalfrhistory(models.Model):
	id = models.AutoField(primary_key = True)
	frequest = models.ForeignKey(frequest, null=False, on_delete=models.CASCADE)
	employee = models.ForeignKey(employee, null=False, on_delete=models.CASCADE)
	datecreated = models.DateField(default=date.today)
	status	= models.CharField(max_length=18)
	department = models.ForeignKey(department, null=False, on_delete=models.CASCADE)

class frequestdetail(models.Model):
	id = models.AutoField(primary_key = True)
	frequest = models.ForeignKey(frequest, null=False, on_delete=models.CASCADE)
	employee = models.ForeignKey(employee, null=False, on_delete=models.CASCADE)
	datecreated = models.DateField(default=date.today)
	type = models.CharField(max_length=50,null=True)
	sn = models.CharField(max_length=50,null=True)
	startdate = models.DateField(null=True)
	starttime = models.CharField(max_length=15,null=True)
	finishdate = models.DateField(null=True)
	finishtime = models.CharField(max_length=15,null=True)
	hardware = models.CharField(max_length=50,null=True)
	software = models.CharField(max_length=50,null=True) 
	description = models.TextField(null=True)
	prf_accepted = models.CharField(max_length=15,null=True)
	prf_inbudget =  models.BooleanField(default=False, null=True, verbose_name='In Budget?')
	prf_underfive =  models.BooleanField(default=False, null=True, verbose_name='underfive?')
	prf_notes = models.TextField(null=True,blank=True)

class AllLogin(models.Model):
    id = models.AutoField(primary_key = True) 
    user= models.ForeignKey(User, null=False, on_delete=models.CASCADE)
    date= models.DateTimeField(auto_now_add= True)

    def __str__(self):
        return str(self.user) + ': ' + str(self.date)

class logemail(models.Model):
    id = models.AutoField(primary_key = True)
    user= models.ForeignKey(User, null=False, on_delete=models.CASCADE)
    datetrans= models.DateTimeField(auto_now_add= True)
    timetrans = models.TimeField(auto_now=True)
    message = models.TextField(null=True, blank=True)
    resendlink = models.TextField(null=True, blank=True)
    codelink = models.CharField(max_length=20)
    
    
class emailsent(models.Model):
    id = models.AutoField(primary_key = True)
    employee= models.ForeignKey(employee, null=False, on_delete=models.CASCADE)
    datetrans= models.DateTimeField(auto_now_add= True)
    timetrans = models.TimeField(auto_now=True)
    message = models.TextField(null=True, blank=True)
    resendlink = models.TextField(null=True, blank=True)
    codelink = models.CharField(max_length=20)