from django.contrib import admin
from search.models import *
# Register your models here.
admin.site.register(SavedSearch)
admin.site.register(SearchGroup)
admin.site.register(SearchRow)
admin.site.register(SearchFieldCache)
