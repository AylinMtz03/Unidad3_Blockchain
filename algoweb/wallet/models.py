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
    

class Contacto(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.EmailField()
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    contact_wallet = models.CharField(max_length=58, blank=True, null=True)
    def __str__(self):
        return f"Contacto: {self.nombre} ({self.wallet.user.username})"