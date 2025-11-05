from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Min, Max
from openpyxl import Workbook
from .models import User, Marcacion
from datetime import datetime, timedelta
from django.utils import timezone as dj_timezone

# === VISTAS PÚBLICAS ===

def marcacion_publica(request):
    """Interfaz pública de marcación (sin login)"""
    return render(request, 'asistencia/marcacion_publica.html', {'now': datetime.now()})


def marcar_asistencia(request):
    if request.method == 'POST':
        dni = request.POST.get('dni', '').strip()
        pin = request.POST.get('pin', '').strip()

        if not dni or not pin:
            return JsonResponse({'success': False, 'error': 'DNI y PIN son obligatorios.'})

        if not pin.isdigit() or len(pin) != 4:
            return JsonResponse({'success': False, 'error': 'El PIN debe ser numérico de 4 dígitos.'})

        try:
            usuario = User.objects.get(dni=dni, clave_pin=pin, role='personal')
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'DNI o PIN incorrectos.'})

        ahora = datetime.now()
        hoy = ahora.date()
        hora_actual = ahora.time()

        # Verificar marcaciones de hoy
        marcaciones_hoy = Marcacion.objects.filter(usuario=usuario, fecha=hoy)

        entrada_hoy = marcaciones_hoy.filter(tipo='entrada').first()
        salida_hoy = marcaciones_hoy.filter(tipo='salida').first()

        # Regla 1: Si ya tiene entrada y salida → no permitir más
        if entrada_hoy and salida_hoy:
            return JsonResponse({'success': False, 'error': 'Ya registró entrada y salida hoy.'})

        # Regla 2: Si ya tiene entrada → solo permitir salida
        if entrada_hoy:
            # Validar que no intente marcar entrada de nuevo
            if entrada_hoy.hora:
                # Opcional: evitar salida inmediata (menos de 1 minuto)
                entrada_dt = datetime.combine(hoy, entrada_hoy.hora)
                if ahora - entrada_dt < timedelta(minutes=1):
                    return JsonResponse({'success': False, 'error': 'Debe esperar al menos 1 minuto para marcar salida.'})
            # Registrar salida
            Marcacion.objects.create(usuario=usuario, fecha=hoy, hora=hora_actual, tipo='salida')
            return JsonResponse({
                'success': True,
                'nombre': usuario.nombre_completo,
                'hora': ahora.strftime('%H:%M:%S'),
                'tipo': 'salida'
            })

        # Regla 3: Si no tiene entrada → registrar entrada
        # Opcional: evitar entrada duplicada en menos de 10 minutos (aunque unique_together lo evita)
        ultima_entrada = Marcacion.objects.filter(
            usuario=usuario,
            tipo='entrada',
            fecha=hoy
        ).order_by('-hora').first()

        if ultima_entrada:
            # Esto no debería ocurrir por unique_together, pero por seguridad:
            return JsonResponse({'success': False, 'error': 'Ya registró su entrada hoy.'})

        # Registrar entrada
        Marcacion.objects.create(usuario=usuario, fecha=hoy, hora=hora_actual, tipo='entrada')
        return JsonResponse({
            'success': True,
            'nombre': usuario.nombre_completo,
            'hora': ahora.strftime('%H:%M:%S'),
            'tipo': 'entrada'
        })

    return JsonResponse({'success': False, 'error': 'Método no permitido.'})


# === VISTAS PROTEGIDAS ===

@login_required
def dashboard(request):
    """Dashboard para usuarios autenticados (admin o personal)"""
    return render(request, 'asistencia/dashboard.html', {'now': datetime.now()})


@login_required
def exportar_excel(request):
    """Solo accesible desde el dashboard por admin"""
    if request.user.role != 'admin':
        return HttpResponse("Acceso denegado", status=403)

    from datetime import date
    mes = int(request.GET.get('mes', datetime.now().month))
    anio = int(request.GET.get('anio', datetime.now().year))

    # Validar mes y año
    try:
        date(anio, mes, 1)
    except ValueError:
        return HttpResponse("Fecha inválida", status=400)

    usuarios = User.objects.filter(role='personal')
    dias_mes = []
    for d in range(1, 32):
        try:
            dias_mes.append(date(anio, mes, d))
        except ValueError:
            break

    wb = Workbook()
    ws = wb.active
    ws.title = f"Asistencias {anio}-{mes:02d}"

    ws.append(['DNI', 'Nombre Completo', 'Oficina'] + [f"Día {d.day}" for d in dias_mes])

    for usuario in usuarios:
        fila = [usuario.dni, usuario.nombre_completo, usuario.oficina]
        for dia in dias_mes:
            marcaciones = Marcacion.objects.filter(usuario=usuario, fecha=dia).order_by('hora')
            entrada = marcaciones.filter(tipo='entrada').first()
            salida = marcaciones.filter(tipo='salida').first()
            texto = ""
            if entrada:
                texto += f"E:{entrada.hora.strftime('%H:%M')}"
            if salida:
                texto += f" S:{salida.hora.strftime('%H:%M')}"
            fila.append(texto if texto else "")
        ws.append(fila)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=asistencias_{anio}_{mes:02d}.xlsx'
    wb.save(response)
    return response