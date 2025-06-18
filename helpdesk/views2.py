#import datetime
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render, reverse

from .models import crequest, department, employee, frequest, item, approvalfrhistory,frequestdetail,position,approvalcrhistory, cashapprover,AllLogin

from datetime import datetime, timedelta
from django.contrib.humanize.templatetags.humanize import intcomma

from .flogic import *
from django.db.models import Q
from django.template.defaultfilters import linebreaksbr
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.decorators import login_required

from django.http import Http404

def get_topics_ajax(request):
    if request.method == "POST":
        positionid = request.POST['positionid']
        try:
            empldept = employee.objects.all().filter(departments__in = positionid)

            positions = position.objects.get(id = positionid)
            employees = employee.objects.all().filter(position_id = positions.id)
        except Exception:
            data['error_message'] = 'ERROR AJAX'
            return JsonResponse(data)
        return JsonResponse(list(empldept.values('id', 'name')), safe = False) 

def get_employee_department_ajax(request):
    if request.method == "POST":
        positionid = request.POST['positionid']
        try:
            empldept = employee.objects.all().filter(departments__in = positionid).order_by('name')
        except Exception:
            data['error_message'] = 'ERROR AJAX'
            return JsonResponse(data)
        return JsonResponse(list(empldept.values('id', 'name')), safe = False) 


def listToString(s):   
    str1 = ","   
    return (str1.join(s))
       

def test(request):
    employees = employee.objects.all()
    return render(request, 'helpdesk/test.html', {'employees': employees})

@login_required(login_url='/loginPage')
def index(request):
    try:
        employees = employee.objects.get(user_id=request.user.id) 
    except employee.DoesNotExist:
        logout(request)
        messages.error(request, 'User does not allowed to login') 
        return render(request, 'helpdesk/login.html')
    else:
        crfByEmployeeIDCount=frequest.objects.filter(employee_id=employees.id, type='CRF').count()
        srfByEmployeeIDCount=frequest.objects.filter(employee_id=employees.id, type='SRF').count()
        prfByEmployeeIDCount=frequest.objects.filter(employee_id=employees.id, type='PRF').count()
        cashAdvanceByEmployeeIDCount=crequest.objects.filter(Q(employee_id=employees.id)|Q(requestorid_id=employees.id)).count()

        AllLogins = AllLogin.objects.all().filter(user_id=request.user.id).order_by('-id')[:10]
    
    return render(request, 'helpdesk/userProfile.html',{'employees':employees,'crfByEmployeeIDCount':crfByEmployeeIDCount,'srfByEmployeeIDCount':srfByEmployeeIDCount,'prfByEmployeeIDCount':prfByEmployeeIDCount,'cashAdvanceByEmployeeIDCount':cashAdvanceByEmployeeIDCount, 'AllLogins':AllLogins})

@login_required(login_url='/loginPage')
def crf(request):
    lastcode = get_last_number('CRF') 
    employees = employee.objects.get(user_id=request.user.id) 
    items = item.objects.all().filter(item_type='Consumable').order_by('item_name') 
    #emplo_dept = employees.employee.departement.objects.all()
 	#return render(request, 'helpdesk/crf.html', {'employees': employees})
    return render(request, 'helpdesk/crf.html', {'employees': employees, 'items' : items, 'lastcode':lastcode })

@login_required(login_url='/loginPage')
def crfview(request, id, action):
    employee_user = employee.objects.get(user_id=request.user.id)
    frequests = frequest.objects.get(id=id)
    employees = employee.objects.get(id=frequests.employee_id) 
    approvalfrhistorys = approvalfrhistory.objects.filter(frequest_id=frequests.id)
    isapprover = get_isapprover(employee_user.id, frequests.id, frequests.department_id)
    isapprover_mis = get_isapprover_mis(employee_user.id)
    approver_wizard = get_approver_frequest_depthead_wizard(frequests.id, frequests.department_id)
    
    isapproved_mis = get_isapproved_frequest_misdept_wizard(frequests.id)
    
    isdelayed = True
    for approvalfrhistory_records in approvalfrhistorys:
        isdelayed = False   

    approver_department = frequests.department_id
    
    if isapprover_mis :
        department_mis = department.objects.get(isapprover=True)
        approver_department = department_mis.id

    if action == 2000 :
        approvalfrhistorys = approvalfrhistory(frequest_id=id, employee_id=employee_user.id, status='ACCEPTED', department_id=approver_department)
        approvalfrhistorys.save()

        if isapprover_mis :
            frequests.status = 'FINISHED'
        else:
            frequests.status = 'APPROVE'

        frequests.save()
    elif action == 3000 :
        approvalfrhistorys = approvalfrhistory(frequest_id=id, employee_id=employee_user.id, status='REJECTED', department_id=approver_department)
        approvalfrhistorys.save()
        frequests.status = 'REJECTED'
        frequests.save()

    if (isapprover_mis == False) and (action > 1000): 
        sendEmail = sendEmailWhenApproveDeptHead(frequests.code, frequests.status)
        return HttpResponseRedirect('/crfview/' + str(id) + '/1000' )


    return render(request, 'helpdesk/crfview.html', 
        {'employees': employees,'frequests':frequests, 
        'isapprover':isapprover,'approvalfrhistorys':approvalfrhistorys,
        'approver_wizard':approver_wizard,
        'isapproved_mis':isapproved_mis,
        'isapprover_mis':isapprover_mis,
        'isdelayed':isdelayed})

def submitmiscrf(request): 
    if request.method == 'POST':
        pfrequest_id = request.POST['frequest_id']   
        pemployeeid = request.POST['employee_id']   
        pstatus = request.POST['status']   
        department_mis = department.objects.get(isapprover=True)
        approver_department = department_mis.id

        employee_user = employee.objects.get(user_id=request.user.id)

        frequests = frequest.objects.get(id=pfrequest_id)

        approvalfrhistory_exist = approvalfrhistory.objects.all().filter(frequest_id=pfrequest_id, department_id=approver_department).last()

        if approvalfrhistory_exist is None:
            if pstatus != "DELAYED" :
                approvalfrhistorys = approvalfrhistory(frequest_id=pfrequest_id, employee_id=employee_user.id, status=pstatus, department_id=approver_department)
                approvalfrhistorys.save()

                if pstatus == 'ACCEPTED' :
                    frequests.status = 'FINISHED'
                else: 
                    frequests.status = pstatus

                frequests.save()
            
                messages.success(request, 'submitted') 
        else:
            messages.error(request, 'Already submitted') 

    return HttpResponseRedirect('/crfview/' + str(pfrequest_id) + '/1000' )

def submitcrf(request):
    try:
        employeeid = request.POST['employee_id']
        codenumber = request.POST['codenumber']
        itemcode = request.POST['itemcode']
        departselect = request.POST['departselect']

        if codenumber == '':
            messages.error(request, 'CRF number cannot be blank') 
            return HttpResponseRedirect(reverse('crf'))
        elif itemcode == '':
            messages.error(request, 'Item should be choosen') 
            return HttpResponseRedirect(reverse('crf'))
        else:
            frequests = frequest(code=codenumber, type='CRF', description='', employee_id=employeeid, item_id=itemcode, department_id=departselect)
            frequests.save()
            messages.success(request, codenumber + ' submitted..') 

            emailSend = emailSendWhenSubmit('Consumables Request Forms (CRF)', departselect, codenumber)
            return HttpResponseRedirect(reverse('crf'))
    except Exception:
        messages.error(request, 'Failed to submit') 
        return HttpResponseRedirect(reverse('crf')) 
 
def crfapproveemailDeptHead(request, codenumber, empid, departid, action):
    frequests = frequest.objects.get(code=codenumber)
    checkApproval = approvalfrhistory.objects.filter(frequest_id=frequests.id).count()
    statusInfo = ''

    if checkApproval == 0 : 
        if action == 2000 :
            approvalfrhistorys = approvalfrhistory(frequest_id=frequests.id, employee_id=empid, status='ACCEPTED', department_id=departid)
            approvalfrhistorys.save()
            
            statusInfo = 'Approved'
            frequests.status = 'APPROVE'
            frequests.save()
        elif action == 3000 :
            approvalfrhistorys = approvalfrhistory(frequest_id=frequests.id, employee_id=empid, status='REJECTED', department_id=departid)
            approvalfrhistorys.save()

            statusInfo = 'Rejected'
            frequests.status = 'REJECTED'
            frequests.save()  
        
        sendEmail = sendEmailWhenApproveDeptHead(codenumber, statusInfo)
    return render(request, 'helpdesk/windowautoclose.html')


def prfapproveemailDeptHead(request, codenumber, empid, departid, action):
    frequests = frequest.objects.get(code=codenumber)
    checkApproval = approvalfrhistory.objects.filter(frequest_id=frequests.id).count()
    statusInfo = ''
    if checkApproval == 0 : 
        if action == 2000 :
            approvalfrhistorys = approvalfrhistory(frequest_id=frequests.id, employee_id=empid, status='ACCEPTED', department_id=departid)
            approvalfrhistorys.save()
            
            statusInfo = 'Approved'
            frequests.status = 'APPROVE'
            frequests.save()
        elif action == 3000 :
            approvalfrhistorys = approvalfrhistory(frequest_id=frequests.id, employee_id=empid, status='REJECTED', department_id=departid)
            approvalfrhistorys.save()

            statusInfo = 'Rejected'
            frequests.status = 'REJECTED'
            frequests.save()  
        
        sendEmail = sendEmailWhenApproveDeptHead(codenumber, statusInfo)

    return render(request, 'helpdesk/windowautoclose.html')

def prfapproveemailGenMGR(request, codenumber, empid, departid, action):
    frequests = frequest.objects.get(code=codenumber)
    checkApproval = approvalfrhistory.objects.filter(frequest_id=frequests.id).count()
    statusInfo = ''
    if checkApproval == 1 : 
        if action == 2000 :
            approvalfrhistorys = approvalfrhistory(frequest_id=frequests.id, employee_id=empid, status='ACCEPTED', department_id=departid)
            approvalfrhistorys.save()
            
            statusInfo = 'Approved'
            frequests.status = 'APPROVE'
            frequests.save()
        elif action == 3000 :
            approvalfrhistorys = approvalfrhistory(frequest_id=frequests.id, employee_id=empid, status='REJECTED', department_id=departid)
            approvalfrhistorys.save()

            statusInfo = 'Rejected'
            frequests.status = 'REJECTED'
            frequests.save()  

        sendEmail = sendEmailWhenApproveGenMGR(codenumber, statusInfo)

    return render(request, 'helpdesk/windowautoclose.html')

@login_required(login_url='/loginPage')
def frequest_list(request):
    return render(request, 'helpdesk/frequest_list.html')
 

@login_required(login_url='/loginPage')
def srf(request):
    lastcode = get_last_number('SRF') 

    employees = employee.objects.get(user_id=request.user.id) 
    items = item.objects.all().order_by('item_name') 
    return render(request, 'helpdesk/srf.html', {'employees': employees, 'items' : items, 'lastcode':lastcode })

def submitsrf(request):
    try:
        employeeid = request.POST['employee_id']
        codenumber = request.POST['codenumber']
        desc = request.POST['desc']
        departselect = request.POST['departselect']


        if codenumber == '':
            messages.error(request, 'SRF number cannot be blank') 
            return HttpResponseRedirect(reverse('srf'))
        elif desc == '':
            messages.error(request, 'FAULT DESCRIPTION / REASON cannot be blank') 
            return HttpResponseRedirect(reverse('srf'))
        else:
            frequests = frequest(code=codenumber, type='SRF', description=desc, employee_id=employeeid, department_id=departselect )
            frequests.save()
            messages.success(request, codenumber + ' submitted..') 

            emailSend = emailSendWhenSubmit('Service Request Forms (SRF)', departselect, codenumber)

            return HttpResponseRedirect(reverse('srf'))
    except Exception:
        messages.error(request, 'Failed to submit') 
        return HttpResponseRedirect(reverse('srf')) 

@login_required
def srfview(request, id, action):
    employee_user = employee.objects.get(user_id=request.user.id)
    frequests = frequest.objects.get(id=id)
    srfdetails = frequestdetail.objects.filter(frequest_id=id).last()
    employees = employee.objects.get(id=frequests.employee_id) 
    approvalfrhistorys = approvalfrhistory.objects.filter(frequest_id=frequests.id)
    isapprover = get_isapprover(employee_user.id, frequests.id, frequests.department_id)
    isapprover_mis = get_isapprover_mis(employee_user.id)
    approver_wizard = get_approver_frequest_depthead_wizard(frequests.id, frequests.department_id)
    
    isapproved_mis = get_isapproved_frequest_misdept_wizard(frequests.id)
    
    isdelayed = True
    for approvalfrhistory_records in approvalfrhistorys:
        isdelayed = False   

    approver_department = frequests.department_id
    
    if isapprover_mis :
        department_mis = department.objects.get(isapprover=True)
        approver_department = department_mis.id

    if action == 2000 :
        approvalfrhistorys = approvalfrhistory(frequest_id=id, employee_id=employee_user.id, status='ACCEPTED', department_id=approver_department)
        approvalfrhistorys.save()

        if isapprover_mis :
            frequests.status = 'FINISHED'
        else:
            frequests.status = 'APPROVE'

        frequests.save()
    elif action == 3000 :
        approvalfrhistorys = approvalfrhistory(frequest_id=id, employee_id=employee_user.id, status='REJECTED', department_id=approver_department)
        approvalfrhistorys.save()
        frequests.status = 'REJECTED'
        frequests.save()

    if (isapprover_mis == False) and (action > 1000): 
        sendEmail = sendEmailWhenApproveDeptHead(frequests.code, frequests.status)
        return HttpResponseRedirect('/srfview/' + str(id) + '/1000' )

    return render(request, 'helpdesk/srfview.html', 
        {'employee_user':employee_user,'employees': employees,'frequests':frequests, 
        'isapprover':isapprover,'approvalfrhistorys':approvalfrhistorys,
        'approver_wizard':approver_wizard,
        'isapproved_mis':isapproved_mis,'isapprover_mis':isapprover_mis,
        'isdelayed':isdelayed,'srfdetails':srfdetails})

def submitsrfdetail(request):
    if request.method == 'POST':
        pfrequest_id = request.POST['frequest_id']   
        puser_id = request.POST['user_id']   
        type = request.POST['type']   
        pstartdate = request.POST['startdate']   
        pstarttime = request.POST['starttime']   
        sn = request.POST['sn']   
        pfinishdate = request.POST['finishdate']   
        pfinishtime = request.POST['finishtime']   
        phardware = listToString(request.POST.getlist('hardware'))
        psoftware = listToString(request.POST.getlist('software'))
        action_taken = request.POST['action_taken']   
        #engineerid = request.POST['engineername']   

        employee_user = employee.objects.get(user_id=puser_id)

        isexist_srfdetail = frequestdetail.objects.filter(frequest_id=pfrequest_id).last()

        if isexist_srfdetail is not None:
            isexist_srfdetail.type = type
            isexist_srfdetail.sn = sn
            isexist_srfdetail.startdate = pstartdate
            isexist_srfdetail.starttime = pstarttime
            isexist_srfdetail.finishdate = pfinishdate
            isexist_srfdetail.finishtime = pfinishtime
            isexist_srfdetail.hardware = phardware
            isexist_srfdetail.description = action_taken
            isexist_srfdetail.save()
        else:
            srfdetails = frequestdetail(frequest_id=pfrequest_id, employee_id=employee_user.id,type=type, sn=sn, startdate=pstartdate,starttime=pstarttime,finishdate=pfinishdate, finishtime=pfinishtime,hardware=phardware,software=psoftware,description=action_taken)
            srfdetails.save()

            department_mis = department.objects.get(isapprover=True)
            approver_department = department_mis.id

            approvalfrhistorys = approvalfrhistory(frequest_id=pfrequest_id, employee_id=employee_user.id, status="ACCEPTED", department_id=approver_department)
            approvalfrhistorys.save()

            frequests = frequest.objects.get(id=pfrequest_id)
            frequests.status = 'FINISHED'
            frequests.save()

    return HttpResponseRedirect('/srfview/' + str(pfrequest_id) + '/1000' )

@login_required(login_url='/loginPage')
def prf(request):
    lastcode = get_last_number('PRF') 

    employees = employee.objects.get(user_id=request.user.id) 
    items = item.objects.all().filter(item_type="Peripheral").order_by('item_name') 
    return render(request, 'helpdesk/prf.html', {'employees': employees, 'items' : items, 'lastcode':lastcode })

@login_required(login_url='/loginPage')
def prfview(request, id, action):
    employee_user = employee.objects.get(user_id=request.user.id)
    frequests = frequest.objects.get(id=id)
    srfdetails = frequestdetail.objects.filter(frequest_id=id).last()
    employees = employee.objects.get(id=frequests.employee_id) 
    approvalfrhistorys = approvalfrhistory.objects.filter(frequest_id=frequests.id)
    isapprover = get_isapprover(employee_user.id, frequests.id, frequests.department_id)
    isapprover_mis = get_isapprover_mis(employee_user.id)
    approver_wizard = get_approver_frequest_depthead_wizard(frequests.id, frequests.department_id)

    position_approver_level2 = position.objects.filter(isapprover_last=True).last()
    approver_wizard_level2 = get_approver_frequest_genmgr_wizard(frequests.id, position_approver_level2.id)
    
    isapproved_mis = get_isapproved_frequest_misdept_wizard(frequests.id)
    
    isdelayed = True
    for approvalfrhistory_records in approvalfrhistorys:
        isdelayed = False   

    approver_department = frequests.department_id
    
    if isapprover_mis :
        department_mis = department.objects.get(isapprover=True)
        approver_department = department_mis.id

    if action == 2000 :
        approvalfrhistorys = approvalfrhistory(frequest_id=id, employee_id=employee_user.id, status='ACCEPTED', department_id=approver_department)
        approvalfrhistorys.save()

        if isapprover_mis :
            frequests.status = 'FINISHED'
        else:
            frequests.status = 'APPROVE'

        frequests.save()
    elif action == 3000 :
        approvalfrhistorys = approvalfrhistory(frequest_id=id, employee_id=employee_user.id, status='REJECTED', department_id=approver_department)
        approvalfrhistorys.save()
        frequests.status = 'REJECTED'
        frequests.save()

    if (isapprover_mis == False) and (action > 1000): 
        sendEmail = sendEmailWhenApproveDeptHead(frequests.code, frequests.status)
        return HttpResponseRedirect('/prfview/' + str(id) + '/1000' )


    return render(request, 'helpdesk/prfview.html', 
        {'employee_user':employee_user,'employees': employees,'frequests':frequests, 
        'isapprover':isapprover,'approvalfrhistorys':approvalfrhistorys,
        'approver_wizard':approver_wizard,'approver_wizard_level2':approver_wizard_level2,
        'isapproved_mis':isapproved_mis,'isapprover_mis':isapprover_mis,
        'isdelayed':isdelayed,'srfdetails':srfdetails})

def submitprfdetail(request):
    if request.method == 'POST':
        pfrequest_id = request.POST['frequest_id']   
        puser_id = request.POST['user_id']   
        approval = request.POST['approval']   
        inbudget = request.POST['inbudget']   
        nominal = request.POST['nominal']   
        notes = request.POST['notes']   
     
        employee_user = employee.objects.get(user_id=puser_id)
        isexist_prfdetail = frequestdetail.objects.filter(frequest_id=pfrequest_id).last()
    
        department_mis = department.objects.get(isapprover=True)
        approver_department = department_mis.id

        if isexist_prfdetail is not None:
            isexist_prfdetail.prf_accepted = approval
            isexist_prfdetail.prf_inbudget = inbudget
            isexist_prfdetail.prf_underfive = nominal
            isexist_prfdetail.prf_notes = notes
   
            isexist_prfdetail.save()
        else:
            prfdetails = frequestdetail(frequest_id=pfrequest_id, employee_id=employee_user.id,prf_accepted=approval, prf_inbudget=inbudget, prf_underfive=nominal,prf_notes=notes)
            prfdetails.save()

            approvalfrhistorys = approvalfrhistory(frequest_id=pfrequest_id, employee_id=employee_user.id, status=approval, department_id=approver_department)
            approvalfrhistorys.save()

            frequests=frequest.objects.get(id=pfrequest_id)
            frequests.status = 'FINISHED'
            frequests.save()

    return HttpResponseRedirect('/prfview/' + str(pfrequest_id) + '/1000' )

def submitprf(request):
    try:
        employeeid = request.POST['employee_id']
        codenumber = request.POST['codenumber']
        desc = request.POST['desc']
        itemcode = request.POST['itemcode']
        departselect = request.POST['departselect']

        if codenumber == '':
            messages.error(request, 'PRF number cannot be blank') 
            return HttpResponseRedirect(reverse('prf'))
        elif itemcode == '':
            messages.error(request, 'Item should be choosen') 
            return HttpResponseRedirect(reverse('prf'))
        elif desc == '':
            messages.error(request, 'FAULT DESCRIPTION / REASON cannot be blank') 
            return HttpResponseRedirect(reverse('prf'))
        else:
            frequests = frequest(code=codenumber, type='PRF', description=desc, employee_id=employeeid, item_id=itemcode, department_id=departselect)
            frequests.save()
            messages.success(request, codenumber + ' submitted..') 
            
            emailSend = emailSendWhenSubmit('Peripheral Request Forms (PRF)', departselect, codenumber)
            return HttpResponseRedirect(reverse('prf'))
    except Exception:
        messages.error(request, 'Failed to submit') 
        return HttpResponseRedirect(reverse('prf')) 

@login_required(login_url='/loginPage')
def cash(request):
    lastcode = get_last_number_cash(int(datetime.now().year))
    departments = department.objects.all().order_by('costcentre')

    datetoday = datetime.now().strftime('%Y-%m-%d')
    employees = employee.objects.get(user_id=request.user.id) 
    return render(request, 'helpdesk/cash.html', {'employees': employees, 'datetoday': datetoday, 'lastcode':lastcode, 'departments':departments  })

def submitcash(request):

    if request.method == "POST" : 
        employees = employee.objects.get(user_id=request.user.id)
        deptuser = request.POST['departselect']
        dept_id = request.POST['costcenter']
        prequestor = request.POST['requestor']
        pproposaldate = request.POST['porposaldate']
        advanceno = request.POST['advance_no']
        pamount = request.POST['amount']
        pneedate = request.POST['needdate']
        ppurpose = request.POST['purpose']

     
        pamount = pamount.replace(".", "")
        pamount = pamount.replace(",", ".")
        
        if prequestor == '' :
            messages.error(request,'Requestor cannot be blank..')
        elif pamount == '' : 
            messages.error(request,'Amount of the request cannot be zero..')
        elif pneedate == '':
            messages.error(request,'Need date of the request cannot be blank..')
        elif  ppurpose == '' :
            messages.error(request,'Purpose of the request cannot be blank..')
        else : 
            try:   
                settledate=datetime.strptime(pneedate, '%Y-%m-%d') + timedelta(days=14)

                requestor_employe=employee.objects.get(id=prequestor) 
                departments=department.objects.get(id=dept_id)

                crequests = crequest(code=advanceno,employee_id=employees.id,deptuser_id=deptuser,requestorid_id=requestor_employe.id,requestor=requestor_employe.name,department_id=departments.id,costcentre=departments.name,proposaldate=pproposaldate,proposalyear=datetime.now().year, amount=pamount,needdate=pneedate,purpose=ppurpose,status='DELAYED',est_settle=settledate)

                crequests.save()
                messages.success(request, advanceno + ' Submitted'  )

                emailSend = emailSendWhenSubmitCash('Form Cash Advance - ' + advanceno , departments.id ,advanceno) 
            except Exception:
                messages.error(request, 'failed submit')
        
        return HttpResponseRedirect(reverse('cash')) 
         
@login_required(login_url='/loginPage')
def listcash(request):
    employees = employee.objects.get(user_id=request.user.id) 
    empldept = employee.objects.all().filter(user_id=request.user.id, departments__in=department.objects.all()).select_related('department').values_list('departments',flat=True)
    
    iscashapproverDeptHead =checkIsCashApproverDeptHead(employees.id)
    iscashapproverFinManager =checkIsCashApproverFinManager(employees.id)
    iscashapproverAPFinance =checkIsCashApproverAPFinance(employees.id)
    
    fldate1_value = ''
    fldate2_value = ''
    if request.method == 'POST':
        idrequestDelete = request.POST['idrequest']
        fldate1_value = request.POST['fldate1']
        fldate2_value = request.POST['fldate2'] 

        if fldate1_value == '' and fldate2_value == '' :
            fldate1_value = '1999-01-01'
            fldate2_value = '9999-12-31'

        fldate1 = fldate1_value
        fldate2 = fldate2_value

        if idrequestDelete != '0':
            crequestDelete = crequest.objects.filter(pk=idrequestDelete)
            crequestDelete.delete()

    listIDCashCanBeApproved = []
    if iscashapproverFinManager : 
        searchIDList=crequest.objects.filter(status__in=['DELAYED','APPROVE'])
        
        listcashID = []
        for cashlist in searchIDList:
            isInclude = True
            countApproval = 0

            approvals = approvalcrhistory.objects.filter(crequest_id=cashlist.id)
            for historyApproval in approvals:
                countApproval = countApproval + 1
                
                if historyApproval.employee_id == employees.id :
                    isInclude = False

            if isInclude and countApproval == 1 :
                listcashID.append(cashlist.id)
        
        searchIDListForOwn = crequest.objects.all().filter(Q(requestorid_id=employees.id) | Q(employee_id=employees.id), status__in=['DELAYED','APPROVE']).order_by('-id')

        for cashlist in searchIDListForOwn:
            listcashID.append(cashlist.id)

        if request.method == 'POST':
            crequests = crequest.objects.all().filter(id__in=listcashID,proposaldate__range=[fldate1, fldate2]).order_by('-id')
        else:
            crequests = crequest.objects.all().filter(id__in=listcashID).order_by('-id')

        for crequestsList in crequests: 
            approvalcrhistorys_count = approvalcrhistory.objects.filter(crequest_id=crequestsList.id).count()
            if approvalcrhistorys_count == 1:
                listIDCashCanBeApproved.append(crequestsList.id)

    elif iscashapproverAPFinance:
        searchIDList=crequest.objects.filter(status__in=['DELAYED','APPROVE'])
        
        listcashID = []
        for cashlist in searchIDList:
            isInclude = True
            countApproval = 0

            approvals = approvalcrhistory.objects.filter(crequest_id=cashlist.id)

            for historyApproval in approvals:
                countApproval = countApproval + 1
                
                if historyApproval.employee_id == employees.id :
                    isInclude = False

            if isInclude and countApproval == 2 :
                listcashID.append(cashlist.id)
        
        searchIDListForOwn = crequest.objects.all().filter(Q(requestorid_id=employees.id) | Q(employee_id=employees.id), status__in=['DELAYED','APPROVE']).order_by('-id')

        for cashlist in searchIDListForOwn:
            listcashID.append(cashlist.id)
            
        if request.method == 'POST':
            fldate1 = request.POST['fldate1']
            fldate2 = request.POST['fldate2'] 
            crequests = crequest.objects.all().filter(id__in=listcashID,proposaldate__range=[fldate1, fldate2]).order_by('-id')
        else:
            crequests = crequest.objects.all().filter(id__in=listcashID).order_by('-id')

        for crequestsList in crequests: 
            approvalcrhistorys_count = approvalcrhistory.objects.filter(crequest_id=crequestsList.id).count()
            if approvalcrhistorys_count == 2:
                listIDCashCanBeApproved.append(crequestsList.id)
    elif iscashapproverDeptHead :
        deptList = getDeptList(employees.id)

        if request.method == 'POST':
            crequests = crequest.objects.all().filter(department_id__in=deptList, status__in=['DELAYED','APPROVE'],proposaldate__range=[fldate1, fldate2]).order_by('-id')
        else:
            crequests = crequest.objects.all().filter(department_id__in=deptList, status__in=['DELAYED','APPROVE']).order_by('-id')

        for crequestsList in crequests: 
            iscashapproverDeptHeadAtThisID =checkIsCashApproverDeptHeadByID(employees.id, crequestsList.department_id)

            if iscashapproverDeptHeadAtThisID and crequestsList.status == 'DELAYED' :
                listIDCashCanBeApproved.append(crequestsList.id)
    else:
        if request.method == 'POST':
            crequests = crequest.objects.all().filter(Q(requestorid_id=employees.id) | Q(employee_id=employees.id), status__in=['DELAYED','APPROVE'],proposaldate__range=[fldate1, fldate2]).order_by('-id')
        else:
            crequests = crequest.objects.all().filter(Q(requestorid_id=employees.id) | Q(employee_id=employees.id), status__in=['DELAYED','APPROVE']).order_by('-id')

    canDeleteListID = []
    for req in crequests:
        if req.employee.id == employees.id and req.status == 'DELAYED' :
            canDeleteListID.append(req.id)    

    if fldate1_value == '1999-01-01' :
        fldate1_value = ''
    if fldate2_value == '9999-12-31':
        fldate2_value = ''  


    return render(request, 'helpdesk/listcash.html', {'crequests':crequests, 'empldept':empldept,'listIDCashCanBeApproved':listIDCashCanBeApproved,'iscashapproverAPFinance':iscashapproverAPFinance,'fldate1_value':fldate1_value,'fldate2_value':fldate2_value,'canDeleteListID':canDeleteListID})

@login_required(login_url='/loginPage')
def historycash(request):
    employees = employee.objects.get(user_id=request.user.id) 
    empldept = employee.objects.all().filter(user_id=request.user.id, departments__in=department.objects.all()).select_related('department').values_list('departments',flat=True)
    
    iscashapproverDeptHead =checkIsCashApproverDeptHead(employees.id)
    iscashapproverFinManager =checkIsCashApproverFinManager(employees.id)
    iscashapproverAPFinance =checkIsCashApproverAPFinance(employees.id)

    fldate1_value = ''
    fldate2_value = ''
    if request.method == 'POST':
        fldate1_value = request.POST['fldate1']
        fldate2_value = request.POST['fldate2'] 

        if fldate1_value == '' and fldate2_value == '' :
            fldate1_value = '1999-01-01'
            fldate2_value = '9999-12-31'

        fldate1 = fldate1_value
        fldate2 = fldate2_value

    statusAllowed=['REJECTED','TRANSFERRED']
    if iscashapproverFinManager : 
        if request.method == 'POST':
            crequests = crequest.objects.all().filter(status__in=statusAllowed,proposaldate__range=[fldate1, fldate2]).order_by('-id')
        else:
            crequests = crequest.objects.all().filter(status__in=statusAllowed).order_by('-id')
    elif iscashapproverAPFinance:
        if request.method == 'POST':
            crequests = crequest.objects.all().filter(status__in=statusAllowed,proposaldate__range=[fldate1, fldate2]).order_by('-id')
            crequests = crequest.objects.all().filter(status__in=statusAllowed).order_by('-id')
        else:      
            crequests = crequest.objects.all().filter(status__in=statusAllowed).order_by('-id')
    elif iscashapproverDeptHead :
        deptList = getDeptList(employees.id)

        if request.method == 'POST':
            crequests = crequest.objects.all().filter(department_id__in=deptList, status__in=statusAllowed,proposaldate__range=[fldate1, fldate2]).order_by('-id')
        else:
            crequests = crequest.objects.all().filter(department_id__in=deptList, status__in=statusAllowed).order_by('-id')
    else:
        if request.method == 'POST':
            crequests = crequest.objects.all().filter(Q(requestorid_id=employees.id) | Q(employee_id=employees.id), status__in=statusAllowed, proposaldate__range=[fldate1, fldate2]).order_by('-id')
        else: 
            crequests = crequest.objects.all().filter(Q(requestorid_id=employees.id) | Q(employee_id=employees.id), status__in=statusAllowed).order_by('-id')

    if fldate1_value == '1999-01-01' :
        fldate1_value = ''
    if fldate2_value == '9999-12-31':
        fldate2_value = ''  

    return render(request, 'helpdesk/historycash.html', {'crequests':crequests, 'empldept':empldept,'fldate1_value':fldate1_value, 'fldate2_value':fldate2_value})

@login_required(login_url='/loginPage')
def cashview(request,id,action): 
    employees = employee.objects.get(user_id=request.user.id)
    crequests = crequest.objects.get(id=id)

    approvalcrhistorys = approvalcrhistory.objects.filter(crequest_id=crequests.id)

    isdelayed = True
    for app in approvalcrhistorys: 
        isdelayed = False   

    iscashapprover = get_iscashapprover(employees.id, crequests.id, crequests.department_id) 

    iscashapproverAPFinance =checkIsCashApproverAPFinance(employees.id)

    if action == 2000 :
        approvalcrhistorysupd = approvalcrhistory(crequest_id=id, employee_id=employees.id, status='ACCEPTED', department_id=crequests.department_id)
        approvalcrhistorysupd.save()

        crequests.status = 'APPROVE'
        if iscashapproverAPFinance : 
            crequests.status = 'TRANSFERRED'

        crequests.save()
        return HttpResponseRedirect('/cashview/' + str(id) + '/1000' )
    elif action == 3000 :
        approvalcrhistorysupd = approvalcrhistory(crequest_id=id, employee_id=employees.id, status='REJECTED', department_id=crequests.department_id)
        approvalcrhistorysupd.save()
        crequests.status = 'REJECTED'
        crequests.save()
        return HttpResponseRedirect('/cashview/' + str(id) + '/1000' )

    #LOGIC WIZARD
    empWizard = employee.objects.filter(departments =  crequests.department_id)
    approverName = []
    approverStatus = []
    for emp in empWizard:
        if emp.position.isapprover :
            approverName.append(emp.name)

    getcashapprovers=cashapprover.objects.all()
    for getcashapprover in getcashapprovers :
        if getcashapprover.approverorder == 1 : 
            approverName.append(getcashapprover.approver.name)
        elif getcashapprover.approverorder == 2 :
            approverName.append(getcashapprover.approver.name)
    
    getStatusWizardcount = approvalcrhistory.objects.filter(crequest_id=id).count()
    for x in range(getStatusWizardcount):
        approverStatus.append('done')


    return render(request, 'helpdesk/cashview.html',{'crequests':crequests,'employees':employees,'iscashapprover':iscashapprover,'approvalcrhistorys':approvalcrhistorys,'isdelayed':isdelayed,'approverName':approverName,'approverStatus':approverStatus,'iscashapproverAPFinance':iscashapproverAPFinance})

@login_required(login_url='/loginPage')
def cashApprovalAtList(request,id,action) : 
    employees = employee.objects.get(user_id=request.user.id)
    crequests = crequest.objects.get(id=id)

    countapproval = approvalcrhistory.objects.filter(crequest_id=id).count()

    if action == 2000 :
        try:
            approvalcrhistorysupd = approvalcrhistory(crequest_id=id, employee_id=employees.id, status='ACCEPTED', department_id=crequests.department_id)
            approvalcrhistorysupd.save()

            crequests.status = 'APPROVE'
            iscashapproverAPFinance =checkIsCashApproverAPFinance(employees.id)
            if iscashapproverAPFinance : 
                crequests.status = 'TRANSFERRED'

            crequests.save()
            messages.success(request, crequests.code + ' already approved..')
        except Exception:
            messages.error(request, 'There is an error when submitting, please try again') 
    elif action == 3000 :
        try:
            approvalcrhistorysupd = approvalcrhistory(crequest_id=id, employee_id=employees.id, status='REJECTED', department_id=crequests.department_id)
            approvalcrhistorysupd.save()
            crequests.status = 'REJECTED'
            crequests.save()
            messages.success(request, crequests.code + ' already rejected..')
        except Exception:
            messages.error(request, 'There is an error when submitting, please try again') 

    sendEmail = sendEmailCashWhenApproveApprovalLevel(crequests.code, countapproval + 1)

    return HttpResponseRedirect('/listcash')

def cashapproveemailLevel(request, codenumber, empid, departid, action, countapproval):
    frequests = crequest.objects.get(code=codenumber)
    checkApproval = approvalcrhistory.objects.filter(crequest_id=frequests.id).count()
    statusInfo = ''

    #countapproval=0 DEPT HEAD
    #countapproval=1 AP FINANCE
    #countapproval=2 FINANCE MANAGER
    if checkApproval == countapproval: 
        if action == 2000 :
            approvalfrhistorys = approvalcrhistory(crequest_id=frequests.id, employee_id=empid, status='ACCEPTED', department_id=departid)
            approvalfrhistorys.save()
            
            statusInfo = 'Approved'
            if countapproval == 2 :
                frequests.status = 'TRANSFERRED'
            else:
                frequests.status = 'APPROVE'
            frequests.save()
        elif action == 3000 :
            approvalfrhistorys = approvalcrhistory(crequest_id=frequests.id, employee_id=empid, status='REJECTED', department_id=departid)
            approvalfrhistorys.save()

            statusInfo = 'Rejected'
            frequests.status = 'REJECTED'
            frequests.save()  
        
        sendEmail = sendEmailCashWhenApproveApprovalLevel(codenumber, countapproval + 1)
    return render(request, 'helpdesk/windowautoclose.html')
  

@login_required(login_url='/loginPage')
def listrequest(request):
    employees = employee.objects.get(user_id=request.user.id) 
    empldept = employee.objects.all().filter(user_id=request.user.id, departments__in=department.objects.all()).select_related('department').values_list('departments',flat=True)

    #print(empldept.__dict__)
    fldate1_value = ''
    fldate2_value = ''
    if request.method == 'POST':
        idrequestDelete = request.POST['idrequest']
        fldate1_value = request.POST['fldate1']
        fldate2_value = request.POST['fldate2'] 

        if fldate1_value == '' and fldate2_value == '' :
            fldate1_value = '1999-01-01'
            fldate2_value = '9999-12-31'

        fldate1 = fldate1_value
        fldate2 = fldate2_value

        if idrequestDelete != '0':
            frequestDelete = frequest.objects.filter(pk=idrequestDelete)
            frequestDelete.delete()

    departid = []
    for dpt in empldept:
        departid.append(dpt)
    
    if employees.position.isapprover_last :
        if request.method == 'POST':
            frequests = frequest.objects.all().filter(status='APPROVE', type='PRF', submitted__range=[fldate1, fldate2]).order_by('-id')
        else:
            frequests = frequest.objects.all().filter(status='APPROVE', type='PRF').order_by('-id')
    else: 
        isapprover_mis = get_isapprover_mis(employees.id)

        if isapprover_mis == True :
            departid = []
            departid = range(50)

        if request.method == 'POST':
            frequests = frequest.objects.all().filter(status__in=['DELAYED','APPROVE'], department_id__in=departid, submitted__range=[fldate1, fldate2]).order_by('-id')
        else:
            frequests = frequest.objects.all().filter(status__in=['DELAYED','APPROVE'], department_id__in=departid).order_by('-id')

    canDeleteListID = []
    for req in frequests:
        if req.employee.id == employees.id and req.status == 'DELAYED' :
            canDeleteListID.append(req.id)    

    if fldate1_value == '1999-01-01' :
        fldate1_value = ''
    if fldate2_value == '9999-12-31':
        fldate2_value = ''   

    return render(request, 'helpdesk/listrequest.html', {'frequests':frequests, 'empldept':empldept,'fldate1_value':fldate1_value, 'fldate2_value':fldate2_value,'canDeleteListID':canDeleteListID})

@login_required(login_url='/loginPage')
def requestreport(request):
    employees = employee.objects.get(user_id=request.user.id) 
    empldept = employee.objects.all().filter(user_id=request.user.id, departments__in=department.objects.all()).select_related('department').values_list('departments',flat=True)

    fldate1_value = ''
    fldate2_value = ''
 
    if request.method == 'POST':
        fldate1_value = request.POST['fldate1']
        fldate2_value = request.POST['fldate2'] 

        if fldate1_value == '' and fldate2_value == '' :
            fldate1_value = '1999-01-01'
            fldate2_value = '9999-12-31'

        fldate1 = fldate1_value
        fldate2 = fldate2_value

        frequests = frequest.objects.all().filter(status='FINISHED', submitted__range=[fldate1, fldate2]).order_by('-id')
    else:
        frequests = frequest.objects.all().filter(status='FINISHED').order_by('-id')

    if fldate1_value == '1999-01-01' :
        fldate1_value = ''
    if fldate2_value == '9999-12-31':
        fldate2_value = ''  

    return render(request, 'helpdesk/requestreport.html', {'frequests':frequests,'fldate1_value':fldate1_value, 'fldate2_value':fldate2_value})


@login_required(login_url='/loginPage')
def historyrequest(request):
    employees = employee.objects.get(user_id=request.user.id) 
    empldept = employee.objects.all().filter(user_id=request.user.id, departments__in=department.objects.all()).select_related('department').values_list('departments',flat=True)

    #print(empldept.__dict__)
    departid = []
    for dpt in empldept:
        departid.append(dpt)

    fldate1_value = ''
    fldate2_value = ''
    if request.method == 'POST':
        fldate1_value = request.POST['fldate1']
        fldate2_value = request.POST['fldate2'] 

        if fldate1_value == '' and fldate2_value == '' :
            fldate1_value = '1999-01-01'
            fldate2_value = '9999-12-31'

        fldate1 = fldate1_value
        fldate2 = fldate2_value

    if employees.position.isapprover_last :
        if request.method == 'POST':
            frequests = frequest.objects.all().filter(status__in=['FINISHED','REJECTED'], type='PRF', submitted__range=[fldate1, fldate2]).order_by('-id')
        else:
            frequests = frequest.objects.all().filter(status__in=['FINISHED','REJECTED'], type='PRF').order_by('-id')
    else: 
        isapprover_mis = get_isapprover_mis(employees.id)

        if isapprover_mis == True :
            departid = []
            departid = range(50)

        if request.method == 'POST':
            fldate1 = request.POST['fldate1']
            fldate2 = request.POST['fldate2'] 
            frequests = frequest.objects.all().filter(status__in=['FINISHED','REJECTED'], department_id__in=departid, submitted__range=[fldate1, fldate2]).order_by('-id')
        else:
            frequests = frequest.objects.all().filter(status__in=['FINISHED','REJECTED'], department_id__in=departid).order_by('-id')

    if fldate1_value == '1999-01-01' :
        fldate1_value = ''
    if fldate2_value == '9999-12-31':
        fldate2_value = ''  


    return render(request, 'helpdesk/historyrequest.html', {'frequests':frequests, 'empldept':empldept,'fldate1_value':fldate1_value, 'fldate2_value':fldate2_value})

@login_required(login_url='/loginPage')
def dthistcashadv(request):
    return render(request, 'helpdesk/dthistcashadv.html')

def loginPage(request):
    return render(request, 'helpdesk/login.html')

def loginAuth(request):
    if request.method == 'POST':
        reqUsername = request.POST['username']
        reqPassword = request.POST['password']
        user = authenticate(request, username=reqUsername, password=reqPassword)

        try:
            checkuser= User.objects.get(username=reqUsername)
        except User.DoesNotExist:
            messages.error(request, 'User is not exist.') 
            return HttpResponseRedirect(reverse('loginPage'))
        else:
            if checkuser.is_active == True :
                if user is not None :
                    login(request, user)
                    AllLogin.objects.create(user= request.user)
                    return redirect('index')
                else:
                    messages.error(request, 'Username/password is incorect') 
                    return HttpResponseRedirect(reverse('loginPage')) 
            else:
                messages.error(request, 'User is not active.') 
                return HttpResponseRedirect(reverse('loginPage'))
    else:
        return HttpResponseRedirect(reverse('loginPage'))

def logoutPage(request):
    logout(request)
    return render(request, 'helpdesk/login.html')

@login_required
def userProfile(request):
    employees = employee.objects.get(user_id=request.user.id) 

    crfByEmployeeIDCount=frequest.objects.filter(employee_id=employees.id, type='CRF').count()
    srfByEmployeeIDCount=frequest.objects.filter(employee_id=employees.id, type='SRF').count()
    prfByEmployeeIDCount=frequest.objects.filter(employee_id=employees.id, type='PRF').count()
    cashAdvanceByEmployeeIDCount=crequest.objects.filter(Q(employee_id=employees.id)|Q(requestorid_id=employees.id)).count()

    AllLogins = AllLogin.objects.all().filter(user_id=request.user.id).order_by('-id')[:10]
    return render(request, 'helpdesk/userProfile.html',{'employees':employees,'crfByEmployeeIDCount':crfByEmployeeIDCount,'srfByEmployeeIDCount':srfByEmployeeIDCount,'prfByEmployeeIDCount':prfByEmployeeIDCount,'cashAdvanceByEmployeeIDCount':cashAdvanceByEmployeeIDCount, 'AllLogins':AllLogins})

 
def independen(request):
    departmentsdata = department.objects.all()
    check= testlogic('202200028')
    #get_cashapprover_APFin(1)
    return render(request, 'helpdesk/independen.html', {'departmentsdata':departmentsdata})


def changepassword(request):
    users = User.objects.get(id=request.user.id)
    if request.method == "POST":
        reqUsername = request.POST['username']
        reqPassword = request.POST['password']

        try:
            u = User.objects.get(username=reqUsername)
            u.set_password(reqPassword)
            u.save()

            messages.success(request, 'Your password already changed. Plase login again')
            logout(request)
            return render(request, 'helpdesk/login.html')
        except Exception:
            messages.error(request, 'Password failed to be changed ')
    return render(request, 'helpdesk/changepassword.html',{'users':users})

def resetPassword(request):
    users = ''
    if request.method == "POST":
        reqEmail = request.POST['email']

        try:
            employees = employee.objects.get(email=reqEmail)
        except employee.DoesNotExist:
            messages.error(request, 'Email not register')
        else:
            users = User.objects.get(id=employees.user_id)
            newPassword = users.username + datetime.now().strftime("%H%M%S")

            users.set_password(newPassword)
            users.save()

            #email to approver 1
            subjectEmail = "Reset Password"
            subject, from_email, to = subjectEmail, 'admin@example.com', employees.email
            text_content = 'This is an important message.'
        
            html_content = '<div style="text-align:center;">' + '<h2>Your Password Has Been Reset</h2><br>' + '<p>Username: ' + users.username + '</p>' + '<p>Password: ' + newPassword + '</p>'  + '<br><br><br>' + '<small><p>PT. Sinar Meadow International Indonesia</p>' + '<p>Kawasan Industri Pulogadung Blok III.S.20-23 No.3, Jalan Puloayang 2, RW.9, Jatinegara</p>' + '<p>Cakung, Kota Jakarta Timur</p>' + '<p>Daerah Khusus Ibukota Jakarta 13260</p>' + '</div>' 
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            msg.attach_alternative(html_content, "text/html")
            msg.send()

            messages.success(request, 'The new passowrd has been sent to your email. Please check')

    return render(request, 'helpdesk/resetPassword.html', {'users':users})
