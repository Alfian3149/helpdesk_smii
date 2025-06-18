from datetime import datetime, timedelta
from .models import crequest, department, employee, frequest, item, approvalfrhistory,frequestdetail,position,approvalcrhistory, cashapprover, logemail
from django.db.models import Q
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.core import mail
from django.conf import settings
import traceback
webhost = 'https://emgmt.sinarmeadow.com/'

 
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
    
def sendEmailCashWhenApproveApprovalLevel(codenumber, countapproval):
    statusSend = False
    try:
        frequestdata = crequest.objects.get(code=codenumber)

        vamount = "Rp{:,.2f}".format(frequestdata.amount)
        if countapproval == 3 : #LAST APPROVER
            subjectEmail = "Form Cash Advance - " + frequestdata.code
            subject, from_email, to = subjectEmail, subjectEmail + settings.EMAIL_FROM, frequestdata.requestorid.email
            text_content = 'This is an important message.'
        
            html_content = '<div style="text-align:center;">' + '<h2>Your Cash Advance Request has been ' + frequestdata.status + '</h2>' + '<p>No Advance: ' + frequestdata.code + '</p>' + '<p>Name of Requester: ' + frequestdata.requestor + '</p>' + '<p> Department: ' + frequestdata.department.name + '</p>' + '<p> Need Date : ' + str(frequestdata.needdate) + '</p>' + '<p> Amount : ' + str(vamount) +  '</p>' + '<p> Purpose : ' +  frequestdata.purpose + '</p>'  + '<br><br><br>' + settings.COMPANY_ADDRESS + '</div>' 
            
            try:
                msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
                msg.attach_alternative(html_content, "text/html")
                msg.send()
            except Exception:
                messagesTraceback = 'countapproval:' + str(countapproval)
                resendMaterial = subject + ";" + from_email + ";" + to + ";" + html_content
                isCreateLog = createLogEmail(codenumber, resendMaterial, messagesTraceback, 129)                    
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
                
                try:
                    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
                    msg.attach_alternative(html_content, "text/html")
                    msg.send()
                except Exception:
                    messagesTraceback = 'countapproval:' + str(countapproval)
                    resendMaterial = subject + ";" + from_email + ";" + to + ";" + html_content
                    isCreateLog = createLogEmail(codenumber, resendMaterial, messagesTraceback, 129)                    

                #email to backupapprover 
                '''  
                if len(approver[3]) > 0 :
                    subjectEmail = "Form Cash Advance - " + frequestdata.code
                    subject, from_email, to = subjectEmail, subjectEmail + settings.EMAIL_FROM, approver[3]
                    text_content = 'This is an important message.'
                
                    if countapproval == 2:
                        html_content = '<div style="text-align:center;">' + '<h2>Requester of Cash Advance Request need your action</h2>' + '<p>No Advance: ' + frequestdata.code + '</p>' + '<p>Name of Requester: ' + frequestdata.requestor + '</p>' + '<p> Department: ' + frequestdata.department.name + '</p>' + '<p> Need Date : ' + str(frequestdata.needdate) + '</p>' + '<p> Amount : ' + str(vamount) +  '</p>' + '<p> Purpose : ' +  frequestdata.purpose + '</p><br>' + '<a target ="popup" href="' + webhost + 'cashapproveemailLevel/' + frequestdata.code + '/' + approver[1]  + '/' + approver[2] + '/3000/' + str(countapproval) + '">' + '<button style="background-color:#dc3545;color:white;border-color: #dc3545;padding: 2%;border-radius: 3px;">Reject</button></a>' + '&nbsp; &nbsp; &nbsp;' + '<a target ="popup" href="' + webhost + 'cashapproveemailLevel/' + frequestdata.code + '/' + approver[1] + '/' + approver[2] +  '/2000/' + str(countapproval) + '">'  + '<button style="background-color:#007bff;color:white;border-color: #007bff;padding: 2%;border-radius: 3px;">Accept</button></a>' + '<br><br><br>' + settings.COMPANY_ADDRESS + '</div>' 
                    else: 
                        html_content = '<div style="text-align:center;">' + '<h2>Requester of Cash Advance Request need your action</h2>' + '<p>No Advance: ' + frequestdata.code + '</p>' + '<p>Name of Requester: ' + frequestdata.requestor + '</p>' + '<p> Department: ' + frequestdata.department.name + '</p>' + '<p> Need Date : ' + str(frequestdata.needdate) + '</p>' + '<p> Amount : ' + str(vamount) +  '</p>' + '<p> Purpose : ' +  frequestdata.purpose + '</p><br>' + '<a target ="popup" href="' + webhost + 'cashapproveemailLevel/' + frequestdata.code + '/' + approver[1]  + '/' + approver[2] + '/3000/' + str(countapproval) + '">' + '<button style="background-color:#dc3545;color:white;border-color: #dc3545;padding: 2%;border-radius: 3px;">Reject</button></a>' + '&nbsp; &nbsp; &nbsp;' + '<a target ="popup" href="' + webhost + 'cashapproveemailLevel/' + frequestdata.code + '/' + approver[1] + '/' + approver[2] +  '/2000/' + str(countapproval) + '">'  + '<button style="background-color:#007bff;color:white;border-color: #007bff;padding: 2%;border-radius: 3px;">Accept</button></a>' + '<br><br><br>' + settings.COMPANY_ADDRESS + '</div>' 
                    
                    try:
                        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
                        msg.attach_alternative(html_content, "text/html")
                        msg.send()
                        
                        statusSend =  True
                    except Exception:
                        messagesTraceback = 'countapproval:' + str(countapproval)
                        resendMaterial = subject + ";" + from_email + ";" + to + ";" + html_content
                        isCreateLog = createLogEmail(codenumber, resendMaterial, messagesTraceback, 129)   
                 '''
    
            else :       
                subjectEmail = "Form Cash Advance - " + frequestdata.code
                subject, from_email, to = subjectEmail, subjectEmail + settings.EMAIL_FROM, frequestdata.requestorid.email
                text_content = 'This is an important message.'
            
                html_content = '<div style="text-align:center;">' + '<h2>Your Cash Advance Request has been Rejected</h2>' + '<p>No Advance: ' + frequestdata.code + '</p>' + '<p>Name of Requester: ' + frequestdata.requestor + '</p>' + '<p> Department: ' + frequestdata.department.name + '</p>' + '<p> Need Date : ' + str(frequestdata.needdate) + '</p>' + '<p> Amount : ' + str(vamount) +  '</p>' + '<p> Purpose : ' +  frequestdata.purpose + '</p>'  + '<br><br><br>' + settings.COMPANY_ADDRESS + '</div>' 

                try:
                    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
                    msg.attach_alternative(html_content, "text/html")
                    msg.send()
                except Exception:
                    messagesTraceback = 'countapproval:' + str(countapproval)
                    resendMaterial = subject + ";" + from_email + ";" + to + ";" + html_content
                    isCreateLog = createLogEmail(codenumber, resendMaterial, messagesTraceback, 129)                    
                    
        statusSend = True
    except Exception:
        statusSend = False

    return statusSend