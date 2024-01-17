from django.contrib import admin
from .models import UserDetail, Procedure, Folder, Shift, FolderProcedure, Record

admin.site.register(UserDetail)
admin.site.register(Procedure)
admin.site.register(Folder)
admin.site.register(FolderProcedure)
admin.site.register(Shift)
admin.site.register(Record)