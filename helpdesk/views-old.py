from django.shortcuts import render

from django.http import HttpResponse
from .models import employee

def index(request):
    employees = employee.objects.all()
    return render(request, 'helpdesk/test.html', {'employees': employees})

