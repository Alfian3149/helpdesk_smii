import django_filters

from helpdesk.models import frequest,crequest

class frequestFilter(django_filters.FilterSet):

    class Meta:
        model = frequest
        fields = {
            'employee':['exact'],
            'department':['exact'],
            'submitted':['range'],
            'type':['exact'],
        }
 
class crequestFilter(django_filters.FilterSet):

    class Meta:
        model = crequest
        fields = {
            'employee':['exact'],
            'deptuser':['exact'],
            'datecreated':['range'],
            'requestorid':['exact'],
            'department':['exact'],
            'amount':['range'],
        }
