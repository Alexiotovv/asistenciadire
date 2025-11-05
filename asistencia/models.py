from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator
from django.utils import timezone

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('personal', 'Personal'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='personal')
    dni = models.CharField(max_length=12, unique=True, null=True, blank=True)
    nombre_completo = models.CharField(max_length=100, blank=True)
    oficina = models.CharField(max_length=100, blank=True)
    clave_pin = models.CharField(
        max_length=4,
        validators=[MinLengthValidator(4)],
        help_text="PIN de 4 dígitos numéricos",
        blank=False,
        null=False,
        default="0000"
    )

    def __str__(self):
        return f"{self.nombre_completo} ({self.dni})"

class Marcacion(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha = models.DateField(default=timezone.now)
    hora = models.TimeField(default=timezone.now)
    tipo = models.CharField(max_length=10, choices=[('entrada', 'Entrada'), ('salida', 'Salida')])

    class Meta:
        ordering = ['-fecha', '-hora']
        unique_together = [('usuario', 'fecha', 'tipo')]  # Evita duplicados