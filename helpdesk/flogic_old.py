from datetime import datetime, timedelta
from .models import crequest, department, employee, frequest, item, approvalfrhistory,frequestdetail,position,approvalcrhistory, cashapprover
from django.db.models import Q
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives

from django.conf import settings

#MENCARI NOMOR TERAKHIR
def get_last_number(inptype):
    lastnbr = frequest.objects.filter(type=inptype, submitted=datetime.now()).order_by('id').last()
    
    sendlastnbr = ''
    if lastnbr is not None:
        sendlastnbr = lastnbr.code    
        prefix = (sendlastnbr[0:14])
        suffix = str(int(sendlastnbr[13:17]) + 1).zfill(2)
    else :
        prefix = inptype + '-' + str(datetime.now().year) + str(datetime.now().month) + str(datetime.now().day) + '-'   
        suffix = '001'
    return prefix + suffix

#MENCARI ROLE APPROVAL USER
def get_isapprover(input_employeeid, input_frequest_id, input_frequest_department):
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
                approvalfrhistorys = approvalfrhistory.objects.filter(frequest_id=input_frequest_id, status='ACCEPTED').last()
                if approvalfrhistorys is not None and approvalfrhistorys.employee_id != emp.id:
                    isapprover = True
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
    lastnbr = crequest.objects.filter(proposalyear=int(inptype)).order_by('id').last()
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
    employees = employee.objects.filter(id=inputEmployeeID)
    
    isapprover = False    
    for emp in employees : 

        for depart in emp.departments.all():
            #APPROVER 1 DEPT HEAD
            if  (emp.position.isapprover) :
                isapprover = True

    return isapprover

def checkIsCashApproverDeptHeadByID(inputEmployeeID, inputDepartmentID):
    employees = employee.objects.filter(id=inputEmployeeID)
    
    isapprover = False    
    for emp in employees : 

        for depart in emp.departments.all():
            #APPROVER 1 DEPT HEAD
            if  (emp.position.isapprover) and (depart.id == inputDepartmentID) :
                isapprover = True
    return isapprover

def getDeptList(inputEmployeeID):
    employees = employee.objects.filter(id=inputEmployeeID)
    
    deptList = []    
    for emp in employees : 

        for depart in emp.departments.all():
            deptList.append(depart.id)            
    return deptList

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

def emailSendWhenSubmit(subjectEmail, departselect, codenumber):
    statusSend = False
    try:
        deptHeadData = get_approver_frequest_depthead_email(departselect)
        frequestdata = frequest.objects.get(code=codenumber)

        subject, from_email, to = subjectEmail, settings.EMAIL_HOST_USER, deptHeadData[0]
        text_content = 'This is an important message.'
        
        if frequestdata.type == "CRF":
            html_content = '<div style="text-align:center;">' + '<h2>Requester of Consumable Request need your action</h2>' + '<p>Nomor Request: ' + frequestdata.code + '</p>' + '<p>Requester: ' + frequestdata.employee.name + '</p>' + '<p> Department: ' + frequestdata.department.name + '</p>' + '<p> Barang: ' + frequestdata.item.item_name + '</p><br>' + '<a target ="popup" href="https://newemgmt.sinarmeadow.com/crfapproveemailDeptHead/' + frequestdata.code + '/' + deptHeadData[1]  + '/' + deptHeadData[2] + '/3000">' + '<button style="background-color:#dc3545;color:white;border-color: #dc3545;padding: 2%;border-radius: 3px;">Reject</button></a>' + '&nbsp; &nbsp; &nbsp;' + '<a target ="popup" href="https://newemgmt.sinarmeadow.com/crfapproveemailDeptHead/' + frequestdata.code + '/' + deptHeadData[1] + '/' + deptHeadData[2] +  '/2000">'  + '<button style="background-color:#007bff;color:white;border-color: #007bff;padding: 2%;border-radius: 3px;">Accept</button></a>' +'<br><br><br>' + '<small><p>PT. Sinar Meadow International Indonesia</p>' + '<p>Kawasan Industri Pulogadung Blok III.S.20-23 No.3, Jalan Puloayang 2, RW.9, Jatinegara</p>' + '<p>Cakung, Kota Jakarta Timur</p>' + '<p>Daerah Khusus Ibukota Jakarta 13260</p>' + '</div>' 
        elif frequestdata.type == "SRF":
            html_content = '<div style="text-align:center;">' + '<h2>Requester of Service Request need your action</h2>' + '<p>Nomor Request: ' + frequestdata.code + '</p>' + '<p>Requester: ' + frequestdata.employee.name + '</p>' + '<p> Department: ' + frequestdata.department.name + '</p>' + '<p> DESCRIPTION : ' + frequestdata.description + '</p><br>' + '<a target ="popup" href="https://newemgmt.sinarmeadow.com/crfapproveemailDeptHead/' + frequestdata.code + '/' + deptHeadData[1]  + '/' + deptHeadData[2] + '/3000">' + '<button style="background-color:#dc3545;color:white;border-color: #dc3545;padding: 2%;border-radius: 3px;">Reject</button></a>' + '&nbsp; &nbsp; &nbsp;' + '<a target ="popup" href="https://newemgmt.sinarmeadow.com/crfapproveemailDeptHead/' + frequestdata.code + '/' + deptHeadData[1] + '/' + deptHeadData[2] +  '/2000">'  + '<button style="background-color:#007bff;color:white;border-color: #007bff;padding: 2%;border-radius: 3px;">Accept</button></a>' +'<br><br><br>' + '<small><p>PT. Sinar Meadow International Indonesia</p>' + '<p>Kawasan Industri Pulogadung Blok III.S.20-23 No.3, Jalan Puloayang 2, RW.9, Jatinegara</p>' + '<p>Cakung, Kota Jakarta Timur</p>' + '<p>Daerah Khusus Ibukota Jakarta 13260</p>' + '</div>' 
        elif frequestdata.type == "PRF":
            html_content = '<div style="text-align:center;">' + '<h2>Requester of Peripheral Request need your action</h2>' + '<p>Nomor Request: ' + frequestdata.code + '</p>' + '<p>Requester: ' + frequestdata.employee.name + '</p>' + '<p> Department: ' + frequestdata.department.name + '</p>' + '<p> Barang : ' + frequestdata.item.item_name + '</p>' + '<p> Reason : ' + frequestdata.description +  '</p>' + '<a target ="popup" href="https://newemgmt.sinarmeadow.com/prfapproveemailDeptHead/' + frequestdata.code + '/' + deptHeadData[1]  + '/' + deptHeadData[2] + '/3000">' + '<button style="background-color:#dc3545;color:white;border-color: #dc3545;padding: 2%;border-radius: 3px;">Reject</button></a>' + '&nbsp; &nbsp; &nbsp;' + '<a target ="popup" href="https://newemgmt.sinarmeadow.com/prfapproveemailDeptHead/' + frequestdata.code + '/' + deptHeadData[1] + '/' + deptHeadData[2] +  '/2000">'  + '<button style="background-color:#007bff;color:white;border-color: #007bff;padding: 2%;border-radius: 3px;">Accept</button></a>' +'<br><br><br>' + '<small><p>PT. Sinar Meadow International Indonesia</p>' + '<p>Kawasan Industri Pulogadung Blok III.S.20-23 No.3, Jalan Puloayang 2, RW.9, Jatinegara</p>' + '<p>Cakung, Kota Jakarta Timur</p>' + '<p>Daerah Khusus Ibukota Jakarta 13260</p>' + '</div>' 

        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        statusSend = True
    except Exception:
        statusSend = False

    return statusSend

def sendEmailWhenApproveDeptHead(codenumber, statusInfo):
    frequests = frequest.objects.get(code=codenumber)
    statusSend = False

    try:
        if frequests.type == "PRF":
            itemDisplay = 'Barang: ' + frequests.item.item_name 
            subjectDisplay = 'Peripheral Request Forms (PRF) : '   

            if frequests.status == 'APPROVE':           
                isLastApprover = True
                deptHeadData = get_approver_frequest_genmgr_email(isLastApprover)

                subject, from_email, to = subjectDisplay, settings.EMAIL_HOST_USER, deptHeadData[0]
                text_content = 'This is an important message.'
                html_content = '<div style="text-align:center;">' + '<h2>Requester of Peripheral Request need your action</h2>' + '<p>Nomor Request: ' + frequests.code + '</p>' + '<p>Requester: ' + frequests.employee.name + '</p>' + '<p> Department: ' + frequests.department.name + '</p>' + '<p>' + itemDisplay + '</p>'+ '<p> Reason : ' + frequests.description +  '</p><br>'  +  '<a target ="popup" href="https://newemgmt.sinarmeadow.com/prfapproveemailGenMGR/' + frequests.code + '/' + deptHeadData[1]  + '/' + deptHeadData[2] + '/3000">' + '<button style="background-color:#dc3545;color:white;border-color: #dc3545;padding: 2%;border-radius: 3px;">Reject</button></a>' + '&nbsp; &nbsp; &nbsp;' + '<a target ="popup" href="https://newemgmt.sinarmeadow.com/prfapproveemailGenMGR/' + frequests.code + '/' + deptHeadData[1] + '/' + deptHeadData[2] +  '/2000">'  + '<button style="background-color:#007bff;color:white;border-color: #007bff;padding: 2%;border-radius: 3px;">Accept</button></a>' +'<br><br><br>' + '<small><p>PT. Sinar Meadow International Indonesia</p>' + '<p>Kawasan Industri Pulogadung Blok III.S.20-23 No.3, Jalan Puloayang 2, RW.9, Jatinegara</p>' + '<p>Cakung, Kota Jakarta Timur</p>' + '<p>Daerah Khusus Ibukota Jakarta 13260</p>' + '</div>' 
                msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
                msg.attach_alternative(html_content, "text/html")
                msg.send()
            else:
                subject, from_email, to = subjectDisplay + frequests.code, settings.EMAIL_HOST_USER, frequests.employee.email
                text_content = 'This is an important message.'
                html_content = '<div style="text-align:center;">' + '<h2>Your Request Has Been ' + statusInfo + '</h2>' + '<p>Nomor Request: ' + frequests.code + '</p>' + '<p>Requester: ' + frequests.employee.name + '</p>' + '<p> Department: ' + frequests.department.name + '</p>' + '<p>' + itemDisplay + '</p><br>' +'<br><br><br>' + '<small><p>PT. Sinar Meadow International Indonesia</p>' + '<p>Kawasan Industri Pulogadung Blok III.S.20-23 No.3, Jalan Puloayang 2, RW.9, Jatinegara</p>' + '<p>Cakung, Kota Jakarta Timur</p>' + '<p>Daerah Khusus Ibukota Jakarta 13260</p>' + '</div>' 
                msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
                msg.attach_alternative(html_content, "text/html")
                msg.send()    
        else :
            if frequests.type == "CRF":
                itemDisplay = 'Barang: ' + frequests.item.item_name 
                subjectDisplay = 'Consumable Request Forms (CRF) : '
            elif frequests.type == "SRF":
                itemDisplay = 'DESCRIPTION: ' + frequests.description
                subjectDisplay = 'Service Request Forms (SRF) : '

            subject, from_email, to = subjectDisplay + frequests.code, settings.EMAIL_HOST_USER, frequests.employee.email
            text_content = 'This is an important message.'
            html_content = '<div style="text-align:center;">' + '<h2>Your Request Has Been ' + statusInfo + '</h2>' + '<p>Nomor Request: ' + frequests.code + '</p>' + '<p>Requester: ' + frequests.employee.name + '</p>' + '<p> Department: ' + frequests.department.name + '</p>' + '<p>' + itemDisplay + '</p><br>' +'<br><br><br>' + '<small><p>PT. Sinar Meadow International Indonesia</p>' + '<p>Kawasan Industri Pulogadung Blok III.S.20-23 No.3, Jalan Puloayang 2, RW.9, Jatinegara</p>' + '<p>Cakung, Kota Jakarta Timur</p>' + '<p>Daerah Khusus Ibukota Jakarta 13260</p>' + '</div>' 
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
    except Exception:
        statusSend = False
    return statusSend


def sendEmailWhenApproveGenMGR(codenumber, statusInfo):
    frequests = frequest.objects.get(code=codenumber)
    statusSend = False

    try:
        itemDisplay = 'Barang: ' + frequests.item.item_name 
        subjectDisplay = 'Peripheral Request Forms (PRF) : '

        subject, from_email, to = subjectDisplay + frequests.code, settings.EMAIL_HOST_USER, frequests.employee.email
        text_content = 'This is an important message.'
        html_content = '<div style="text-align:center;">' + '<h2>Your Request Has Been ' + statusInfo + '</h2>' + '<p>Nomor Request: ' + frequests.code + '</p>' + '<p>Requester: ' + frequests.employee.name + '</p>' + '<p> Department: ' + frequests.department.name + '</p>' + '<p>' + itemDisplay + '</p><br>' +'<br><br><br>' + '<small><p>PT. Sinar Meadow International Indonesia</p>' + '<p>Kawasan Industri Pulogadung Blok III.S.20-23 No.3, Jalan Puloayang 2, RW.9, Jatinegara</p>' + '<p>Cakung, Kota Jakarta Timur</p>' + '<p>Daerah Khusus Ibukota Jakarta 13260</p>' + '</div>' 
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    except Exception:
        statusSend = False
    return statusSend


def emailSendWhenSubmitCash(subjectEmail, departselect, codenumber):
    statusSend = False
    try:
        deptHeadData = get_approver_frequest_depthead_email(departselect)
        frequestdata = crequest.objects.get(code=codenumber)

        subject, from_email, to = subjectEmail, settings.EMAIL_HOST_USER, deptHeadData[0]
        text_content = 'This is an important message.'
        
        vamount = "Rp{:,.2f}".format(frequestdata.amount)

        html_content = '<div style="text-align:center;">' + '<h2>Requester of Cash Advance Request need your action</h2>' + '<p>No Advance: ' + frequestdata.code + '</p>' + '<p>Name of Requester: ' + frequestdata.requestor + '</p>' + '<p> Department: ' + frequestdata.department.name + '</p>' + '<p> Need Date : ' + str(frequestdata.needdate) + '</p>' + '<p> Amount : ' + str(vamount) +  '</p>' + '<p> Purpose : ' +  frequestdata.purpose + '</p>' + '<a target ="popup" href="https://newemgmt.sinarmeadow.com/cashapproveemailLevel/' + frequestdata.code + '/' + deptHeadData[1]  + '/' + deptHeadData[2] + '/3000/0">' + '<button style="background-color:#dc3545;color:white;border-color: #dc3545;padding: 2%;border-radius: 3px;">Reject</button></a>' + '&nbsp; &nbsp; &nbsp;' + '<a target ="popup" href="https://newemgmt.sinarmeadow.com/cashapproveemailLevel/' + frequestdata.code + '/' + deptHeadData[1] + '/' + deptHeadData[2] +  '/2000/0">'  + '<button style="background-color:#007bff;color:white;border-color: #007bff;padding: 2%;border-radius: 3px;">Accept</button></a>' + '<br><br><br>' + '<small><p>PT. Sinar Meadow International Indonesia</p>' + '<p>Kawasan Industri Pulogadung Blok III.S.20-23 No.3, Jalan Puloayang 2, RW.9, Jatinegara</p>' + '<p>Cakung, Kota Jakarta Timur</p>' + '<p>Daerah Khusus Ibukota Jakarta 13260</p>' + '</div>' 
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        msg.send()


        statusSend = True
    except Exception:
        statusSend = False

    return statusSend

def sendEmailCashWhenApproveApprovalLevel(codenumber, countapproval):
    statusSend = False
    try:
        frequestdata = crequest.objects.get(code=codenumber)

        vamount = "Rp{:,.2f}".format(frequestdata.amount)
        if countapproval == 3 : #LAST APPROVER
            subjectEmail = "Form Cash Advance - " + frequestdata.code
            subject, from_email, to = subjectEmail, settings.EMAIL_HOST_USER, frequestdata.requestorid.email
            text_content = 'This is an important message.'
        
            html_content = '<div style="text-align:center;">' + '<h2>Your Cash Advance Request has been Released!</h2>' + '<p>No Advance: ' + frequestdata.code + '</p>' + '<p>Name of Requester: ' + frequestdata.requestor + '</p>' + '<p> Department: ' + frequestdata.department.name + '</p>' + '<p> Need Date : ' + str(frequestdata.needdate) + '</p>' + '<p> Amount : ' + str(vamount) +  '</p>' + '<p> Purpose : ' +  frequestdata.purpose + '</p>'  + '<br><br><br>' + '<small><p>PT. Sinar Meadow International Indonesia</p>' + '<p>Kawasan Industri Pulogadung Blok III.S.20-23 No.3, Jalan Puloayang 2, RW.9, Jatinegara</p>' + '<p>Cakung, Kota Jakarta Timur</p>' + '<p>Daerah Khusus Ibukota Jakarta 13260</p>' + '</div>' 
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
        else:
            if frequestdata.status == 'APPROVE':
                approver = get_cashapprover(countapproval)
                
                #email to approver 1
                subjectEmail = "Form Cash Advance - " + frequestdata.code
                subject, from_email, to = subjectEmail, settings.EMAIL_HOST_USER, approver[0]
                text_content = 'This is an important message.'
            
                html_content = '<div style="text-align:center;">' + '<h2>Requester of Cash Advance Request need your action</h2>' + '<p>No Advance: ' + frequestdata.code + '</p>' + '<p>Name of Requester: ' + frequestdata.requestor + '</p>' + '<p> Department: ' + frequestdata.department.name + '</p>' + '<p> Need Date : ' + str(frequestdata.needdate) + '</p>' + '<p> Amount : ' + str(vamount) +  '</p>' + '<p> Purpose : ' +  frequestdata.purpose + '</p>' + '<a target ="popup" href="https://newemgmt.sinarmeadow.com/cashapproveemailLevel/' + frequestdata.code + '/' + approver[1]  + '/' + approver[2] + '/3000/' + str(countapproval) + '">' + '<button style="background-color:#dc3545;color:white;border-color: #dc3545;padding: 2%;border-radius: 3px;">Reject</button></a>' + '&nbsp; &nbsp; &nbsp;' + '<a target ="popup" href="https://newemgmt.sinarmeadow.com/cashapproveemailLevel/' + frequestdata.code + '/' + approver[1] + '/' + approver[2] +  '/2000/' + str(countapproval) + '">'  + '<button style="background-color:#007bff;color:white;border-color: #007bff;padding: 2%;border-radius: 3px;">Accept</button></a>' + '<br><br><br>' + '<small><p>PT. Sinar Meadow International Indonesia</p>' + '<p>Kawasan Industri Pulogadung Blok III.S.20-23 No.3, Jalan Puloayang 2, RW.9, Jatinegara</p>' + '<p>Cakung, Kota Jakarta Timur</p>' + '<p>Daerah Khusus Ibukota Jakarta 13260</p>' + '</div>' 
                msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
                msg.attach_alternative(html_content, "text/html")
                msg.send()

                #email to backupapprover 
                subjectEmail = "Form Cash Advance - " + frequestdata.code
                subject, from_email, to = subjectEmail, settings.EMAIL_HOST_USER, approver[3]
                text_content = 'This is an important message.'
            
                html_content = '<div style="text-align:center;">' + '<h2>Requester of Cash Advance Request need your action</h2>' + '<p>No Advance: ' + frequestdata.code + '</p>' + '<p>Name of Requester: ' + frequestdata.requestor + '</p>' + '<p> Department: ' + frequestdata.department.name + '</p>' + '<p> Need Date : ' + str(frequestdata.needdate) + '</p>' + '<p> Amount : ' + str(vamount) +  '</p>' + '<p> Purpose : ' +  frequestdata.purpose + '</p>' + '<a target ="popup" href="https://newemgmt.sinarmeadow.com/cashapproveemailLevel/' + frequestdata.code + '/' + approver[4]  + '/' + approver[5] + '/3000/' + str(countapproval) + '">' + '<button style="background-color:#dc3545;color:white;border-color: #dc3545;padding: 2%;border-radius: 3px;">Reject</button></a>' + '&nbsp; &nbsp; &nbsp;' + '<a target ="popup" href="https://newemgmt.sinarmeadow.com/cashapproveemailLevel/' + frequestdata.code + '/' + approver[4] + '/' + approver[5] +  '/2000/' + str(countapproval) + '">'  + '<button style="background-color:#007bff;color:white;border-color: #007bff;padding: 2%;border-radius: 3px;">Accept</button></a>' + '<br><br><br>' + '<small><p>PT. Sinar Meadow International Indonesia</p>' + '<p>Kawasan Industri Pulogadung Blok III.S.20-23 No.3, Jalan Puloayang 2, RW.9, Jatinegara</p>' + '<p>Cakung, Kota Jakarta Timur</p>' + '<p>Daerah Khusus Ibukota Jakarta 13260</p>' + '</div>' 
                msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
                msg.attach_alternative(html_content, "text/html")
                msg.send()
            else :       
                subjectEmail = "Form Cash Advance - " + frequestdata.code
                subject, from_email, to = subjectEmail, settings.EMAIL_HOST_USER, frequestdata.requestorid.email
                text_content = 'This is an important message.'
            
                html_content = '<div style="text-align:center;">' + '<h2>Your Cash Advance Request has been Rejected</h2>' + '<p>No Advance: ' + frequestdata.code + '</p>' + '<p>Name of Requester: ' + frequestdata.requestor + '</p>' + '<p> Department: ' + frequestdata.department.name + '</p>' + '<p> Need Date : ' + str(frequestdata.needdate) + '</p>' + '<p> Amount : ' + str(vamount) +  '</p>' + '<p> Purpose : ' +  frequestdata.purpose + '</p>'  + '<br><br><br>' + '<small><p>PT. Sinar Meadow International Indonesia</p>' + '<p>Kawasan Industri Pulogadung Blok III.S.20-23 No.3, Jalan Puloayang 2, RW.9, Jatinegara</p>' + '<p>Cakung, Kota Jakarta Timur</p>' + '<p>Daerah Khusus Ibukota Jakarta 13260</p>' + '</div>' 
                msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
                msg.attach_alternative(html_content, "text/html")
                msg.send()

        statusSend = True
    except Exception:
        statusSend = False

    return statusSend

def get_cashapprover(inputapproverorder):
    cashapprovers=cashapprover.objects.get(approverorder=inputapproverorder)

    approverData = [] 
    approverData.append(cashapprovers.approver.email)
    approverData.append(str(cashapprovers.approver_id)) 
    approverData.append(str(cashapprovers.approver.departments.all().last().id))
   
    approverData.append(cashapprovers.backupapprover.email)
    approverData.append(str(cashapprovers.backupapprover_id)) 
    approverData.append(str(cashapprovers.backupapprover.departments.all().last().id))

    return approverData

def testlogic(codenumber):

    frequestdata = crequest.objects.get(code=codenumber)
    print(frequestdata.requestorid.email)
    return print(frequestdata.requestorid.email)