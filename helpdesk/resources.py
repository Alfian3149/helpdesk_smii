from import_export import resources
from helpdesk.models import item,position,department, employee

from django.contrib.auth.models import User

class ItemResources(resources.ModelResource):
    class Meta:
        model = item

class PositionResources(resources.ModelResource):
    class Meta:
        model = position

class DepartmentResources(resources.ModelResource):
    class Meta:
        model = department

class EmployeeResources(resources.ModelResource):
    class Meta:
        model = employee

class UserResources(resources.ModelResource):
    class Meta:
        model = User