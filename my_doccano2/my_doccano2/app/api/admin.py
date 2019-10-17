from django.contrib import admin

# Register your models here.
from .models import *


class UserAdmin(admin.ModelAdmin):
    fields = ["username", "last_login", "is_superuser", "date_joined"]


admin.site.register(User, UserAdmin)
