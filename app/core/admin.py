from django.contrib import admin
from .models import User, Recipe, Tag, Ingredient

class UserAdmin(admin.ModelAdmin):
    search_fields = ('email', 'name')
    ordering = ('id',)

admin.site.register(User, UserAdmin)
admin.site.register(Recipe)
admin.site.register(Tag)
admin.site.register(Ingredient)