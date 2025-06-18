from django.contrib import admin
from scheduler.models import *
# Register your models here.

list_per_page = 50

class emailScheduleAdmin(admin.ModelAdmin):
 
	list_display = ['codelink','sendToEmail', 'status','datetrans','timetrans',]
	search_fields = ('codelink__icontains',)
	list_filter = ('status',)


class emailSchedulesCtrlAdmin(admin.ModelAdmin):
	list_display = ['parameter','value','active',]

admin.site.register(emailSchedulesCtrl, emailSchedulesCtrlAdmin)

admin.site.register(emailschedule, emailScheduleAdmin)
