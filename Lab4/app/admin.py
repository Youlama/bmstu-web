from django.contrib import admin

from .models import *

admin.site.register(Document)
admin.site.register(Request)
admin.site.register(DocumentRequest)
