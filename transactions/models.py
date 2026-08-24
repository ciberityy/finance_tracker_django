from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=200,)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Transaction(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_time = models.DateTimeField(default=timezone.now)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)
    description = models.CharField(max_length=100, default='', blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    

    def __str__(self):
        if self.category: 
            return f"{self.date_time.date()}: {self.category.name} - {self.amount}"
        else: 
            return "Unknown"
