from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Marcacion

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('username', 'dni', 'nombre_completo', 'oficina', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),('Información Personal', {'fields': ('dni', 'nombre_completo', 'oficina', 'role','clave_pin')}),('Permisos', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'dni', 'nombre_completo', 'oficina', 'role', 'clave_pin','password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('dni', 'nombre_completo', 'username')
    ordering = ('dni',)

admin.site.register(User, CustomUserAdmin)
admin.site.register(Marcacion)