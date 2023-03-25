import uuid

from django.db import models


class EmployeeManager(models.Manager):
    pass


class AttendanceManager(models.Manager):
    pass


class Employee(models.Model):
    objects = EmployeeManager()
    name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    patronymic = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)
    department = models.CharField(max_length=50)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class Attendance(models.Model):
    objects = AttendanceManager()
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.employee} - {self.date}'
