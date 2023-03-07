import uuid

from django.db import models


class EmployeeManager(models.Manager):
    pass


class Employee(models.Model):
    objects = EmployeeManager()
    name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    fathers_name = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)
    department = models.CharField(max_length=50)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
