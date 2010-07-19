from django.contrib import admin

import models

class ShortenedAdmin(admin.ModelAdmin):
    list_display = ('description', 'count', 'key', 'url', )
    list_filter = ('description',)
    search_fields = ('url','description',)

admin.site.register(models.Shortened, ShortenedAdmin)
