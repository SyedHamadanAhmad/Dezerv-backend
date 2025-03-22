from django.contrib import admin

# Register your models here.
from .models import Group, UserGroup, Transaction, StockData, AppUser

admin.site.register(Group)
admin.site.register(UserGroup)
admin.site.register(Transaction)
admin.site.register(AppUser)
admin.site.register(StockData)




