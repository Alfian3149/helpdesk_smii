from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'), 
    path('sendmail', views.test_send_mail, name='test_send_mail'),
    path('resendmail', views.resend_mail, name='resend_mail'),
    path('crf', views.crf, name='crf'),
    path('submitmiscrf', views.submitmiscrf, name='submitmiscrf'),
    path('crfview/<int:id>/<int:action>', views.crfview, name='crfview'),
    path('crfapproveemailDeptHead/<str:codenumber>/<int:empid>/<int:departid>/<int:action>', views.crfapproveemailDeptHead, name='crfapproveemailDeptHead'),

    path('deptemployeeviews', views.deptemployeeviews, name='deptemployeeviews'),
    path('srf', views.srf, name='srf'),
    path('submitsrfdetail', views.submitsrfdetail, name='submitsrfdetail'),
    path('srfview/<int:id>/<int:action>', views.srfview, name='srfview'),

    path('prf', views.prf, name='prf'),
    path('prfview/<int:id>/<int:action>', views.prfview, name='prfview'),
    path('submitprfdetail', views.submitprfdetail, name='submitprfdetail'),
   path('prfapproveemailDeptHead/<str:codenumber>/<int:empid>/<int:departid>/<int:action>', views.prfapproveemailDeptHead, name='prfapproveemailDeptHead'),
   path('prfapproveemailGenMGR/<str:codenumber>/<int:empid>/<int:departid>/<int:action>', views.prfapproveemailGenMGR, name='prfapproveemailGenMGR'),

    path('listrequest', views.listrequest, name='listrequest'),
    path('requestreport', views.requestreport, name='requestreport'),
    path('historyrequest', views.historyrequest, name='historyrequest'),
    path('independen', views.independen, name='independen'),

    path('cash', views.cash, name='cash'),
    path('listcash', views.listcash, name='listcash'),
    path('historycash', views.historycash, name='historycash'),
    path('cashreport', views.cashreport, name='cashreport'),
    
    path('cashview/<int:id>/<int:action>', views.cashview, name='cashview'),
    path('cashApprovalAtList/<int:id>/<int:action>', views.cashApprovalAtList, name='cashApprovalAtList'),
    path('submitcash', views.submitcash, name='submitcash'),
    path('cashapproveemailLevel/<str:codenumber>/<int:empid>/<int:departid>/<int:action>/<int:countapproval>', views.cashapproveemailLevel, name='cashapproveemailLevel'),

    path('detailcashadv', views.dthistcashadv, name='dthistcashadv'),
    path('loginPage', views.loginPage, name='loginPage'),
    path('userProfile', views.userProfile, name='userProfile'),
    path('frequest_list', views.frequest_list, name='frequest_list'),
    path('submitcrf', views.submitcrf, name='submitcrf'),
    path('submitsrf', views.submitsrf, name='submitsrf'),
    path('submitprf', views.submitprf, name='submitprf'),

    path('loginAuth', views.loginAuth, name='loginAuth'),
    path('logoutPage', views.logoutPage, name='logoutPage'),
    path('resetPassword', views.resetPassword, name='resetPassword'),
    path('changepassword', views.changepassword, name='changepassword'),
    path('test', views.test, name='test'),
    path('get-topics-ajax/', views.get_topics_ajax, name='get_topics_ajax'),
    path('get_employee_department_ajax/', views.get_employee_department_ajax, name='get_employee_department_ajax'),



] 