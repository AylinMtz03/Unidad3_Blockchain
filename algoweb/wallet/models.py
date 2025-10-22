from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.CharField(max_length=58)  
    private_key = models.TextField() 

    def __str__(self):
        return f"Wallet de {self.user.username}"