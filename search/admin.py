from django.contrib import admin
from search.models import *


class SearchGroupInline(admin.StackedInline):
    model = SearchGroup
    extra = 0


class SearchRowInline(admin.StackedInline):
    model = SearchRow
    extra = 0


class SavedSearchAdmin(admin.ModelAdmin):
    inlines = [SearchGroupInline,]
    list_display = ('name', 'created_by', 'created', 'save_search')
    list_filter = ('created', 'save_search')
    date_hierarchy = 'created'
    search_fields = ('name', 'created_by')


class SearchGroupAdmin(admin.ModelAdmin):
    inlines = [SearchRowInline]
    list_display = ('id', 'saved_search', 'and_or', 'position')


class SearchRowAdmin(admin.ModelAdmin):
    list_display = ('search_models', 'search_field', 'and_or', 'operator', 'search_term',
                    'position')


admin.site.register(SavedSearch, SavedSearchAdmin)
admin.site.register(SearchGroup, SearchGroupAdmin)
admin.site.register(SearchRow, SearchRowAdmin)
admin.site.register(SearchFieldCache)
admin.site.register(SearchCache)
