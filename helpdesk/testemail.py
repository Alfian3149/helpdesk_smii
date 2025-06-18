from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from helpdesk.models import crequest, department, employee, frequest, item, approvalfrhistory,frequestdetail,position,approvalcrhistory, cashapprover

frequests = frequest.objects.get(code="CRF-20230130-001")

if frequests.type == "CRF":
    itemDisplay = 'Barang: ' + frequests.item.item_name 
    subjectDisplay = 'Consumable Request Forms (CRF) : '
    bodyEmailDisplay = 'Consumable Request'
elif frequests.type == "SRF":
    itemDisplay = 'DESCRIPTION: ' + frequests.description
    subjectDisplay = 'Service Request Forms (SRF) - '
    bodyEmailDisplay = 'Service Request'

#emailMISTeamArray = get_email_allMIS(True)
#emailMISTeamArray = ['andika.suhendar@smii.co.id', 'edie.hirman@smii.co.id', 'samuel.christoper@smii.co.id']
#emailMISTeamArray = ['alfianpical3149@gmail.com', 'alfian@lukubara.com', 'developmenttrikarya3149@gmail.com']
emailMISTeamArray = ['alfianpical3149@gmail.com']

for emailReceiver in emailMISTeamArray: 
    subject, from_email, to = subjectDisplay + frequests.code, subjectDisplay + settings.EMAIL_FROM, emailReceiver
    text_content = 'This is an important message.'
    html_content = '<div style="text-align:center;"><h2>Requester ' + bodyEmailDisplay +  ' Need Your Action' + '</h2>' + '<p>Nomor Request: ' + frequests.code + '</p>' + '<p>Requester: ' + frequests.employee.name + '</p>' + '<p> Department: ' + frequests.department.name + '</p>' + '<p>' + itemDisplay + '</p><br>' +'<br><br><br>' + '<small><p>PT. Sinar Meadow International Indonesia</p>' + '<p>Kawasan Industri Pulogadung Blok III.S.20-23 No.3, Jalan Puloayang 2, RW.9, Jatinegara</p>' + '<p>Cakung, Kota Jakarta Timur</p>' + '<p>Daerah Khusus Ibukota Jakarta 13260</p>' + '</div>' 
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, "text/html")
    msg.send()