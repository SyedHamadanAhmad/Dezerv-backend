from django.contrib import admin

# Register your models here.
from .models import Group, UserGroup, Transaction

admin.site.register(Group)
admin.site.register(UserGroup)
admin.site.register(Transaction)


