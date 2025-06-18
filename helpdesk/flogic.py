from datetime import datetime, timedelta
from .models import crequest, department, employee, frequest, item, approvalfrhistory,frequestdetail,position,approvalcrhistory, cashapprover, logemail, emailsent
from django.db.models import Q
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.core import mail
from django.conf import settings
from scheduler.models import emailschedule
#import traceback

webhost = 'https://emgmt.sinarmeadow.com/'
'''
1. HELPDESK REQUEST

2. CASH REQUEST
   - User submit cash request maka email akan dikirimkan ke Departement Head dari requestor ID (emailSendWhenSubmitCash)
   - selanjutnya jika Dept Head Approve maka email akan di kirim ke cash approver : (sendEmailCashWhenApproveApprovalLevel) 
     - pertama kepada Finance Manager (Approver 1 dan backup)
     - kedua ke Staf AP (Approver 1 dan backup)
     - Terakhir setelah staff AP approve maka akan kirim email ke requestor (sendEmailCashWhenApproveApprovalLevel countapproval 3)
'''

def createScheduleEmail(param_Body, param_Subject, param_fromEmail, param_sendToEmail, param_codelink, param_status='INITIAL'):
    emailschedules = emailschedule(messageBody=param_Body, messageSubject=param_Subject, fromEmail=param_fromEmail, sendToEmail= param_sendToEmail, codelink=param_codelink, status=param_status)
    emailschedules.save()

    return True
    

def get_email_allMIS(inputParam):
    emailMIS = [] 
    empldept = employee.objects.all().filter(departments__in=department.objects.all().filter(isapprover=inputParam))

    for empl in empldept : 
        emailMIS.append(empl.email)

    return emailMIS


#MENCARI NOMOR TERAKHIR
def get_last_number(inptype):
    lastnbr = frequest.objects.filter(type=inptype, submitted=datetime.now()).order_by('id').last()
    
    sendlastnbr = ''
    if lastnbr is not None:
        sendlastnbr = lastnbr.code    
        prefix = (sendlastnbr[0:14])
        suffix = str(int(sendlastnbr[13:17]) + 1).zfill(2)
    else :
        prefix = inptype + '-' + str(datetime.now().year) + str(datetime.now().strftime('%m')) + str(datetime.now().strftime('%d'))  + '-'  
        suffix = '001'
    return prefix + suffix

#MENCARI ROLE APPROVAL USER
def get_isapprover(input_employeeid, input_frequest_id, input_frequest_department, input_frequest_price):

    employees = employee.objects.filter(id=input_employeeid)
    
    isapprover = False    
    for emp in employees : 

        for depart in emp.departments.all():
            #APPROVER 1 DEPT HEAD
            if (depart.id == int(input_frequest_department)) and  emp.position.isapprover :
                approvalfrhistorys = approvalfrhistory.objects.filter(frequest_id=input_frequest_id, employee_id = emp.id).last()
                if approvalfrhistorys is not None:
                    isapprover = False
                else:
                    isapprover = True
                    
            #APPROVER 2 GENERAL MANAGER
            elif emp.position.isapprover_last :
                if input_frequest_price  > 4999999 : 
                    approvalfrhistorys = approvalfrhistory.objects.filter(frequest_id=input_frequest_id, status='ACCEPTED').last()
                    if approvalfrhistorys is not None and approvalfrhistorys.employee_id != emp.id:
                        isapprover = True
                    else:
                        isapprover = False 
                else: 
                    isapprover = False 

            #APPROVER MIS
            elif depart.isapprover :
                approvalfrhistorys_appr1 = approvalfrhistory.objects.filter(frequest_id=input_frequest_id, department_id=input_frequest_department).last()
                if approvalfrhistorys_appr1 is not None and approvalfrhistorys_appr1.status != 'REJECTED':
                    approvalfrhistorys_appr2 = approvalfrhistory.objects.filter(frequest_id=input_frequest_id, department_id=depart.id).last()
                    if approvalfrhistorys_appr2 is None:
                        isapprover = True

  
    return isapprover

def get_isapprover_head(input_employeeid, input_frequest_id, input_frequest_department):
    getRequestorID = frequest.objects.get(pk=input_frequest_id)

    employeeid = employee.objects.filter(pk = getRequestorID.employee.id).last()
    employees = employee.objects.filter(pk = employeeid.head_id)
    
    isapprover = False    
    for emp in employees : 
        if emp.id == input_employeeid :
            approvalfrhistorys = approvalfrhistory.objects.filter(frequest_id=input_frequest_id, employee_id = emp.id).last()
            if approvalfrhistorys is not None:
                isapprover = False
            else:
                isapprover = True
    
    return isapprover               


def get_isapprover_mis(input_employeeid):
    employees = employee.objects.filter(id=input_employeeid)
    isapprover = False
    for emp in employees :
        for depart in emp.departments.all():
            if depart.isapprover :
                isapprover = True

    return isapprover

def get_approver_frequest_depthead_wizard(input_frequest_id, input_frequest_department_id):
    employees = employee.objects.filter(departments = input_frequest_department_id)

    approver = []
    for emp in employees:
        if emp.position.isapprover :
            approvalfrhistorys_appr1 = approvalfrhistory.objects.filter(frequest_id=input_frequest_id, employee_id=emp.id).last()
            approver.append(emp.name)
            if approvalfrhistorys_appr1 is not None:
                approver.append('done')
            else:
                approver.append('yet')
    return approver

def get_approver_frequest_head_wizard(input_frequest_id, input_frequest_employee_id, input_frequest_department_id):
    employeeid = employee.objects.filter(pk = input_frequest_employee_id).last()

    employees = employee.objects.filter(pk = employeeid.head_id)

    approver = []
    for emp in employees:
        approvalfrhistorys_appr1 = approvalfrhistory.objects.filter(frequest_id=input_frequest_id, employee_id=emp.id).last()
        approver.append(emp.name)
        if approvalfrhistorys_appr1 is not None:
            approver.append('done')
        else:
            approver.append('yet')
    return approver

def get_approver_frequest_genmgr_wizard(input_frequest_id, input_position_id):
    employees = employee.objects.filter(position_id = input_position_id)

    approver = []
    for emp in employees:
        if emp.position.isapprover_last :
            approvalfrhistorys_appr1 = approvalfrhistory.objects.filter(frequest_id=input_frequest_id, employee_id=emp.id).last()
            approver.append(emp.name)
            if approvalfrhistorys_appr1 is not None:
                approver.append('done')
            else:
                approver.append('yet')
    return approver

def get_isapproved_frequest_misdept_wizard(input_frequest_id):
    dept = department.objects.filter(isapprover=True).last()
    approvalfrhistorys_appr = approvalfrhistory.objects.filter(frequest_id=input_frequest_id, department_id=dept.id).last()

    isapproved = []
    if approvalfrhistorys_appr is not None:
        isapproved.append('done')
        isapproved.append(approvalfrhistorys_appr.status)
    else:
        isapproved.append('yet')
        isapproved.append('DELAYED')
        

    return isapproved


def get_last_number_cash(inptype):
    lastnbr = crequest.objects.filter(proposalyear=int(inptype)).order_by('code').last()
    if lastnbr is not None:
        sendlastnbr = lastnbr.code    
        prefix = (sendlastnbr[0:5])
        suffix = str(int(sendlastnbr[4:9]) + 1).zfill(4)
    else:
        prefix = str(inptype)   
        suffix = '00001'
        
    return prefix + suffix


def get_iscashapprover(inpEmployeID, crequestID, crequestDeptId):
    employees = employee.objects.filter(id=inpEmployeID)
    
    idMatch = 0
    isapprover = False    
    for emp in employees : 
        #APPROVER 1 DEPT HEAD
        iscashapproverDeptHead =checkIsCashApproverDeptHeadByID(emp.id, crequestDeptId)
        iscashapproverFinManager =checkIsCashApproverFinManager(emp.id)
        iscashapproverAPFinance =checkIsCashApproverAPFinance(emp.id)

        if iscashapproverDeptHead:
            isapprover = True

            approvalcrhistorys_count = approvalcrhistory.objects.filter(crequest_id=crequestID, employee_id = emp.id).count()
            if approvalcrhistorys_count > 0:
                isapprover = False  
        elif iscashapproverFinManager :
       
            approvalcrhistorys_count = approvalcrhistory.objects.filter(crequest_id=crequestID).count()

            if approvalcrhistorys_count == 1 :
                    isapprover = True
             
        elif iscashapproverAPFinance:
            approvalcrhistorys_count = approvalcrhistory.objects.filter(crequest_id=crequestID).count()
            
            if approvalcrhistorys_count == 2 :
                isapprover = True
                
    return isapprover

def checkIsCashApproverFinManager(inputEmployeeID):
    cashapprovers=cashapprover.objects.filter(Q(approver_id=inputEmployeeID)|Q(backupapprover_id=inputEmployeeID), approverorder=1).count()

    IsCashApprover = False
    if cashapprovers > 0 :
        IsCashApprover = True

    return IsCashApprover

def checkIsCashApproverAPFinance(inputEmployeeID):
    cashapprovers=cashapprover.objects.filter(Q(approver_id=inputEmployeeID)|Q(backupapprover_id=inputEmployeeID),approverorder=2).count()

    IsCashApprover = False
    if cashapprovers > 0 :
        IsCashApprover = True

    return IsCashApprover

def checkIsCashApproverDeptHead(inputEmployeeID):
    departments = department.objects.filter(approver_id=inputEmployeeID).last()
    
    isapprover = False    
    if departments is not None:
        isapprover = True

    return isapprover

def checkIsCashApproverDeptHeadByID(inputEmployeeID, inputDepartmentID):
    departments = department.objects.filter(id=inputDepartmentID, approver_id=inputEmployeeID).last()
    
    isapprover = False    
    if departments is not None:
        isapprover = True

    return isapprover

def getDeptList(inputEmployeeID):
    employees = employee.objects.filter(id=inputEmployeeID)
    
    deptList = []    
    for emp in employees : 

        for depart in emp.departments.all():
            deptList.append(depart.id)            
    return deptList

def get_approver_frequest_head_email(input_employee_id, input_department_id):
    employeeid = employee.objects.filter(pk = input_employee_id).last()
    employeeHead = employee.objects.filter(pk = employeeid.head_id)

    approverData = []
    for emp in employeeHead:
        approverData.append(emp.email)
        approverData.append(str(emp.id))
        approverData.append(str(input_department_id))
    return approverData

def get_approver_frequest_depthead_email(input_frequest_department_id):
    employees = employee.objects.filter(departments = input_frequest_department_id)

    approverData = []
    for emp in employees:
        for depart in emp.departments.all():
            if emp.position.isapprover :
                approverData.append(emp.email)
                approverData.append(str(emp.id))
                approverData.append(str(depart.id))
    return approverData


#LOGIK APPROVER PERTAMA / DEPT HEAD
def get_first_approver_crequest_email(input_frequest_department_id):
    dp = department.objects.filter(pk = input_frequest_department_id).last()
    employees = employee.objects.filter(pk = dp.approver_id)

    approverData = []
    for emp in employees:
        approverData.append(emp.email)
        approverData.append(str(emp.id))
        approverData.append(str(input_frequest_department_id))
    return approverData


def get_approver_frequest_genmgr_email(isLastApprover):
    getIdPositionGenMGR = position.objects.get(isapprover_last = isLastApprover)

    getEmployee = employee.objects.filter(position_id=getIdPositionGenMGR.id)

    approverData = []
    for emp in getEmployee:
        for depart in emp.departments.all():
            approverData.append(emp.email)
            approverData.append(str(emp.id))
            approverData.append(str(depart.id))
    return approverData

#HELPDESK REQUEST
def emailSendWhenSubmit(subjectEmail, departselect, codenumber):
    statusSend = False
    
    frequestdata = frequest.objects.get(code=codenumber)
    if frequestdata.type != "CRF":
        deptHeadData = get_approver_frequest_depthead_email(departselect)
        subject, from_email, to = subjectEmail, subjectEmail + settings.EMAIL_FROM, deptHeadData[0]
    
    text_content = 'This is an important message.'
    
    if frequestdata.type == "CRF":
        deptHeadData = get_approver_frequest_head_email(frequestdata.employee.id, frequestdata.department.id)
        subject, from_email, to = subjectEmail, subjectEmail + settings.EMAIL_FROM, deptHeadData[0]
        
        html_content = '<div style="text-align:center;">' + '<h2>Requester of Consumable Request need your action</h2>' + '<p>Nomor Request: ' + frequestdata.code + '</p>' + '<p>Requester: ' + frequestdata.employee.name + '</p>' + '<p> Department: ' + frequestdata.department.name + '</p>' + '<p> Barang: ' + frequestdata.item.item_name + '</p><br>' + '<a target ="popup"' +  'href="' + webhost + 'crfapproveemailDeptHead/' + frequestdata.code + '/' + deptHeadData[1]  + '/' + deptHeadData[2] + '/3000">' + '<button style="background-color:#dc3545;color:white;border-color: #dc3545;padding: 2%;border-radius: 3px;">Reject</button></a>' + '&nbsp; &nbsp; &nbsp;' + '<a target ="popup" href="' + webhost + 'crfapproveemailDeptHead/' + frequestdata.code + '/' + deptHeadData[1] + '/' + deptHeadData[2] +  '/2000">'  + '<button style="background-color:#007bff;color:white;border-color: #007bff;padding: 2%;border-radius: 3px;">Accept</button></a>' +'<br><br><br>' + settings.COMPANY_ADDRESS + '</div>' 
    elif frequestdata.type == "SRF":
        html_content = '<div style="text-align:center;">' + '<h2>Requester of Service Request need your action</h2>' + '<p>Nomor Request: ' + frequestdata.code + '</p>' + '<p>Requester: ' + frequestdata.employee.name + '</p>' + '<p> Department: ' + frequestdata.department.name + '</p>' + '<p> DESCRIPTION : ' + frequestdata.description + '</p><br>' + '<a target ="popup" href="'+ webhost + 'crfapproveemailDeptHead/' + frequestdata.code + '/' + deptHeadData[1]  + '/' + deptHeadData[2] + '/3000">' + '<button style="background-color:#dc3545;color:white;border-color: #dc3545;padding: 2%;border-radius: 3px;">Reject</button></a>' + '&nbsp; &nbsp; &nbsp;' + '<a target ="popup" href="' + webhost + 'crfapproveemailDeptHead/' + frequestdata.code + '/' + deptHeadData[1] + '/' + deptHeadData[2] +  '/2000">'  + '<button style="background-color:#007bff;color:white;border-color: #007bff;padding: 2%;border-radius: 3px;">Accept</button></a>' +'<br><br><br>' + settings.COMPANY_ADDRESS + '</div>' 
    elif frequestdata.type == "PRF":
        html_content = '<div style="text-align:center;">' + '<h2>Requester of Peripheral Request need your action</h2>' + '<p>Nomor Request: ' + frequestdata.code + '</p>' + '<p>Requester: ' + frequestdata.employee.name + '</p>' + '<p> Department: ' + frequestdata.department.name + '</p>' + '<p> Barang : ' + frequestdata.item.item_name + '</p>' + '<p> Reason : ' + frequestdata.description +  '</p>' + '<a target ="popup" href="' + webhost + 'prfapproveemailDeptHead/' + frequestdata.code + '/' + deptHeadData[1]  + '/' + deptHeadData[2] + '/3000">' + '<button style="background-color:#dc3545;color:white;border-color: #dc3545;padding: 2%;border-radius: 3px;">Reject</button></a>' + '&nbsp; &nbsp; &nbsp;' + '<a target ="popup" href="' + webhost + 'prfapproveemailDeptHead/' + frequestdata.code + '/' + deptHeadData[1] + '/' + deptHeadData[2] +  '/2000">'  + '<button style="background-color:#007bff;color:white;border-color: #007bff;padding: 2%;border-radius: 3px;">Accept</button></a>' +'<br><br><br>' + settings.COMPANY_ADDRESS + '</div>'
            
    createScheduleEmails = createScheduleEmail(html_content, subject, from_email, to, frequestdata.code) 
    statusSend = True                  

    return statusSend

#HELPDESK REQUEST
def sendEmailWhenApproveDeptHead(codenumber, statusInfo):
    frequests = frequest.objects.get(code=codenumber)
    statusSend = False

    if frequests.type == "PRF":
        itemDisplay = 'Barang: ' + frequests.item.item_name 
        subjectDisplay = 'Peripheral Request Forms (PRF) '   

        if frequests.status == 'APPROVE':  
            if frequests.item.item_price > 4999999 :     
                isLastApprover = True
                deptHeadData = get_approver_frequest_genmgr_email(isLastApprover)

                subject, from_email, to = subjectDisplay, subjectDisplay + settings.EMAIL_FROM, deptHeadData[0]
                text_content = 'This is an important message.'
                html_content = '<div style="text-align:center;">' + '<h2>Requester of Peripheral Request need your action</h2>' + '<p>Nomor Request: ' + frequests.code + '</p>' + '<p>Requester: ' + frequests.employee.name + '</p>' + '<p> Department: ' + frequests.department.name + '</p>' + '<p>' + itemDisplay + '</p>'+ '<p> Reason : ' + frequests.description +  '</p><br>'  +  '<a target ="popup" href="' + webhost + 'prfapproveemailGenMGR/' + frequests.code + '/' + deptHeadData[1]  + '/' + deptHeadData[2] + '/3000">' + '<button style="background-color:#dc3545;color:white;border-color: #dc3545;padding: 2%;border-radius: 3px;">Reject</button></a>' + '&nbsp; &nbsp; &nbsp;' + '<a target ="popup" href="' + webhost + 'prfapproveemailGenMGR/' + frequests.code + '/' + deptHeadData[1] + '/' + deptHeadData[2] +  '/2000">'  + '<button style="background-color:#007bff;color:white;border-color: #007bff;padding: 2%;border-radius: 3px;">Accept</button></a>' +'<br><br><br>' + settings.COMPANY_ADDRESS + '</div>' 
                
                createScheduleEmails = createScheduleEmail(html_content, subject, from_email, to, frequests.code) 
                statusSend = True
            else :
                statusSend = sendEmailWhenApproveGenMGR(codenumber, frequests.status)

        else:
            subject, from_email, to = subjectDisplay + frequests.code, subjectDisplay + settings.EMAIL_FROM, frequests.employee.email
            text_content = 'This is an important message.'
            html_content = '<div style="text-align:center;">' + '<h2>Your Request Has Been ' + statusInfo + '</h2>' + '<p>Nomor Request: ' + frequests.code + '</p>' + '<p>Requester: ' + frequests.employee.name + '</p>' + '<p> Department: ' + frequests.department.name + '</p>' + '<p>' + itemDisplay + '</p><br>' +'<br><br><br>' + settings.COMPANY_ADDRESS + '</div>' 
            
            createScheduleEmails = createScheduleEmail(html_content, subject, from_email, to, frequests.code) 
            statusSend = True
    else :
        if frequests.type == "CRF":
            itemDisplay = 'Barang: ' + frequests.item.item_name 
            subjectDisplay = 'Consumable Request Forms (CRF) '
            bodyEmailDisplay = 'Consumable Request'
        elif frequests.type == "SRF":
            itemDisplay = 'DESCRIPTION: ' + frequests.description
            subjectDisplay = 'Service Request Forms (SRF) '
            bodyEmailDisplay = 'Service Request'

        subject, from_email, to = subjectDisplay + frequests.code, subjectDisplay + settings.EMAIL_FROM, frequests.employee.email
        text_content = 'This is an important message.'
        html_content = '<div style="text-align:center;">' + '<h2>Your Request Has Been ' + statusInfo + '</h2>' + '<p>Nomor Request: ' + frequests.code + '</p>' + '<p>Requester: ' + frequests.employee.name + '</p>' + '<p> Department: ' + frequests.department.name + '</p>' + '<p>' + itemDisplay + '</p><br>' +'<br><br><br>' + settings.COMPANY_ADDRESS + '</div>' 

        createScheduleEmails = createScheduleEmail(html_content, subject, from_email, to, frequests.code) 
        statusSend = True

        if frequests.status == 'APPROVE':
            emailMISTeamArray = get_email_allMIS(True)
            for emailReceiver in emailMISTeamArray: 
                subject, from_email, to = subjectDisplay + frequests.code, subjectDisplay + settings.EMAIL_FROM, emailReceiver
                text_content = 'This is an important message.'
                html_content = '<div style="text-align:center;"><h2>Requester ' + bodyEmailDisplay +  ' Need Your Action' + '</h2>' + '<p>Nomor Request: ' + frequests.code + '</p>' + '<p>Requester: ' + frequests.employee.name + '</p>' + '<p> Department: ' + frequests.department.name + '</p>' + '<p>' + itemDisplay + '</p><br>' +'<br><br><br>' + settings.COMPANY_ADDRESS + '</div>' 
                
                messagesTraceback = statusInfo
                resendMaterial = subject + ";" + from_email + ";" + to + ";" + html_content

                createScheduleEmails = createScheduleEmail(html_content, subject, from_email, to, frequests.code) 
                statusSend = True

    return statusSend

#HELPDESK REQUEST
def sendEmailWhenApproveGenMGR(codenumber, statusInfo):
    frequests = frequest.objects.get(code=codenumber)
    statusSend = False

    itemDisplay = 'Barang: ' + frequests.item.item_name 
    subjectDisplay = 'Peripheral Request Forms (PRF) '
    bodyEmailDisplay = 'Peripheral Request'

    subject, from_email, to = subjectDisplay + frequests.code, subjectDisplay + settings.EMAIL_FROM, frequests.employee.email
    text_content = 'This is an important message.'
    html_content = '<div style="text-align:center;">' + '<h2>Your Request Has Been ' + statusInfo + '</h2>' + '<p>Nomor Request: ' + frequests.code + '</p>' + '<p>Requester: ' + frequests.employee.name + '</p>' + '<p> Department: ' + frequests.department.name + '</p>' + '<p>' + itemDisplay + '</p><br>' +'<br><br><br>' + settings.COMPANY_ADDRESS + '</div>' 
    
    messagesTraceback = statusInfo
    resendMaterial = subject + ";" + from_email + ";" + to + ";" + html_content

    createScheduleEmails = createScheduleEmail(html_content, subject, from_email, to, frequests.code) 
    statusSend = True

    if frequests.status == 'APPROVE':
        emailMISTeamArray = get_email_allMIS(True)
            
        for emailReceiver in emailMISTeamArray: 
            subject, from_email, to = subjectDisplay + frequests.code, subjectDisplay + settings.EMAIL_FROM, emailReceiver
            text_content = 'This is an important message.'
            html_content = '<div style="text-align:center;"><h2>Requester ' + bodyEmailDisplay +  ' Need Your Action' + '</h2>' + '<p>Nomor Request: ' + frequests.code + '</p>' + '<p>Requester: ' + frequests.employee.name + '</p>' + '<p> Department: ' + frequests.department.name + '</p>' + '<p>' + itemDisplay + '</p><br>' +'<br><br><br>' + settings.COMPANY_ADDRESS + '</div>' 
           
            messagesTraceback = statusInfo
            resendMaterial = subject + ";" + from_email + ";" + to + ";" + html_content 
            
            createScheduleEmails = createScheduleEmail(html_content, subject, from_email, to, frequests.code) 
            statusSend = True

    return statusSend

#CASH REQUEST
def emailSendWhenSubmitCash(subjectEmail, departselect, codenumber):
    statusSend = False
    
    deptHeadData = get_first_approver_crequest_email(departselect)
    frequestdata = crequest.objects.get(code=codenumber)
 
    subject, from_email, to = subjectEmail, subjectEmail + settings.EMAIL_FROM, deptHeadData[0]
    text_content = 'This is an important message.'
    
    vamount = "Rp{:,.2f}".format(frequestdata.amount)
    
    html_content = '<div style="text-align:center;">' + '<h2>Requester of Cash Advance Request need your action</h2>' + '<p>No Advance: ' + frequestdata.code + '</p>' + '<p>Name of Requester: ' + frequestdata.requestor + '</p>' + '<p> Department: ' + frequestdata.department.name + '</p>' + '<p> Need Date : ' + str(frequestdata.needdate) + '</p>' + '<p> Amount : ' + str(vamount) +  '</p>' + '<p> Purpose : ' +  frequestdata.purpose + '</p>' + '<a target ="popup" href="' + webhost + 'cashapproveemailLevel/' + frequestdata.code + '/' + deptHeadData[1]  + '/' + deptHeadData[2] + '/3000/0">' + '<button style="background-color:#dc3545;color:white;border-color: #dc3545;padding: 2%;border-radius: 3px;">Reject</button></a>' + '&nbsp; &nbsp; &nbsp;' + '<a target ="popup" href="' + webhost + 'cashapproveemailLevel/' + frequestdata.code + '/' + deptHeadData[1] + '/' + deptHeadData[2] +  '/2000/0">'  + '<button style="background-color:#007bff;color:white;border-color: #007bff;padding: 2%;border-radius: 3px;">Accept</button></a>' + '<br><br><br>' + settings.COMPANY_ADDRESS + '</div>' 
    
    messagesTraceback = departselect
    resendMaterial = subject + ";" + from_email + ";" + to + ";" + html_content
    
    createScheduleEmails = createScheduleEmail(html_content, subject, from_email, to, frequestdata.code) 
    statusSend = True

    return statusSend

#CASH REQUEST
def sendEmailCashWhenApproveApprovalLevel(codenumber, countapproval):
    statusSend = False
    frequestdata = crequest.objects.get(code=codenumber)

    vamount = "Rp{:,.2f}".format(frequestdata.amount)
    
    def sendEmailToRequestor():
        statusSendInDef = False
        subjectEmail = "Form Cash Advance - " + frequestdata.code
        subject, from_email, to = subjectEmail, subjectEmail + settings.EMAIL_FROM, frequestdata.requestorid.email
        text_content = 'This is an important message.'
        html_content = '<div style="text-align:center;">' + '<h2>Your Cash Advance Request has been Processed</h2>' + '<p>No Advance: ' + frequestdata.code + '</p>' + '<p>Name of Requester: ' + frequestdata.requestor + '</p>' + '<p> Department: ' + frequestdata.department.name + '</p>' + '<p> Need Date : ' + str(frequestdata.needdate) + '</p>' + '<p> Amount : ' + str(vamount) +  '</p>' + '<p> Purpose : ' +  frequestdata.purpose + '</p>'  + '<br><br><br>' + settings.COMPANY_ADDRESS + '</div>'     
        
        createScheduleEmails = createScheduleEmail(html_content, subject, from_email, to, frequestdata.code) 
        statusSendInDef = True

    if countapproval == 3 : #LAST APPROVER
        statusSend = sendEmailToRequestor()                 
    else:
        if frequestdata.status == 'APPROVE':
            approver = get_cashapprover(countapproval)
            
            #email to approver 1
            subjectEmail = "Form Cash Advance - " + frequestdata.code
            subject, from_email, to = subjectEmail, subjectEmail + settings.EMAIL_FROM, approver[0]
            text_content = 'This is an important message.'

            if countapproval == 2:
                html_content = '<div style="text-align:center;">' + '<h2>Requester of Cash Advance Request need your action</h2>' + '<p>No Advance: ' + frequestdata.code + '</p>' + '<p>Name of Requester: ' + frequestdata.requestor + '</p>' + '<p> Department: ' + frequestdata.department.name + '</p>' + '<p> Need Date : ' + str(frequestdata.needdate) + '</p>' + '<p> Amount : ' + str(vamount) +  '</p>' + '<p> Purpose : ' +  frequestdata.purpose + '</p><br>' + '<a target ="popup" href="' + webhost + 'cashapproveemailLevel/' + frequestdata.code + '/' + approver[1]  + '/' + approver[2] + '/3000/' + str(countapproval) + '">' + '<button style="background-color:#dc3545;color:white;border-color: #dc3545;padding: 2%;border-radius: 3px;">Reject</button></a>' + '&nbsp; &nbsp; &nbsp;' + '<a target ="popup" href="' + webhost + 'cashapproveemailLevel/' + frequestdata.code + '/' + approver[1] + '/' + approver[2] +  '/2000/' + str(countapproval) + '">'  + '<button style="background-color:#007bff;color:white;border-color: #007bff;padding: 2%;border-radius: 3px;">Accept</button></a>' + '<br><br><br>' + settings.COMPANY_ADDRESS + '</div>' 
            else: 
                html_content = '<div style="text-align:center;">' + '<h2>Requester of Cash Advance Request need your action</h2>' + '<p>No Advance: ' + frequestdata.code + '</p>' + '<p>Name of Requester: ' + frequestdata.requestor + '</p>' + '<p> Department: ' + frequestdata.department.name + '</p>' + '<p> Need Date : ' + str(frequestdata.needdate) + '</p>' + '<p> Amount : ' + str(vamount) +  '</p>' + '<p> Purpose : ' +  frequestdata.purpose + '</p><br>' + '<a target ="popup" href="' + webhost + 'cashapproveemailLevel/' + frequestdata.code + '/' + approver[1]  + '/' + approver[2] + '/3000/' + str(countapproval) + '">' + '<button style="background-color:#dc3545;color:white;border-color: #dc3545;padding: 2%;border-radius: 3px;">Reject</button></a>' + '&nbsp; &nbsp; &nbsp;' + '<a target ="popup" href="' + webhost + 'cashapproveemailLevel/' + frequestdata.code + '/' + approver[1] + '/' + approver[2] +  '/2000/' + str(countapproval) + '">'  + '<button style="background-color:#007bff;color:white;border-color: #007bff;padding: 2%;border-radius: 3px;">Accept</button></a>' + '<br><br><br>' + settings.COMPANY_ADDRESS + '</div>' 

            createScheduleEmails = createScheduleEmail(html_content, subject, from_email, to, frequestdata.code) 
            statusSend = True

            #email to backupapprover 
            
            if len(approver[3]) > 0 :
                subjectEmail = "Form Cash Advance - " + frequestdata.code
                subject, from_email, to = subjectEmail, subjectEmail + settings.EMAIL_FROM, approver[3]
                text_content = 'This is an important message.'
            
                if countapproval == 2:
                    html_content = '<div style="text-align:center;">' + '<h2>Requester of Cash Advance Request need your action</h2>' + '<p>No Advance: ' + frequestdata.code + '</p>' + '<p>Name of Requester: ' + frequestdata.requestor + '</p>' + '<p> Department: ' + frequestdata.department.name + '</p>' + '<p> Need Date : ' + str(frequestdata.needdate) + '</p>' + '<p> Amount : ' + str(vamount) +  '</p>' + '<p> Purpose : ' +  frequestdata.purpose + '</p>' + '<a target ="popup" href="' + webhost + 'cashapproveemailLevel/' + frequestdata.code + '/' + approver[4]  + '/' + approver[5] + '/3000/' + str(countapproval) + '">' + '<a target ="popup" href="' + webhost + 'cashapproveemailLevel/' + frequestdata.code + '/' + approver[4] + '/' + approver[5] +  '/2000/' + str(countapproval) + '">'  + '<button style="background-color:#007bff;color:white;border-color: #007bff;padding: 2%;border-radius: 3px;">Accept</button></a>' + '<br><br><br>' + settings.COMPANY_ADDRESS + '</div>' 
                else:
                    html_content = '<div style="text-align:center;">' + '<h2>Requester of Cash Advance Request need your action</h2>' + '<p>No Advance: ' + frequestdata.code + '</p>' + '<p>Name of Requester: ' + frequestdata.requestor + '</p>' + '<p> Department: ' + frequestdata.department.name + '</p>' + '<p> Need Date : ' + str(frequestdata.needdate) + '</p>' + '<p> Amount : ' + str(vamount) +  '</p>' + '<p> Purpose : ' +  frequestdata.purpose + '</p>' + '<a target ="popup" href="' + webhost + 'cashapproveemailLevel/' + frequestdata.code + '/' + approver[4]  + '/' + approver[5] + '/3000/' + str(countapproval) + '">' + '<button style="background-color:#dc3545;color:white;border-color: #dc3545;padding: 2%;border-radius: 3px;">Reject</button></a>' + '&nbsp; &nbsp; &nbsp;' + '<a target ="popup" href="' + webhost + 'cashapproveemailLevel/' + frequestdata.code + '/' + approver[4] + '/' + approver[5] +  '/2000/' + str(countapproval) + '">'  + '<button style="background-color:#007bff;color:white;border-color: #007bff;padding: 2%;border-radius: 3px;">Accept</button></a>' + '<br><br><br>' + settings.COMPANY_ADDRESS + '</div>' 

                createScheduleEmails = createScheduleEmail(html_content, subject, from_email, to, frequestdata.code) 

            statusSend = sendEmailToRequestor() 
        else :       
            subjectEmail = "Form Cash Advance - " + frequestdata.code
            subject, from_email, to = subjectEmail, subjectEmail + settings.EMAIL_FROM, frequestdata.requestorid.email
            text_content = 'This is an important message.'    
            html_content = '<div style="text-align:center;">' + '<h2>Your Cash Advance Request has been Rejected</h2>' + '<p>No Advance: ' + frequestdata.code + '</p>' + '<p>Name of Requester: ' + frequestdata.requestor + '</p>' + '<p> Department: ' + frequestdata.department.name + '</p>' + '<p> Need Date : ' + str(frequestdata.needdate) + '</p>' + '<p> Amount : ' + str(vamount) +  '</p>' + '<p> Purpose : ' +  frequestdata.purpose + '</p>'  + '<br><br><br>' + settings.COMPANY_ADDRESS + '</div>' 

            createScheduleEmails = createScheduleEmail(html_content, subject, from_email, to, frequestdata.code) 
            statusSend = True

    return statusSend

def get_cashapprover(inputapproverorder):
    cashapprovers=cashapprover.objects.filter(approverorder=inputapproverorder).last()

    approverData = [] 
    approverData.append(cashapprovers.approver.email)
    approverData.append(str(cashapprovers.approver_id)) 
    approverData.append(str(cashapprovers.approver.departments.all().last().id))
   
    if cashapprovers.backupapprover_id :
        approverData.append(cashapprovers.backupapprover.email)
        approverData.append(str(cashapprovers.backupapprover_id)) 
        approverData.append(str(cashapprovers.backupapprover.departments.all().last().id))
    else :
        approverData.append('')
        approverData.append('')
        approverData.append('')
        
    return approverData

def testlogic(codenumber):

    frequestdata = crequest.objects.get(code=codenumber)
    print(frequestdata.requestorid.email)
    return print(frequestdata.requestorid.email)
    
from django.core import mail

def test_send_mail():
   # Use Django send_mail function to construct a message
   # Note that you don't have to use this function at all.
   # Any other way of sending an email in Django would work just fine. 
   mail.send_mail(
        'Example subject here',
        'Here is the message body.',
        settings.EMAIL_HOST_USER,
        ['alfianpical3149@gmail.com']
    )
