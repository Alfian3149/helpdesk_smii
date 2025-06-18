from django.contrib import admin
from .models import item, department, employee, position, approvalcode, cashapprover, frequest,crequest, approvalcrhistory, logemail, AllLogin, emailsent
# Register your models here.
from django.contrib.sessions.models import Session
from django.contrib.contenttypes.models import ContentType

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django import forms

admin.site.site_header = "Helpdesk Admin"
admin.site.site_title = "HELPDESK" 
admin.site.index_title = "Home" 

from import_export.admin import ImportExportModelAdmin


class FrequestAdmin(ImportExportModelAdmin):
	list_display = ['code', 'type', 'status', 'description', 'submitted']
	list_per_page = 10
	list_max_show_all = 100
	list_filter = ('type','status')
	ordering = ('id',)
	search_fields = ['code__icontains', 'description__icontains', ]

admin.site.register(frequest, FrequestAdmin)

class approvalcrhistoryForm(forms.ModelForm):
    class Meta:
        model = approvalcrhistory
        exclude = ['department']

class approvalcrhistoryAdmin(admin.ModelAdmin):
	list_display = ['crequest_id','employee', 'status',]
	list_per_page = 10 
	list_max_show_all = 100
	list_filter = ('status',)
	ordering = ('crequest_id',)
	search_fields = ['crequest__id', ] 
admin.site.register(approvalcrhistory, approvalcrhistoryAdmin)


class Inlineapprovalcrhistory(admin.TabularInline):
    model = approvalcrhistory
    extra = 1

class allLoginAdmin(admin.ModelAdmin):
	list_display = ['id','user', 'date',]
	list_per_page = 10 
	list_max_show_all = 100
	list_filter = ('date',)
	ordering = ('id',)
	search_fields = ['user', ] 

admin.site.register(AllLogin, allLoginAdmin)


class CrequestAdmin(ImportExportModelAdmin):
	inlines = [Inlineapprovalcrhistory]
	list_display = ['id','code', 'requestor', 'status', 'purpose',  'datecreated']
	list_per_page = 10 
	list_max_show_all = 100 
	list_filter = ('status',) 
	ordering = ('id',) 
	search_fields = ['code__icontains', 'purpose__icontains', 'requestor__icontains',]


admin.site.register(crequest, CrequestAdmin)

class ItemAdmin(ImportExportModelAdmin):
	list_display = ['item_name', 'item_type', 'item_price']
	list_per_page = 10
	list_max_show_all = 100
	list_filter = ('item_type',)
	search_fields = ['item_name__icontains', 'item_price__icontains', ]

admin.site.register(item, ItemAdmin)

class DepartmentAdmin(ImportExportModelAdmin):
	list_per_page = 20
	list_max_show_all = 100
	list_display = ['id', 'costcentre','name','approver']
	list_filter = ('name', )
	raw_id_fields = ['approver']

	search_fields = ['costcentre__icontains', 'name__icontains' ]

admin.site.register(department, DepartmentAdmin)

class EmployeeAdmin(ImportExportModelAdmin):
	exclude=['active',]
	list_per_page = 20
	list_max_show_all = 100
	list_display = ['empid','name','email','position','phone','user']
	raw_id_fields = ['head']
	list_filter = ('position', )
	search_fields = ['name__icontains', 'email__icontains', 'phone__icontains', ]

admin.site.register(employee, EmployeeAdmin)

class PositionAdmin(ImportExportModelAdmin):
	list_display = ['name', 'isapprover', 'isapprover_last','headposition']
	list_filter = ('isapprover', 'isapprover_last',)
	search_fields = ['name__icontains',  ]
	
admin.site.register(position,PositionAdmin)

class ProfileInline(admin.StackedInline):
    model = employee
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

class CustomUserAdmin(UserAdmin):
	fieldsets=(
		('Change User', {
			'fields':('username','password','is_active','is_staff','groups',)
		}),

	)
	list_display = ['username', 'is_active','is_staff',]

class ApprcodeAdmin(admin.ModelAdmin):
	list_display = ['code', 'condition', 'remarks']

class FrequestAdmin(admin.ModelAdmin):
	list_display = ['code', 'description', 'item', 'employee']

class CashApproverAdmin(admin.ModelAdmin):
	list_display = ['approver', 'backupapprover', 'remarks', 'approverorder']


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(cashapprover,CashApproverAdmin)

class logEmailAdmin(ImportExportModelAdmin):
	list_display = ['user','datetrans', 'timetrans','codelink','resendlink','message',]
	list_per_page = 10 
	list_max_show_all = 100
	ordering = ('id',)
	search_fields = ['codelink__icontains', ]
admin.site.register(logemail, logEmailAdmin)

class emailSentAdmin(admin.ModelAdmin):
	list_display = ['employee','datetrans', 'timetrans','codelink',]
	list_per_page = 10 
	list_max_show_all = 100
	ordering = ('-datetrans',)
	search_fields = ['codelink__icontains', ]
admin.site.register(emailsent, emailSentAdmin)