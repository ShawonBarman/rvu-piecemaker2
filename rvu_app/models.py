from django.db import models
from django.contrib.auth.models import User

class UserDetail(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=False)
    def __str__(self):
        return self.user.username
    
class Procedure(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    cpt = models.CharField(max_length=5, null=True, blank=True)
    modality = models.CharField(max_length=2, choices=[('CR', 'CR'), ('CT', 'CT'), ('MG', 'MG'), ('MR', 'MR'), ('NM', 'NM'), ('OT', 'OT'), ('PT', 'PT'), ('US', 'US')], null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    rvu = models.DecimalField(max_digits=5, decimal_places=2, null=True)

class Folder(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.IntegerField(null=True, blank=True)
    
class Shift(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.IntegerField(null=True, blank=True)
    
class FolderProcedure(models.Model):
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE)
    procedure = models.ForeignKey(Procedure, on_delete=models.CASCADE)
    order = models.IntegerField(null=True, blank=True)
    
class Record(models.Model):
    created_at = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, blank=True)
    procedure = models.ForeignKey(Procedure, on_delete=models.SET_NULL, null=True, blank=True)