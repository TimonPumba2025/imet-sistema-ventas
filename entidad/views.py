from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required,permission_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_http_methods

from django.http import HttpResponse, JsonResponse
from entidad.forms import *

from entidad.models import *

from django.utils import timezone
import json
from decimal import Decimal

from django.db.models import Q


from django.contrib import messages
from django.db.models import Sum, Count
from django.db.models.functions import Coalesce
from django.core.serializers.json import DjangoJSONEncoder

from xhtml2pdf import pisa
from django.template.loader import render_to_string

from django.contrib.auth.forms import SetPasswordForm, PasswordChangeForm

import shutil
import os

from PIL import Image, ImageDraw, ImageFont
import barcode
from barcode.writer import ImageWriter


from pathlib import Path
import requests
from django.conf import settings
from io import BytesIO

import base64


import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont


from django.db.models import Sum, Avg, Count
from django.db.models.functions import TruncMonth, TruncYear
from datetime import datetime, timedelta
from decimal import Decimal



from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncWeek, TruncDay, TruncMonth
from datetime import datetime, timedelta
from django.utils import timezone

# Importar tus modelos (ajusta según tu estructura)
from .models import Sucursal, Venta, Caja, Producto, Cliente, DetalleVenta, DetalleVentaXProducto

from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods


from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from datetime import datetime
from django.utils import timezone

from django.contrib.auth.models import User


#LOGIN 

from django.contrib.auth import authenticate, login, logout

from django.contrib.auth.models import User

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def mi_error_404(request, exception):
    return render(request, '404.html', status=404)

def home(request):
    sucursal_id = request.session.get('sucursal_id')

    if not sucursal_id:
        return redirect('elegir_sucursal')

    sucursal = Sucursal.objects.get(id=sucursal_id)
    if sucursal.id == 1 or 'primera' in sucursal.nombre.lower():
        sucursal.nombre = "Timón y Pumba"
    elif sucursal.id == 2 or 'segunda' in sucursal.nombre.lower():
        sucursal.nombre = "Olor a Viernes"
    
    # Obtener datos rápidos para el dashboard
    hoy = datetime.now().date()
    inicio_mes = datetime(hoy.year, hoy.month, 1)
    
    # Ventas del mes actual
    ventas_mes = Venta.objects.filter(
        caja__sucursal_id=sucursal_id,
        fecha__gte=inicio_mes
    ).count()
    
    # Caja activa
    caja_activa = Caja.objects.filter(
        sucursal_id=sucursal_id,
        activo=True
    ).first()
    
    # Total de productos en inventario
    total_productos = Producto.objects.filter(activo=True).count()
    
    # Total de clientes
    total_clientes = Cliente.objects.filter(activo=True).count()
    
    context = {
        'sucursal': sucursal,
        'ventas_mes': ventas_mes,
        'caja_activa': caja_activa,
        'total_productos': total_productos,
        'total_clientes': total_clientes,
    }
    
    return render(request, 'home.html', context)


@login_required
def kpis_dashboard(request):
    """API endpoint para obtener los KPIs del dashboard"""
    try:
        sucursal_id = request.session.get('sucursal_id')
        
        if not sucursal_id:
            return JsonResponse({'error': 'No hay sucursal seleccionada'}, status=400)
        
        # Fechas para comparación
        ahora = datetime.now()
        inicio_año_actual = datetime(ahora.year, 1, 1)
        inicio_año_anterior = datetime(ahora.year - 1, 1, 1)
        fin_año_anterior = datetime(ahora.year - 1, 12, 31, 23, 59, 59)
        
        # Obtener todas las ventas de la sucursal para debug
        total_ventas = Venta.objects.filter(caja__sucursal_id=sucursal_id).count()
        print(f"Total ventas en sucursal {sucursal_id}: {total_ventas}")
        
        # KPI 1: Total ingresos anuales
        ingresos_actuales = Venta.objects.filter(
            caja__sucursal_id=sucursal_id,
            fecha__gte=inicio_año_actual
        ).aggregate(total=Sum('total'))['total']
        ingresos_actuales = float(ingresos_actuales) if ingresos_actuales else 0
        
        ingresos_anteriores = Venta.objects.filter(
            caja__sucursal_id=sucursal_id,
            fecha__gte=inicio_año_anterior,
            fecha__lte=fin_año_anterior
        ).aggregate(total=Sum('total'))['total']
        ingresos_anteriores = float(ingresos_anteriores) if ingresos_anteriores else 0
        
        # Calcular cambio porcentual
        if ingresos_anteriores > 0:
            cambio_ingresos = ((ingresos_actuales - ingresos_anteriores) / ingresos_anteriores) * 100
        else:
            cambio_ingresos = 100 if ingresos_actuales > 0 else 0
        
        # KPI 2: Promedio de venta
        promedio_actual = Venta.objects.filter(
            caja__sucursal_id=sucursal_id,
            fecha__gte=inicio_año_actual
        ).aggregate(promedio=Avg('total'))['promedio']
        promedio_actual = float(promedio_actual) if promedio_actual else 0
        
        promedio_anterior = Venta.objects.filter(
            caja__sucursal_id=sucursal_id,
            fecha__gte=inicio_año_anterior,
            fecha__lte=fin_año_anterior
        ).aggregate(promedio=Avg('total'))['promedio']
        promedio_anterior = float(promedio_anterior) if promedio_anterior else 0
        
        if promedio_anterior > 0:
            cambio_promedio = ((promedio_actual - promedio_anterior) / promedio_anterior) * 100
        else:
            cambio_promedio = 100 if promedio_actual > 0 else 0
        
        # KPI 3: Total de ventas (cantidad de transacciones)
        ventas_actuales = Venta.objects.filter(
            caja__sucursal_id=sucursal_id,
            fecha__gte=inicio_año_actual
        ).count()
        
        ventas_anteriores = Venta.objects.filter(
            caja__sucursal_id=sucursal_id,
            fecha__gte=inicio_año_anterior,
            fecha__lte=fin_año_anterior
        ).count()
        
        if ventas_anteriores > 0:
            cambio_ventas = ((ventas_actuales - ventas_anteriores) / ventas_anteriores) * 100
        else:
            cambio_ventas = 100 if ventas_actuales > 0 else 0
        
        # KPI 4: Total productos vendidos (suma de cantidades)
        # Primero intentar con DetalleVentaXProducto
        productos_actuales = DetalleVentaXProducto.objects.filter(
            detalle_venta__venta__caja__sucursal_id=sucursal_id,
            detalle_venta__venta__fecha__gte=inicio_año_actual
        ).aggregate(total=Sum('cantidad'))['total']
        productos_actuales = productos_actuales if productos_actuales else 0
        
        productos_anteriores = DetalleVentaXProducto.objects.filter(
            detalle_venta__venta__caja__sucursal_id=sucursal_id,
            detalle_venta__venta__fecha__gte=inicio_año_anterior,
            detalle_venta__venta__fecha__lte=fin_año_anterior
        ).aggregate(total=Sum('cantidad'))['total']
        productos_anteriores = productos_anteriores if productos_anteriores else 0
        
        # Si no hay datos en DetalleVentaXProducto, usar DetalleVenta
        if productos_actuales == 0:
            productos_actuales = DetalleVenta.objects.filter(
                venta__caja__sucursal_id=sucursal_id,
                venta__fecha__gte=inicio_año_actual
            ).aggregate(total=Sum('cantidad'))['total']
            productos_actuales = productos_actuales if productos_actuales else 0
            
            productos_anteriores = DetalleVenta.objects.filter(
                venta__caja__sucursal_id=sucursal_id,
                venta__fecha__gte=inicio_año_anterior,
                venta__fecha__lte=fin_año_anterior
            ).aggregate(total=Sum('cantidad'))['total']
            productos_anteriores = productos_anteriores if productos_anteriores else 0
        
        if productos_anteriores > 0:
            cambio_productos = ((productos_actuales - productos_anteriores) / productos_anteriores) * 100
        else:
            cambio_productos = 100 if productos_actuales > 0 else 0
        
        print(f"Ingresos actuales: {ingresos_actuales}, anteriores: {ingresos_anteriores}")
        print(f"Promedio actual: {promedio_actual}, anterior: {promedio_anterior}")
        print(f"Ventas actuales: {ventas_actuales}, anteriores: {ventas_anteriores}")
        print(f"Productos actuales: {productos_actuales}, anteriores: {productos_anteriores}")
        
        return JsonResponse({
            'ingresos_anuales': {
                'valor': ingresos_actuales,
                'cambio': round(cambio_ingresos, 1),
                'anterior': ingresos_anteriores
            },
            'promedio_venta': {
                'valor': promedio_actual,
                'cambio': round(cambio_promedio, 1),
                'anterior': promedio_anterior
            },
            'total_ventas': {
                'valor': ventas_actuales,
                'cambio': round(cambio_ventas, 1),
                'anterior': ventas_anteriores
            },
            'productos_vendidos': {
                'valor': productos_actuales,
                'cambio': round(cambio_productos, 1),
                'anterior': productos_anteriores
            }
        })
        
    except Exception as e:
        print(f"Error en kpis_dashboard: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def datos_grafico_mensual(request):
    """API endpoint para obtener datos del gráfico mensual de ventas"""
    try:
        sucursal_id = request.session.get('sucursal_id')
        
        if not sucursal_id:
            return JsonResponse({'error': 'No hay sucursal seleccionada'}, status=400)
        
        # Obtener ventas de los últimos 12 meses
        fecha_limite = datetime.now() - timedelta(days=365)
        
        ventas_mensuales = (
            Venta.objects.filter(
                caja__sucursal_id=sucursal_id,
                fecha__gte=fecha_limite
            )
            .annotate(mes=TruncMonth('fecha'))
            .values('mes')
            .annotate(
                total_ventas=Sum('total'),
                cantidad_ventas=Count('id')
            )
            .order_by('mes')
        )
        
        print(f"Ventas mensuales encontradas: {ventas_mensuales.count()}")
        
        # Formatear datos para Chart.js
        labels = []
        datos_ventas = []
        datos_cantidad = []
        
        for venta in ventas_mensuales:
            mes_nombre = venta['mes'].strftime('%b %Y')
            labels.append(mes_nombre)
            datos_ventas.append(float(venta['total_ventas'] or 0))
            datos_cantidad.append(venta['cantidad_ventas'])
            print(f"Mes: {mes_nombre}, Total: {venta['total_ventas']}, Cantidad: {venta['cantidad_ventas']}")
        
        # Si no hay datos, crear meses vacíos
        if not labels:
            now = datetime.now()
            for i in range(11, -1, -1):
                mes = now - timedelta(days=30*i)
                labels.append(mes.strftime('%b %Y'))
                datos_ventas.append(0)
                datos_cantidad.append(0)
        
        return JsonResponse({
            'labels': labels,
            'datasets': [
                {
                    'label': 'Ventas ($)',
                    'data': datos_ventas,
                    'borderColor': 'rgb(59, 130, 246)',
                    'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                    'tension': 0.4,
                    'yAxisID': 'y'
                },
                {
                    'label': 'Cantidad de Ventas',
                    'data': datos_cantidad,
                    'borderColor': 'rgb(16, 185, 129)',
                    'backgroundColor': 'rgba(16, 185, 129, 0.1)',
                    'tension': 0.4,
                    'yAxisID': 'y1'
                }
            ]
        })
        
    except Exception as e:
        print(f"Error en datos_grafico_mensual: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def ventas_por_empleado(request):
    """API endpoint para obtener ventas por empleado (diario o semanal)"""
    try:
        sucursal_id = request.session.get('sucursal_id')
        periodo = request.GET.get('periodo', 'semanal')  # 'diario' o 'semanal'
        
        if not sucursal_id:
            return JsonResponse({'error': 'No hay sucursal seleccionada'}, status=400)
        
        # Definir el período de tiempo según la selección
        ahora = timezone.now()
        
        if periodo == 'diario':
            # Últimos 7 días
            fecha_inicio = ahora - timedelta(days=7)
            trunc_function = TruncDay
            formato_fecha = '%d/%m'
        else:
            # Últimas 8 semanas
            fecha_inicio = ahora - timedelta(weeks=8)
            trunc_function = TruncWeek
            formato_fecha = 'Sem %U'
        
        # Obtener datos agrupados por empleado y período
        ventas_empleados = (
            Venta.objects.filter(
                caja__sucursal_id=sucursal_id,
                fecha__gte=fecha_inicio
            )
            .annotate(periodo=trunc_function('fecha'))
            .values('empleado__first_name', 'empleado__last_name', 'empleado__username', 'periodo')
            .annotate(
                total_ventas=Sum('total'),
                cantidad_ventas=Count('id'),
                promedio_venta=Avg('total')
            )
            .order_by('periodo', 'empleado__username')
        )
        
        # Organizar datos para la tabla
        empleados_data = {}
        periodos_set = set()
        
        for venta in ventas_empleados:
            empleado_key = f"{venta['empleado__first_name']} {venta['empleado__last_name']}".strip()
            if not empleado_key or empleado_key == " ":
                empleado_key = venta['empleado__username']
            
            periodo_str = venta['periodo'].strftime(formato_fecha)
            periodos_set.add(venta['periodo'])
            
            if empleado_key not in empleados_data:
                empleados_data[empleado_key] = {
                    'username': venta['empleado__username'],
                    'total_general': 0,
                    'cantidad_general': 0,
                    'promedio_general': 0,
                    'periodos': {}
                }
            
            empleados_data[empleado_key]['periodos'][periodo_str] = {
                'total': float(venta['total_ventas'] or 0),
                'cantidad': venta['cantidad_ventas'],
                'promedio': float(venta['promedio_venta'] or 0)
            }
        
        # Calcular totales generales por empleado
        for empleado in empleados_data.values():
            totales = [p['total'] for p in empleado['periodos'].values()]
            cantidades = [p['cantidad'] for p in empleado['periodos'].values()]
            
            empleado['total_general'] = sum(totales)
            empleado['cantidad_general'] = sum(cantidades)
            empleado['promedio_general'] = empleado['total_general'] / empleado['cantidad_general'] if empleado['cantidad_general'] > 0 else 0
        
        # Crear lista de períodos ordenados
        periodos_ordenados = sorted(list(periodos_set))
        periodos_labels = [p.strftime(formato_fecha) for p in periodos_ordenados]
        
        # Convertir a formato para la tabla
        tabla_data = []
        for nombre, data in empleados_data.items():
            fila = {
                'empleado': nombre,
                'username': data['username'],
                'total_general': data['total_general'],
                'cantidad_general': data['cantidad_general'],
                'promedio_general': data['promedio_general'],
                'periodos': []
            }
            
            # Agregar datos de cada período
            for periodo_label in periodos_labels:
                periodo_data = data['periodos'].get(periodo_label, {
                    'total': 0,
                    'cantidad': 0,
                    'promedio': 0
                })
                fila['periodos'].append(periodo_data)
            
            tabla_data.append(fila)
        
        # Ordenar por total general descendente
        tabla_data.sort(key=lambda x: x['total_general'], reverse=True)
        
        return JsonResponse({
            'empleados': tabla_data,
            'periodos_labels': periodos_labels,
            'periodo_tipo': periodo,
            'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
            'fecha_fin': ahora.strftime('%Y-%m-%d')
        })
        
    except Exception as e:
        print(f"Error en ventas_por_empleado: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required 
def ranking_empleados(request):
    """API endpoint para obtener ranking de empleados por diferentes métricas"""
    try:
        sucursal_id = request.session.get('sucursal_id')
        metrica = request.GET.get('metrica', 'total')  # 'total', 'cantidad', 'promedio'
        
        if not sucursal_id:
            return JsonResponse({'error': 'No hay sucursal seleccionada'}, status=400)
        
        # Últimos 30 días
        fecha_inicio = timezone.now() - timedelta(days=30)
        
        ranking = (
            Venta.objects.filter(
                caja__sucursal_id=sucursal_id,
                fecha__gte=fecha_inicio
            )
            .values('empleado__first_name', 'empleado__last_name', 'empleado__username')
            .annotate(
                total_ventas=Sum('total'),
                cantidad_ventas=Count('id'),
                promedio_venta=Avg('total')
            )
        )
        
        # Ordenar según la métrica seleccionada
        if metrica == 'cantidad':
            ranking = ranking.order_by('-cantidad_ventas')
        elif metrica == 'promedio':
            ranking = ranking.order_by('-promedio_venta')
        else:
            ranking = ranking.order_by('-total_ventas')
        
        ranking_data = []
        for i, empleado in enumerate(ranking, 1):
            nombre = f"{empleado['empleado__first_name']} {empleado['empleado__last_name']}".strip()
            if not nombre or nombre == " ":
                nombre = empleado['empleado__username']
            
            ranking_data.append({
                'posicion': i,
                'empleado': nombre,
                'username': empleado['empleado__username'],
                'total_ventas': float(empleado['total_ventas'] or 0),
                'cantidad_ventas': empleado['cantidad_ventas'],
                'promedio_venta': float(empleado['promedio_venta'] or 0)
            })
        
        return JsonResponse({
            'ranking': ranking_data,
            'metrica': metrica,
            'periodo': '30 días'
        })
        
    except Exception as e:
        print(f"Error en ranking_empleados: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def debug_dashboard(request):
    """Vista temporal para debuggear los datos del dashboard"""
    try:
        sucursal_id = request.session.get('sucursal_id')
        
        if not sucursal_id:
            return JsonResponse({'error': 'No hay sucursal seleccionada'}, status=400)
        
        # Información general
        debug_info = {
            'sucursal_id': sucursal_id,
            'sucursal_nombre': '',
            'total_ventas': 0,
            'ventas_por_estado': {},
            'cajas_total': 0,
            'cajas_activas': 0,
            'ventas_recientes': []
        }
        
        # Información de la sucursal
        sucursal = Sucursal.objects.get(id=sucursal_id)
        debug_info['sucursal_nombre'] = sucursal.nombre
        
        # Total de ventas
        debug_info['total_ventas'] = Venta.objects.filter(caja__sucursal_id=sucursal_id).count()
        
        # Ventas por estado
        estados = Venta.objects.filter(caja__sucursal_id=sucursal_id).values('estado').annotate(count=Count('id'))
        for estado in estados:
            debug_info['ventas_por_estado'][estado['estado']] = estado['count']
        
        # Información de cajas
        debug_info['cajas_total'] = Caja.objects.filter(sucursal_id=sucursal_id).count()
        debug_info['cajas_activas'] = Caja.objects.filter(sucursal_id=sucursal_id, activo=True).count()
        
        # Últimas 5 ventas
        ventas_recientes = Venta.objects.filter(caja__sucursal_id=sucursal_id).order_by('-fecha')[:5]
        for venta in ventas_recientes:
            debug_info['ventas_recientes'].append({
                'id': venta.id,
                'fecha': venta.fecha.strftime('%Y-%m-%d %H:%M'),
                'total': float(venta.total),
                'estado': venta.estado,
                'empleado': venta.empleado.username,
                'caja_id': venta.caja.id
            })
        
        return JsonResponse(debug_info, indent=2)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



@login_required
def permiso_denegado(request):
    return render(request, "permiso_denegado.html")

#PRODUCTO
@login_required
def productos(request):
    if not request.user.has_perm('entidad.add_producto'):
        return redirect('permiso_denegado')
    productos_list= Producto.objects.filter(activo=True)
    return render(request, "entidad/productos.html", {'productos': productos_list})

@login_required
def nuevo_producto(request, categoria_id=None):
    if not request.user.has_perm('entidad.add_producto'):
        return redirect('permiso_denegado')

    categoria = None
    if categoria_id:
        categoria = get_object_or_404(Categoria, id=categoria_id)

    if request.method == "POST":
        form = ProductoForm(request.POST)
        nombre = request.POST['nombre']
        marca = request.POST['marca']
        precio = Decimal(request.POST['precio'])
        unidad_medida = request.POST['unidad_medida']
        cantidad = int(request.POST['cantidad'])
        proveedores_ids = request.POST.getlist('proveedores')
        codigo = request.POST.get('codigo', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()

        # Validaciones
        if Producto.objects.filter(codigo__iexact=codigo).exists():
            messages.error(request, 'Ya existe un producto con ese código de barras.')
            
        elif Producto.objects.filter(nombre__iexact=nombre, marca__iexact=marca, activo=False).exists():
            # Reactivar producto inactivo
            producto = Producto.objects.get(nombre__iexact=nombre, marca__iexact=marca, activo=False)
            producto.activo = True
            producto.precio = precio
            producto.cantidad = cantidad
            if categoria:
                producto.categoria = categoria
            producto.unidad_medida = unidad_medida
            producto.codigo = codigo
            producto.descripcion = descripcion
            producto.save()
            producto.proveedores.set(proveedores_ids)
            
            # Mensaje de éxito para el modal
            messages.success(request, f'El producto "{producto.nombre}" se ha reactivado y actualizado exitosamente.')
            
            # Redirigir para mostrar el modal
            if categoria_id:
                return redirect('nuevo_producto_categoria', categoria_id=categoria_id)
            else:
                return redirect('nuevo_producto')

        elif Producto.objects.filter(nombre__iexact=nombre, marca__iexact=marca).exists():
            messages.error(request, 'El producto ya existe y está activo.')

        elif form.is_valid():
            # Crear nuevo producto
            try:
                producto = form.save(commit=False)
                producto.nombre = form.cleaned_data['nombre'].strip().lower().capitalize()
                producto.marca = form.cleaned_data['marca'].strip().lower().capitalize()
                producto.precio = precio
                producto.cantidad = cantidad
                if categoria:
                    producto.categoria = categoria
                producto.unidad_medida = unidad_medida
                producto.codigo = codigo
                producto.descripcion = descripcion

                producto.save()
                producto.proveedores.set(proveedores_ids)
                
                # Mensaje de éxito para el modal
                messages.success(request, f'El producto "{producto.nombre}" se ha agregado exitosamente.')
                
                # Redirigir para mostrar el modal
                if categoria_id:
                    return redirect('nuevo_producto_categoria', categoria_id=categoria_id)
                else:
                    return redirect('nuevo_producto')
                    
            except Exception as e:
                messages.error(request, f'Error al guardar el producto: {str(e)}')
        else:
            # Errores de validación del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    field_name = form.fields[field].label or field.replace('_', ' ').title()
                    messages.error(request, f'{field_name}: {error}')

    else:
        # GET request - mostrar formulario vacío
        initial_data = {}
        if categoria:
            initial_data['categoria'] = categoria.id
        form = ProductoForm(initial=initial_data)

    context = {
        'form': form, 
        'tipo': 'Crear',
        'dato': '',
        'categoria': categoria
    }
    return render(request, "entidad/producto_form.html", context)


@login_required
def modificar_producto(request, pk):
    if not request.user.has_perm('entidad.add_productos'):
        return redirect('permiso_denegado')
    producto = get_object_or_404(Producto, id=pk)
    
    if not request.user.has_perm('entidad.change_producto') or not producto.activo:
        return redirect('permiso_denegado')
    
    if request.method == "POST":
        form = ProductoForm(request.POST, instance=producto)
        nombre = request.POST['nombre']
        marca = request.POST['marca']
        codigo = request.POST.get('codigo', '').strip()

        # Validaciones
        if Producto.objects.filter(codigo__iexact=codigo).exclude(id=pk).exists():
            messages.error(request, 'Ya existe otro producto con ese código de barras.')
            
        elif Producto.objects.filter(nombre__iexact=nombre, marca__iexact=marca).exclude(id=pk).exists():
            messages.error(request, 'Ya existe otro producto con estos datos.')

        elif form.is_valid():
            try:
                # Actualizar producto
                producto.nombre = form.cleaned_data['nombre'].strip().lower().capitalize()
                producto.marca = form.cleaned_data['marca'].strip().lower().capitalize()
                producto.codigo = codigo
                
                # Guardar otros campos del formulario
                for field in ['precio', 'cantidad', 'unidad_medida', 'descripcion']:
                    if field in form.cleaned_data:
                        setattr(producto, field, form.cleaned_data[field])
                
                producto.save()
                
                # Guardar proveedores si están en el formulario
                if 'proveedores' in request.POST:
                    proveedores_ids = request.POST.getlist('proveedores')
                    producto.proveedores.set(proveedores_ids)
                
                messages.success(request, f'El producto "{producto.nombre}" se ha modificado correctamente.')
                return redirect("productos")
                
            except Exception as e:
                messages.error(request, f'Error al actualizar el producto: {str(e)}')
        else:
            # Errores de validación del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    field_name = form.fields[field].label or field.replace('_', ' ').title()
                    messages.error(request, f'{field_name}: {error}')
    else:
        form = ProductoForm(instance=producto)

    context = {
        'form': form,
        'dato': f': {producto.nombre}',
        'tipo': 'Modificar',
        'producto': producto
    }
    return render(request, "entidad/producto_form.html", context)

def eliminar_producto(request, pk):
    producto = Producto.objects.get(id=pk)
    if not request.user.has_perm('entidad.delete_producto') or not producto.activo==True:
        return redirect('permiso_denegado')
    
    if request.method == "POST":
        try:
            if DetalleVentaXProducto.objects.filter(producto=producto):
                producto.activo = False
                producto.cantidad = 0
                producto.save()
                messages.success(request, 'Producto eliminado con éxito.')
            else:
                producto.delete()
                messages.success(request, 'Producto eliminado con éxito de forma permanente.')
            
            # Si es una petición AJAX, devolver JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Producto eliminado correctamente'})
            else:
                return redirect('productos')
                
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
            else:
                messages.error(request, f'Error al eliminar el producto: {str(e)}')
                return render(request, "entidad/eliminar_producto_form.html", {
                    'objeto': producto,
                })
    
    return render(request, "entidad/eliminar_producto_form.html", {
        'objeto': producto,
    })

#CATEGORIA
@login_required
def categorias(request):
    if not request.user.has_perm('entidad.add_categoria'):
        return redirect('permiso_denegado')

    categoria_list= Categoria.objects.filter(activo=True)
    return render(request, "entidad/categorias.html", {'categorias': categoria_list})

@login_required
def nueva_categoria(request):
    if not request.user.has_perm('entidad.add_categoria'):
        return redirect('permiso_denegado')

    if request.method == "POST":
        nombre = request.POST['nombre'].strip().lower().capitalize()
        form = CategoriaForm(request.POST)
        
        # Verificar si existe una categoría inactiva con el mismo nombre
        if Categoria.objects.filter(nombre__iexact=nombre, activo=False).exists():
            categoria = Categoria.objects.get(nombre__iexact=nombre, activo=False)
            categoria.activo = True
            categoria.save()
            messages.success(request, 'Categoría creada y reactivada correctamente.')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            else:
                return redirect("categorias")

        # Verificar si ya existe una categoría activa con el mismo nombre
        elif Categoria.objects.filter(nombre__iexact=nombre, activo=True).exists():
            # Solo agregar el error al formulario, no a messages
            form.add_error('nombre', 'Esta categoría ya existe.')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return render(request, "entidad/categoria_form.html", {
                    "form": form,
                    'tipo': 'Nueva'
                })
            
        # Si el formulario es válido, crear nueva categoría
        elif form.is_valid():
            try:
                nueva_categoria = form.save(commit=False)
                nueva_categoria.nombre = nombre
                nueva_categoria.save()
                messages.success(request, 'Categoría creada correctamente.')
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True})
                else:
                    return redirect("categorias")
                    
            except Exception as e:
                # Solo agregar el error al formulario
                form.add_error(None, f'Error al crear la categoría: {str(e)}')
        
        # Si hay errores y es AJAX, devolver el modal con errores
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, "entidad/categoria_form.html", {
                "form": form,
                'tipo': 'Nueva'
            })
    else:
        form = CategoriaForm()
    
    return render(request, "entidad/categoria_form.html", {
        "form": form,
        'tipo': 'Nueva'
    })

@login_required
def modificar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, id=pk)
    
    if not request.user.has_perm('entidad.add_categoria') or not categoria.activo:
        return redirect('permiso_denegado')

    if request.method == "POST":
        nombre = request.POST['nombre'].strip().lower().capitalize()
        form = CategoriaForm(request.POST, instance=categoria)
        
        # Verificar si existe otra categoría con el mismo nombre (excluyendo la actual)
        if Categoria.objects.filter(nombre__iexact=nombre, activo=True).exclude(id=categoria.id).exists():
            # Solo agregar el error al formulario, no a messages
            form.add_error('nombre', 'Ya existe otra categoría con ese nombre.')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return render(request, "entidad/categoria_form.html", {
                    "form": form,
                    'tipo': 'Editar'
                })
        
        # Si el formulario es válido, actualizar categoría
        elif form.is_valid():
            try:
                categoria_actualizada = form.save(commit=False)
                categoria_actualizada.nombre = nombre
                categoria_actualizada.save()
                messages.success(request, 'Categoría actualizada correctamente.')
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True})
                else:
                    return redirect("categorias")
                    
            except Exception as e:
                # Solo agregar el error al formulario
                form.add_error(None, f'Error al actualizar la categoría: {str(e)}')
        
        # Si hay errores y es AJAX, devolver el modal con errores
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, "entidad/categoria_form.html", {
                "form": form,
                'tipo': 'Editar'
            })
    else:
        form = CategoriaForm(instance=categoria)
    
    return render(request, "entidad/categoria_form.html", {
        "form": form,
        'tipo': 'Editar'
    })

@login_required
def eliminar_categoria(request, pk):
    categoria = Categoria.objects.get(id=pk)
    if not request.user.has_perm('entidad.delete_categoria') or not categoria.activo==True:
        return redirect('permiso_denegado')
    
    if request.method == "POST":
        try:
            # Verificar si hay productos asociados (opcional, comentado en tu código)
            # if Producto.objects.filter(categoria=categoria).exists():
            #     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            #         return JsonResponse({'success': False, 'error': 'No se puede eliminar la categoría porque está asociada a un producto.'})
            #     else:
            #         messages.error(request, 'ERROR! No se puede eliminar la categoría porque está asociada a un producto.')
            #         return render(request, "entidad/eliminar_categoria_form.html", {'objeto': categoria})
            
            categoria.activo = False
            categoria.save()
            messages.success(request, 'Categoría eliminada con éxito.')
            
            # Si es una petición AJAX, devolver JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Categoría eliminada correctamente'})
            else:
                return redirect('categorias')
                
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
            else:
                messages.error(request, f'Error al eliminar la categoría: {str(e)}')
                return render(request, "entidad/eliminar_categoria_form.html", {'objeto': categoria})
    
    return render(request, "entidad/eliminar_categoria_form.html", {'objeto': categoria})


def seleccionar_categoria(request):
    if request.method == 'POST':
        categoria_id = request.POST.get('categoria')
        return redirect('nuevo_producto_categoria', categoria_id=categoria_id)
    
    categorias = Categoria.objects.all()
    return render(request, 'entidad/seleccionar_categoria.html', {'categorias': categorias})

#PROVEEDORES
@login_required
def proveedores_productos(request):
    if not request.user.has_perm('entidad.add_proveedorproducto'):
        return redirect('permiso_denegado')
    
    prov_list = ProveedorProducto.objects.filter(activo=True)
    return render(request, "entidad/proveedores_productos.html", {'proveedores': prov_list})

@login_required
def nuevo_proveedor_producto(request):
    if not request.user.has_perm('entidad.add_proveedorproducto'):
        return redirect('permiso_denegado')
    
    if request.method == 'POST':
        nombre = request.POST['nombre'].strip().upper()
        form = ProveedorProductoForm(request.POST)
        
        # Verificar si existe un proveedor inactivo con el mismo nombre
        if ProveedorProducto.objects.filter(nombre__iexact=nombre, activo=False).exists():
            proveedor = ProveedorProducto.objects.get(nombre__iexact=nombre, activo=False)
            proveedor.telefono = request.POST['telefono']
            proveedor.activo = True
            proveedor.save()
            messages.success(request, 'Proveedor creado y reactivado correctamente.')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            else:
                return redirect("proveedores_productos")
                
        # Verificar si ya existe un proveedor activo con el mismo nombre
        elif ProveedorProducto.objects.filter(nombre__iexact=nombre, activo=True).exists():
            # Solo agregar el error al formulario
            form.add_error('nombre', 'Este proveedor ya existe.')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return render(request, "entidad/proveedor_producto_form.html", {
                    "form": form,
                    'tipo': 'Nuevo'
                })
                
        # Si el formulario es válido, crear nuevo proveedor
        elif form.is_valid():
            try:
                nuevo_proveedor = form.save(commit=False)
                nuevo_proveedor.nombre = nombre
                nuevo_proveedor.save()
                messages.success(request, 'Proveedor creado correctamente.')
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True})
                else:
                    return redirect("proveedores_productos")
                    
            except Exception as e:
                # Solo agregar el error al formulario
                form.add_error(None, f'Error al crear el proveedor: {str(e)}')
        
        # Si hay errores y es AJAX, devolver el modal con errores
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, "entidad/proveedor_producto_form.html", {
                "form": form,
                'tipo': 'Nuevo'
            })
    else:
        form = ProveedorProductoForm()
        
    return render(request, "entidad/proveedor_producto_form.html", {
        "form": form,
        'tipo': 'Nuevo'
    })


@login_required
def modificar_proveedor_producto(request, pk):
    proveedor = get_object_or_404(ProveedorProducto, id=pk)
    
    if not request.user.has_perm('entidad.add_proveedorproducto') or not proveedor.activo:
        return redirect('permiso_denegado')
    
    if request.method == "POST":
        nombre = request.POST['nombre'].strip().upper()
        form = ProveedorProductoForm(request.POST, instance=proveedor)
        
        # Verificar si existe otro proveedor con el mismo nombre (excluyendo el actual)
        if ProveedorProducto.objects.filter(nombre__iexact=nombre, activo=True).exclude(id=pk).exists():
            # Solo agregar el error al formulario
            form.add_error('nombre', 'Ya existe otro proveedor con ese nombre.')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return render(request, "entidad/proveedor_producto_form.html", {
                    'form': form,
                    'tipo': 'Modificar',
                    'dato': ': ' + proveedor.nombre
                })
                
        # Si el formulario es válido, actualizar proveedor
        elif form.is_valid():
            try:
                proveedor_actualizado = form.save(commit=False)
                proveedor_actualizado.nombre = nombre
                proveedor_actualizado.save()
                messages.success(request, 'Proveedor modificado correctamente.')
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True})
                else:
                    return redirect("proveedores_productos")
                    
            except Exception as e:
                # Solo agregar el error al formulario
                form.add_error(None, f'Error al modificar el proveedor: {str(e)}')
        
        # Si hay errores y es AJAX, devolver el modal con errores
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, "entidad/proveedor_producto_form.html", {
                'form': form,
                'tipo': 'Modificar',
                'dato': ': ' + proveedor.nombre
            })
    else:
        form = ProveedorProductoForm(instance=proveedor)
        
    return render(request, "entidad/proveedor_producto_form.html", {
        'form': form,
        'tipo': 'Modificar',
        'dato': ': ' + proveedor.nombre
    })

@login_required
def eliminar_proveedor_producto(request, pk):
    proveedor = get_object_or_404(ProveedorProducto, id=pk)
    
    if not request.user.has_perm('entidad.delete_proveedorproducto') or not proveedor.activo:
        return redirect('permiso_denegado')

    if request.method == "POST":
        try:
            proveedor.activo = False
            proveedor.save()
            messages.success(request, 'Proveedor eliminado correctamente.')
            
            # Si es una petición AJAX, devolver JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            else:
                return redirect('proveedores_productos')
                
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
            else:
                messages.error(request, f'Error al eliminar el proveedor: {str(e)}')
                return render(request, "entidad/eliminar_proveedor_form.html", {'objeto': proveedor})

    return render(request, "entidad/eliminar_proveedor_form.html", {'objeto': proveedor})


#CAJA
@login_required



def caja(request):
    if not request.user.has_perm('entidad.view_caja'):
        return redirect('permiso_denegado')
    sucursal_id = request.session.get('sucursal_id')

    if not sucursal_id:
        return redirect('elegir_sucursal')  # Redirige si no seleccionó una
    
    sucursal = Sucursal.objects.get(id=sucursal_id)
    caja = Caja.objects.filter(activo=True, sucursal=sucursal_id).first()
    movimientos = MovimientoCaja.objects.filter(caja=caja).order_by('-id')


    # Total efectivo: suma monto_pago_1 donde metodo_pago_1 sea efectivo + monto_pago_2 donde metodo_pago_2 sea efectivo
    ventas_efectivo_1 = Venta.objects.filter(caja=caja, metodo_pago_1='efectivo')
    total_efectivo_1 = sum(venta.monto_pago_1 for venta in ventas_efectivo_1)

    ventas_efectivo_2 = Venta.objects.filter(caja=caja, metodo_pago_2='efectivo')
    total_efectivo_2 = sum(venta.monto_pago_2 for venta in ventas_efectivo_2)

    total_efectivo = total_efectivo_1 + total_efectivo_2

    # Lo mismo para transferencia
    ventas_transferencia_1 = Venta.objects.filter(caja=caja, metodo_pago_1='transferencia')
    total_transferencia_1 = sum(venta.monto_pago_1 for venta in ventas_transferencia_1)

    ventas_transferencia_2 = Venta.objects.filter(caja=caja, metodo_pago_2='transferencia')
    total_transferencia_2 = sum(venta.monto_pago_2 for venta in ventas_transferencia_2)

    total_transferencia = total_transferencia_1 + total_transferencia_2

    # Y para tarjeta
    ventas_tarjeta_1 = Venta.objects.filter(caja=caja, metodo_pago_1='tarjeta')
    total_tarjeta_1 = sum(venta.monto_pago_1 for venta in ventas_tarjeta_1)

    ventas_tarjeta_2 = Venta.objects.filter(caja=caja, metodo_pago_2='tarjeta')
    total_tarjeta_2 = sum(venta.monto_pago_2 for venta in ventas_tarjeta_2)

    total_tarjeta = total_tarjeta_1 + total_tarjeta_2

    return render(request, "entidad/caja.html", {
        'caja_activa': caja,
        'movimientos': movimientos,
        'efectivo': total_efectivo,
        'transferencia': total_transferencia,
        'tarjeta': total_tarjeta,
        'sucursal': sucursal
    })



@login_required
@require_http_methods(["GET", "POST"])
def abrir_caja(request):
    if not request.user.has_perm('entidad.add_caja'):
        messages.error(request, 'No tiene permisos para abrir caja')
        return redirect('permiso_denegado')
    
    sucursal_id = request.session.get('sucursal_id')
    if not sucursal_id:
        messages.warning(request, 'Debe seleccionar una sucursal primero')
        return redirect('elegir_sucursal')
    
    try:
        sucursal = Sucursal.objects.get(id=sucursal_id)
    except Sucursal.DoesNotExist:
        messages.error(request, 'Sucursal no válida')
        return redirect('elegir_sucursal')
    
    # Verificar si ya existe una caja activa
    caja_activa = Caja.objects.filter(activo=True, sucursal=sucursal).first()
    if caja_activa:
        messages.info(request, 'Ya existe una caja activa. Redirecting...')
        return redirect('caja')
    
    if request.method == 'POST':
        form = AperturaCajaForm(request.POST)
        if form.is_valid():
            monto_inicial = form.cleaned_data["monto_inicial"]
            
            # Validaciones adicionales
            if monto_inicial <= 0:
                messages.error(request, 'El monto inicial debe ser mayor a 0')
                return render(request, 'entidad/abrir_caja_form.html', {
                    'form': form,
                    'sucursal': sucursal
                })
            
            if monto_inicial > 50000:  # Límite de seguridad
                messages.warning(request, 'El monto inicial es muy alto. Verifique con su supervisor.')
                return render(request, 'entidad/abrir_caja_form.html', {
                    'form': form,
                    'sucursal': sucursal
                })
            
            try:
                # Crear nueva caja
                nueva_caja = Caja.objects.create(
                    empleado=request.user,
                    monto_inicial=monto_inicial,
                    saldo_total=monto_inicial,  # Corregido: era +=
                    activo=True,
                    sucursal=sucursal
                )
                
                messages.success(request, f'Caja abierta exitosamente con ${monto_inicial:,.2f}')
                return redirect('caja')
                
            except Exception as e:
                messages.error(request, 'Error al abrir la caja. Intente nuevamente.')
                return render(request, 'entidad/abrir_caja_form.html', {
                    'form': form,
                    'sucursal': sucursal
                })
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario')
    else:
        form = AperturaCajaForm()
    
    return render(request, 'entidad/abrir_caja_form.html', {
        'form': form,
        'sucursal': sucursal
    })


@login_required
def  cerrar_caja(request):
    if not request.user.has_perm('entidad.add_caja'):
        return redirect('permiso_denegado')
    
    sucursal_id = request.session.get('sucursal_id')

    if not sucursal_id:
        return redirect('elegir_sucursal')  # Redirige si no seleccionó una
    
    sucursal=Sucursal.objects.get(id=sucursal_id)
    empleado= request.user
    caja=Caja.objects.filter(activo=True, sucursal=sucursal_id).first()
    if request.method == 'POST':
            caja.activo = False
            caja.fecha_cierre = timezone.now()
            caja.save()
            redirect('caja')
    return render(request, 'entidad/cerrar_caja.html', {'caja': caja,
                                                        'sucursal':sucursal})

@login_required
def ingresar_dinero(request):
    if not request.user.has_perm('entidad.view_caja'):
        return redirect('permiso_denegado')
    
    sucursal_id = request.session.get('sucursal_id')

    if not sucursal_id:
        return redirect('elegir_sucursal')  # Redirige si no seleccionó una
    
    sucursal=Sucursal.objects.get(id=sucursal_id)

    empleado=request.user
    caja=Caja.objects.filter(activo=True, sucursal=sucursal_id).first()
    if request.method=='POST':
        form=IngresarDineroForm(request.POST)
        if form.is_valid():
            MovimientoCaja.objects.create(caja=caja,
                                          empleado= empleado,
                                         tipo=form.cleaned_data["tipo"],
                                         cantidad=form.cleaned_data["cantidad"],
                                        descripcion=form.cleaned_data["descripcion"])
        
            caja.total_ingresado += form.cleaned_data["cantidad"]
            caja.saldo_total += form.cleaned_data["cantidad"]
            caja.save()
            return redirect('caja')
    else:
        form = IngresarDineroForm()
    return render(request,'entidad/ingresar_dinero_form.html', {'form': form})


@login_required
def retirar_dinero(request):
    if not request.user.has_perm('entidad.view_caja'):
        return redirect('permiso_denegado')
    
    sucursal_id = request.session.get('sucursal_id')

    if not sucursal_id:
        return redirect('elegir_sucursal')  # Redirige si no seleccionó una
    
    sucursal=Sucursal.objects.get(id=sucursal_id)
    empleado = request.user
    caja = Caja.objects.filter(activo=True, sucursal=sucursal_id).first()

    if request.method == 'POST':
        form = RetirarDineroForm(request.POST)
        if form.is_valid():
            if form.cleaned_data["cantidad"] > caja.saldo_total:
                messages.error(request, "El monto supera el saldo disponible en la caja.")
            else:
                MovimientoCaja.objects.create(
                    caja=caja,
                    empleado=empleado,
                    tipo=form.cleaned_data["tipo"],
                    cantidad=form.cleaned_data["cantidad"],
                    descripcion=form.cleaned_data["descripcion"]
                )
                caja.total_egresado += form.cleaned_data["cantidad"]
                caja.saldo_total -= form.cleaned_data["cantidad"]
                caja.save()
                return redirect('caja')
        return render(request, 'entidad/retirar_dinero_form.html', {'form': form})
    else:
        form = RetirarDineroForm()
        return render(request, 'entidad/retirar_dinero_form.html', {'form': form})


@login_required
def cajas(request):
    if not request.user.has_perm('entidad.delete_caja'):
        return redirect('permiso_denegado')
    
    caja_list = Caja.objects.all().order_by('-id')  # ← Agregar esto
    return render(request, 'entidad/cajas.html', {'cajas': caja_list})

#VENTAS
@login_required
def crear_venta(request):
    if not request.user.has_perm('entidad.add_venta'):
        return redirect('permiso_denegado')
    
    sucursal_id = request.session.get('sucursal_id')
    if not sucursal_id:
        return redirect('elegir_sucursal')
    
    sucursal = Sucursal.objects.get(id=sucursal_id)
    empleado = request.user

    if request.method == 'POST':
        # ✅ CORRECCIÓN: Validar caja activa en la sucursal específica
        if not Caja.objects.filter(activo=True, sucursal=sucursal_id).exists():
            messages.error(request, 'No tienes ninguna caja abierta en esta sucursal para realizar la venta. Primero abre una.')
            return redirect('caja')

        cliente_id = request.POST.get('cliente')
        if not cliente_id:
            cliente_generico = get_object_or_404(Cliente, nombre="Generico")
            cliente_id = cliente_generico.id

        metodo_pago_1 = request.POST.get('metodo_pago_1')
        monto_pago_1 = Decimal(request.POST.get('monto_pago_1') or '0')

        metodo_pago_2 = request.POST.get('metodo_pago_2')
        monto_pago_2 = Decimal(request.POST.get('monto_pago_2') or '0')

        productos = json.loads(request.POST.get('productos'))
        cantidades = json.loads(request.POST.get('cantidades'))
        precios = json.loads(request.POST.get('precios'))
        descuento = Decimal(request.POST.get('descuento') or '0')

        total_venta_sDes = 0
        cantidadprod = 0
        
        productos_detalle = []

        for i, producto_id in enumerate(productos):
            producto = Producto.objects.get(id=producto_id)
            cantidad_ingresada = Decimal(cantidades[i])
            subtotal_recibido = Decimal(precios[i])
            unidad = producto.unidad_medida

            if unidad in ['kg', 'g', 'l', 'ml']:
                cantidad_stock = cantidad_ingresada / Decimal('1000')
            else:
                cantidad_stock = cantidad_ingresada
            
            if unidad in ['kg', 'g', 'l', 'ml']:
                cantidad_en_unidad_base = cantidad_ingresada / Decimal('1000')
                precio_unitario_usado = subtotal_recibido / cantidad_en_unidad_base
            else:
                precio_unitario_usado = subtotal_recibido / cantidad_ingresada
            
            productos_detalle.append({
                'producto': producto,
                'cantidad': cantidad_ingresada,
                'precio_unitario_usado': precio_unitario_usado,
                'subtotal': subtotal_recibido,
                'cantidad_stock': cantidad_stock
            })
            
            total_venta_sDes += subtotal_recibido
            cantidadprod += 1

            producto.cantidad -= cantidad_stock
            producto.save()

        if descuento:
            total_venta_conDes = total_venta_sDes - (total_venta_sDes * (descuento / 100))
        else:
            total_venta_conDes = total_venta_sDes

        # ✅ SOLUCIÓN MÁS ROBUSTA: Usar try/except para manejar el error
        try:
            caja = Caja.objects.get(activo=True, sucursal=sucursal_id)
        except Caja.DoesNotExist:
            messages.error(request, f'No existe una caja activa en la sucursal {sucursal.nombre}. Contacte al administrador.')
            return redirect('caja')
        except Caja.MultipleObjectsReturned:
            # Si hay múltiples cajas activas, tomar la primera
            caja = Caja.objects.filter(activo=True, sucursal=sucursal_id).first()

        nueva_venta = Venta.objects.create(
            caja=caja,
            cliente_id=cliente_id,
            empleado=empleado,
            total=total_venta_conDes,
            metodo_pago_1=metodo_pago_1,
            monto_pago_1=monto_pago_1,
            metodo_pago_2=metodo_pago_2 if metodo_pago_2 else None,
            monto_pago_2=monto_pago_2,
            descuento=descuento
        )

        detalle_venta = DetalleVenta.objects.create(
            venta=nueva_venta,
            sub_total=total_venta_conDes,
            cantidad=cantidadprod,
        )

        for detalle in productos_detalle:
            DetalleVentaXProducto.objects.create(
                detalle_venta=detalle_venta,
                producto=detalle['producto'],
                cantidad=detalle['cantidad_stock'],
                precio_unitario_venta=detalle['precio_unitario_usado'],
                subtotal_venta=detalle['subtotal']
            )

        caja.saldo_total += total_venta_conDes
        caja.save()

        MovimientoCaja.objects.create(
            caja=caja,
            empleado=empleado,
            tipo='VENTA',
            cantidad=total_venta_conDes
        )

        return redirect('venta_exitosa', pk=nueva_venta.id)

    else:
        clientes = Cliente.objects.all()
        productos = Producto.objects.filter(activo=True)
        return render(request, 'entidad/crear_venta.html', {
            'clientes': clientes,
            'productos': productos,
        })
    
@login_required
def ventas(request, pk):
    if not request.user.has_perm('entidad.delete_caja'):
        return redirect('permiso_denegado')
    
    caja= Caja.objects.get(id=pk)
    ventas_list = Venta.objects.filter(caja=caja)
    return render(request, 'entidad/ventas.html', {'ventas': ventas_list,
                                                    'title': f'Historial de ventas',
                                                    'caja':caja,
                                                    'cajaid': f'#{caja.id}'
                                                    }
                                                    )

@login_required
def detalle_venta(request, pk):
    if not request.user.has_perm('entidad.view_detalleventa'):
        return redirect('permiso_denegado')
    
    venta = Venta.objects.get(id=pk)
    detalle_venta = DetalleVenta.objects.get(venta=venta)
    detalle_venta_producto_list = DetalleVentaXProducto.objects.filter(detalle_venta=detalle_venta)
    
    print(f"=== ANALIZANDO VENTA {pk} ===")
    print(f"Total de la venta: ${venta.total}")
    
    for dxp in detalle_venta_producto_list:
        producto = dxp.producto
        cantidad = dxp.cantidad
        unidad = producto.unidad_medida
        precio_actual = producto.precio
        
        # ✅ USAR DATOS GUARDADOS SI EXISTEN
        if hasattr(dxp, 'precio_unitario_venta') and dxp.precio_unitario_venta > 0:
            # Tenemos los datos guardados - usar directamente
            precio_unitario_usado = dxp.precio_unitario_venta
            subtotal_real = dxp.subtotal_venta
            
            print(f"✅ {producto.nombre}: Usando datos guardados")
            print(f"   Precio unitario usado: ${precio_unitario_usado}")
            print(f"   Subtotal: ${subtotal_real}")
            
        else:
            # Datos antiguos - calcular como antes (para compatibilidad)
            total_sin_descuento = venta.total
            if venta.descuento > 0:
                total_sin_descuento = venta.total / (1 - (venta.descuento / Decimal('100')))
            
            # Asumir que todo el total va a este producto si es el único
            if detalle_venta_producto_list.count() == 1:
                subtotal_real = total_sin_descuento
            else:
                # Para múltiples productos sin datos guardados, distribuir equitativamente
                subtotal_real = total_sin_descuento / detalle_venta_producto_list.count()
            
            # Calcular precio unitario
            if unidad in ['kg', 'g', 'l', 'ml']:
                cantidad_base = cantidad / Decimal('1000')
                precio_unitario_usado = subtotal_real / cantidad_base
            else:
                precio_unitario_usado = subtotal_real / cantidad
                
            print(f"⚠️ {producto.nombre}: Calculando datos (venta antigua)")
        
        # Calcular subtotal teórico (con precio actual)
        if unidad in ['kg', 'g', 'l', 'ml']:
            cantidad_base = cantidad / Decimal('1000')
            subtotal_teorico = cantidad_base * precio_actual
        else:
            subtotal_teorico = cantidad * precio_actual
        
        # Configurar displays
        if unidad in ['kg', 'g']:
            dxp.cantidad_display = f"{cantidad}g"
            dxp.precio_original_display = f"${precio_actual}/kg"
            dxp.precio_venta_display = f"${precio_unitario_usado:.2f}/kg"
        elif unidad in ['l', 'ml']:
            dxp.cantidad_display = f"{cantidad}ml"
            dxp.precio_original_display = f"${precio_actual}/L"
            dxp.precio_venta_display = f"${precio_unitario_usado:.2f}/L"
        else:
            dxp.cantidad_display = f"{cantidad}unid"
            dxp.precio_original_display = f"${precio_actual}"
            dxp.precio_venta_display = f"${precio_unitario_usado:.2f}"
        
        # Detectar modificación
        diferencia_precio = precio_unitario_usado - precio_actual
        es_precio_modificado = abs(diferencia_precio) > Decimal('0.01')
        
        # Asignar propiedades para el template
        dxp.subtotal_producto = subtotal_real
        dxp.subtotal_original = subtotal_teorico
        dxp.precio_original_producto = precio_actual
        dxp.precio_unitario_venta = precio_unitario_usado
        dxp.es_precio_modificado = es_precio_modificado
        dxp.diferencia_precio = diferencia_precio
        dxp.diferencia_subtotal = subtotal_real - subtotal_teorico
        
        if precio_actual > 0:
            dxp.porcentaje_cambio = (diferencia_precio / precio_actual) * 100
        else:
            dxp.porcentaje_cambio = 0
        
        print(f"   Precio original: ${precio_actual}")
        print(f"   ¿Modificado?: {es_precio_modificado}")
        print(f"   Diferencia: ${diferencia_precio}")
    
    return render(request, 'entidad/detalle_venta.html', {
        'venta': venta,
        'detalle_venta': detalle_venta,
        'dxp': detalle_venta_producto_list
    })
@login_required
def detalle_venta_pdf(request, pk):
    venta = Venta.objects.get(id=pk)
    detalle_venta = DetalleVenta.objects.get(venta=venta)
    detalle_venta_producto_list = DetalleVentaXProducto.objects.filter(detalle_venta=detalle_venta)
    total_sin_descuento = 0
    
    for dxp in detalle_venta_producto_list:
        producto = dxp.producto
        cantidad = dxp.cantidad
        unidad = producto.unidad_medida
        
        # ✅ CORRECCIÓN - Aplicar la misma lógica que en crear_venta
        if unidad in ['kg', 'g', 'l', 'ml']:
            # Para productos por peso, calcular: cantidad × precio_por_unidad
            # Ejemplo: 100g × $2500/kg = 100 × 2.5 = $250
            if unidad in ['g', 'ml']:
                # Convertir gramos/ml a kg/l para el cálculo del precio
                cantidad_convertida = cantidad / Decimal('1000')
            else:
                cantidad_convertida = cantidad
            
            subtotal_producto = cantidad_convertida * producto.precio
        else:
            # Para productos por unidad, multiplicar normalmente
            subtotal_producto = producto.precio * cantidad
        
        total_sin_descuento += subtotal_producto
        dxp.subtotal_producto = subtotal_producto

    descuento = venta.descuento
    total_con_descuento = total_sin_descuento - (total_sin_descuento * (descuento / 100)) if descuento else total_sin_descuento

    total_final = total_con_descuento

    html_content = render_to_string("entidad/detalle_venta_pdf.html", {
        'venta': venta,
        'detalle_venta': detalle_venta,
        'detalle_venta_producto_list': detalle_venta_producto_list,
        'total_sin_descuento': total_sin_descuento,
        'total_con_descuento': total_con_descuento,
        'total_final': total_final,
        'descuento': descuento
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="detalle_venta_{venta.id}.pdf"'

    pisa_status = pisa.CreatePDF(html_content, dest=response)
    if pisa_status.err:
        return HttpResponse("Error generando el PDF", status=500)

    return response



def cierre_caja_pdf(request, pk):
    try:
        # Obtener la caja
        caja = Caja.objects.get(id=pk)
        
        # Obtener el empleado específico
        empleado = User.objects.get(id=caja.empleado.id)
        
        # Debug: Verificar datos del empleado
        print(f"Empleado ID: {empleado.id}")
        print(f"Username: {empleado.username}")
        print(f"First name: '{empleado.first_name}'")
        print(f"Last name: '{empleado.last_name}'")
        
        # Usar fecha de cierre si existe, sino usar fecha actual
        fecha_cierre = caja.fecha_cierre if caja.fecha_cierre else timezone.now()
        
        context = {
            'caja': caja,
            'empleado': empleado,
            'fecha_cierre': fecha_cierre,
        }
        
        html_content = render_to_string("entidad/cierre_caja_pdf.html", context)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="cierre_caja_{caja.id}.pdf"'
        
        pisa_status = pisa.CreatePDF(html_content, dest=response)
        if pisa_status.err:
            return HttpResponse("Error generando el PDF", status=500)
        
        return response
        
    except Caja.DoesNotExist:
        return HttpResponse("Caja no encontrada", status=404)
    except User.DoesNotExist:
        return HttpResponse("Empleado no encontrado", status=404)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)
@login_required
def venta_exitosa(request, pk):
    if not request.user.has_perm('entidad.view_detalleventa'):
        return redirect('permiso_denegado')
    
    venta = Venta.objects.get(id=pk)
    detalle_venta = DetalleVenta.objects.get(venta=venta)
    detalle_venta_producto_list = DetalleVentaXProducto.objects.filter(detalle_venta= detalle_venta)
    return render(request, 'entidad/venta_exitosa.html', {'venta' : venta,
                                                          'detalle_venta': detalle_venta,
                                                          'dxp': detalle_venta_producto_list})

    
@login_required
def ventasactual(request):
    sucursal_id = request.session.get('sucursal_id')

    if not sucursal_id:
        return redirect('elegir_sucursal')

    sucursal = Sucursal.objects.get(id=sucursal_id)

    if not request.user.has_perm('entidad.view_venta'):
        return redirect('permiso_denegado')
    try:
        caja = Caja.objects.get(activo=True, sucursal=sucursal)
    except Caja.DoesNotExist:
        return redirect('caja')
    
    ventas_list = Venta.objects.filter(caja=caja)
    return render(request, 'entidad/ventas.html', {'ventas': ventas_list, 'title': 'Historial de Ventas'})

# CLIENTES
@login_required
def clientes(request, template_name="entidad/clientes.html"):
    if not request.user.has_perm('entidad.view_cliente'):
        return redirect('permiso_denegado')
    
    cliente_list= Cliente.objects.filter(activo=True)
    dato={"clientes": cliente_list}
    return render(request, template_name, dato)


@login_required
def nuevo_cliente(request):
    if not request.user.has_perm('entidad.add_cliente'):
        return redirect('permiso_denegado')
    
    if request.method == "POST":
        dni = request.POST['dni']
        form = ClienteForm(request.POST)
        
        # Verificar si existe un cliente inactivo con el mismo DNI
        if Cliente.objects.filter(dni__iexact=dni, activo=False).exists():
            cliente = Cliente.objects.get(dni__iexact=dni, activo=False)
            cliente.nombre = request.POST['nombre'].strip().lower().capitalize()
            cliente.apellido = request.POST['apellido'].strip().lower().capitalize()
            cliente.correo = request.POST['correo']
            cliente.telefono = request.POST['telefono']
            cliente.activo = True
            cliente.save()
            messages.success(request, 'Cliente creado y reactivado correctamente.')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            else:
                return redirect("clientes")
                
        # Verificar si ya existe un cliente activo con el mismo DNI
        elif Cliente.objects.filter(dni__iexact=dni, activo=True).exists():
            # Solo agregar el error al formulario
            form.add_error('dni', 'Este cliente ya existe.')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return render(request, "entidad/cliente_form.html", {"form": form})
                
        # Si el formulario es válido, crear nuevo cliente
        elif form.is_valid():
            try:
                cliente = form.save(commit=False)
                cliente.nombre = form.cleaned_data['nombre'].strip().lower().capitalize()
                cliente.apellido = form.cleaned_data['apellido'].strip().lower().capitalize()
                cliente.save()
                messages.success(request, 'Cliente creado correctamente.')
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True})
                else:
                    return redirect("clientes")
                    
            except Exception as e:
                # Solo agregar el error al formulario
                form.add_error(None, f'Error al crear el cliente: {str(e)}')
        
        # Si hay errores y es AJAX, devolver el modal con errores
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, "entidad/cliente_form.html", {"form": form})
    else:
        form = ClienteForm()
        
    return render(request, "entidad/cliente_form.html", {"form": form})

@login_required
def modificar_cliente(request, pk, template_name="entidad/cliente_form.html"):
    if not request.user.has_perm('entidad.change_cliente'):
        return redirect('permiso_denegado')
    
    try:
        cliente = Cliente.objects.get(id=pk)
    except Cliente.DoesNotExist:
        messages.error(request, 'El cliente no existe.')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Cliente no encontrado'})
        return redirect("clientes")
    
    if request.method == "POST":
        form = ClienteForm(request.POST, instance=cliente)
        dni = request.POST['dni']
        
        # Verificar si existe otro cliente activo con el mismo DNI (excluyendo el actual)
        if Cliente.objects.filter(dni__iexact=dni, activo=True).exclude(id=pk).exists():
            form.add_error('dni', 'Ya existe otro cliente con ese DNI.')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return render(request, template_name, {"form": form})
        
        elif form.is_valid():
            try:
                cliente = form.save(commit=False)
                cliente.nombre = form.cleaned_data['nombre'].strip().lower().capitalize()
                cliente.apellido = form.cleaned_data['apellido'].strip().lower().capitalize()
                cliente.save()
                messages.success(request, 'Cliente modificado correctamente.')
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True})
                else:
                    return redirect("clientes")
                    
            except Exception as e:
                form.add_error(None, f'Error al modificar el cliente: {str(e)}')
        
        # Si hay errores y es AJAX, devolver el modal con errores
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, template_name, {"form": form})
    else:
        form = ClienteForm(instance=cliente)
        
    return render(request, template_name, {"form": form})

@login_required
def eliminar_cliente(request, pk): 
    if not request.user.has_perm('entidad.delete_cliente'):
        return redirect('permiso_denegado')
    
    cliente = get_object_or_404(Cliente._base_manager, id=pk) 
 
    if not request.user.has_perm('entidad.delete_cliente') or not cliente.activo:
        return redirect('permiso_denegado') 

    if request.method == 'POST': 
        try:
            cliente.activo = False  
            cliente.save()
            messages.success(request, 'Cliente eliminado con éxito.')
            
            # Si es una petición AJAX, devolver JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Cliente eliminado correctamente'})
            else:
                return redirect('clientes')
                
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
            else:
                messages.error(request, f'Error al eliminar el cliente: {str(e)}')
                return render(request, "entidad/eliminar_cliente_form.html", {'objeto': cliente})
    
    return render(request, "entidad/eliminar_cliente_form.html", {'objeto': cliente})


@login_required
def ventas_clientes(request, pk):
    if not request.user.has_perm('entidad.view_venta'):
        return redirect('permiso_denegado')
    
    cliente = Cliente.objects.get(id=pk)
    ventas = Venta.objects.filter(cliente=cliente)
    return render(request, 'entidad/ventas.html', {'ventas':ventas,
                                                   'title': f'Cliente: {cliente.nombre} {cliente.apellido}'})






@login_required
def usuarios(request):
    if not request.user.has_perm('entidad.delete_caja'):
        return redirect('permiso_denegado')
    usuarios_list= User.objects.filter().exclude(username='estebanadmin')
    return render(request, 'login/usuarios.html', {'usuarios': usuarios_list})


@login_required
def nuevo_usuario(request):
    if not request.user.has_perm('entidad.delete_caja'):
        return redirect('permiso_denegado')

    if not request.user.has_perm('entidad.delete_caja'):
        return redirect('permiso_denegado')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = form.cleaned_data.get('username').strip().lower()
            user.first_name = form.cleaned_data.get('first_name').strip().lower().capitalize()
            user.last_name = form.cleaned_data.get('last_name').strip().lower().capitalize()
            user.email = form.cleaned_data.get('email').strip().lower()
            user.save()

            group = form.cleaned_data.get('group')
            user.groups.add(group)
            messages.success(request, 'Cuenta creada correctamente')
            return redirect('usuarios')
    else:
        form = CustomUserCreationForm()
    return render(request, 'login/usuario_form.html', {'form': form})

@login_required
def modificar_usuario(request, pk):
    if not request.user.has_perm('entidad.delete_caja'):
        return redirect('permiso_denegado')

    usuario = User.objects.get(id=pk)
    form = UserModifyForm(request.POST or None, instance=usuario)
    if request.method == 'POST':
        if form.is_valid:
            usuario = form.save(commit=False)
            usuario.first_name = form.cleaned_data.get('first_name').strip().lower().capitalize()
            usuario.last_name = form.cleaned_data.get('last_name').strip().lower().capitalize()
            usuario.save()

            group = form.cleaned_data['group']
            usuario.groups.clear()
            usuario.groups.add(group)
            messages.success(request, 'Modificado con éxito.')
            return redirect('usuarios')
        
    return render(request, 'login/modificar_usuario.html', {'form':form, 'usuario': usuario})

@login_required
def change_password_user(request, pk):
    if not request.user.has_perm('entidad.delete_caja'):
        return redirect('permiso_denegado')
    
    usuario = User.objects.get(id=pk)
    if request.method == 'POST':
        form = SetPasswordForm(usuario, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"La contraseña del usuario {usuario.username} ha sido cambiada exitosamente.")
            return redirect('usuarios')
    else:
        form = SetPasswordForm(usuario)
    return render(request, 'login/cambiar_contraseña.html', {'form': form, 'usuario': usuario})

@login_required
def eliminar_usuario(request, pk):
    if not request.user.has_perm('entidad.delete_caja'):
        return redirect('permiso_denegado')

    usuario = User.objects.get(id=pk)
    if request.method == 'POST':
        usuario.delete()
        messages.success(request, 'Usuario eliminado con éxito.')
        return redirect('usuarios')
    
    return render(request, "entidad/confirmar_eliminacion.html", {
        'objeto': 'el usuario',
        'dato': usuario.username,
        'urls': 'usuarios'
    })

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        # Buscar el usuario de forma case-insensitive
        try:
            usuario = User.objects.get(username__iexact=username)
            # Usar el username exacto de la base de datos para authenticate
            user = authenticate(request, username=usuario.username, password=password)
        except User.DoesNotExist:
            messages.error(request, 'Nombre de usuario incorrecto.')
            return render(request, 'login/login.html')

        if user is not None:
            # Resetear intentos fallidos del día actual al hacer login exitoso
            AccesoUsuario.objects.filter(
                usuario=usuario, 
                tipo=False, 
                fecha_ingreso=datetime.now().date()
            ).delete()
            
            AccesoUsuario.objects.create(usuario=usuario,
                                        ip_address=request.META['REMOTE_ADDR'],
                                        tipo=True)
            login(request, user)
            return redirect('elegir_sucursal')
        else:
            intento = AccesoUsuario.objects.filter(usuario=usuario, tipo=False, fecha_ingreso=datetime.now().date()).count()
            if intento > 4:
                user_desactivado = User.objects.get(username=usuario.username)
                user_desactivado.is_active = False
                user_desactivado.save()
                messages.error(request, 'Usuario bloqueado. Por favor, comuníquese con su Administrador.')
            else:
                AccesoUsuario.objects.create(usuario=usuario,
                                            ip_address=request.META['REMOTE_ADDR'],
                                            tipo=False)
                contador = 5 - intento
                messages.error(request, f"Contraseña incorreta, le quedan {contador} {'intento' if contador == 1 else 'intentos'}.")

    return render(request, 'login/login.html')


def login_logout(request):
    logout(request)
    return redirect('login')




#codigos de barra


def generar_etiqueta_view(request):
    if not request.user.has_perm('entidad.delete_caja'):
        return redirect('permiso_denegado')
    productos = Producto.objects.filter(activo=True)  # Para el dropdown
    
    if request.method == 'POST':
        tipo_generacion = request.POST.get('tipo_generacion')
        
        if tipo_generacion == 'manual':
            # Generación manual (como estaba antes)
            nombre = request.POST.get('nombre')
            codigo = request.POST.get('codigo')
            precio = request.POST.get('precio')
            
        elif tipo_generacion == 'producto_existente':
            # Generación desde producto existente
            producto_id = request.POST.get('producto_id')
            producto = get_object_or_404(Producto, id=producto_id)
            
            nombre = f"{producto.nombre} {producto.marca}" if producto.marca else producto.nombre
            codigo = producto.codigo
            precio = str(producto.precio)
        
        else:
            # Si no se especifica tipo, redirigir al formulario
            return render(request, 'entidad/mostrar_etiqueta.html', {'productos': productos})
        
        # Generar el código de barras SIN el texto automático
        barcode_class = barcode.get_barcode_class("code128")
        barcode_img = barcode_class(codigo, writer=ImageWriter())
        
        # Configurar opciones para que no muestre texto automáticamente
        barcode_img.default_writer_options['write_text'] = False
        
        barcode_filename = barcode_img.save("temp_codigo")
        
        # Abrir la imagen del código de barras
        codigo_img = Image.open(barcode_filename)
        ancho_codigo, alto_codigo = codigo_img.size
        
        # Crear una etiqueta más grande y bien proporcionada
        padding = 20
        altura_texto = 120  # Espacio para 3 líneas de texto + márgenes
        ancho_etiqueta = max(ancho_codigo + (padding * 2), 300)  # Mínimo 300px de ancho
        alto_etiqueta = alto_codigo + altura_texto + (padding * 2)
        
        # Crear la imagen de la etiqueta con fondo blanco
        etiqueta = Image.new("RGB", (ancho_etiqueta, alto_etiqueta), "white")
        draw = ImageDraw.Draw(etiqueta)
        
        # Configurar fuentes con tamaños más grandes
        try:
            fuente_nombre = ImageFont.truetype("arial.ttf", 20)  # Más grande
            fuente_precio = ImageFont.truetype("arial.ttf", 28)  # Más grande
            fuente_codigo = ImageFont.truetype("arial.ttf", 14)  # Para calcular el tamaño inicial
        except:
            fuente_nombre = ImageFont.load_default()
            fuente_precio = ImageFont.load_default()
            fuente_codigo = ImageFont.load_default()
        
        # Calcular el tamaño de fuente correcto para que el código ocupe el ancho exacto del código de barras
        codigo_texto = codigo
        fuente_size = 14
        
        # Encontrar el tamaño de fuente que hace que el texto tenga el ancho exacto del código de barras
        while fuente_size > 8:  # Tamaño mínimo de fuente
            try:
                fuente_test = ImageFont.truetype("arial.ttf", fuente_size)
            except:
                fuente_test = ImageFont.load_default()
            
            # Crear un draw temporal para medir el texto
            temp_img = Image.new("RGB", (1, 1), "white")
            temp_draw = ImageDraw.Draw(temp_img)
            bbox = temp_draw.textbbox((0, 0), codigo_texto, font=fuente_test)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= ancho_codigo:
                fuente_codigo_final = fuente_test
                break
            fuente_size -= 1
        else:
            # Si no encontramos un tamaño apropiado, usar el mínimo
            try:
                fuente_codigo_final = ImageFont.truetype("arial.ttf", 8)
            except:
                fuente_codigo_final = ImageFont.load_default()
        
        # Si el texto es más pequeño que el ancho del código de barras, aumentar el tamaño
        if fuente_size <= ancho_codigo:
            while fuente_size < 24:  # Tamaño máximo razonable
                try:
                    fuente_test = ImageFont.truetype("arial.ttf", fuente_size + 1)
                except:
                    break
                
                temp_img = Image.new("RGB", (1, 1), "white")
                temp_draw = ImageDraw.Draw(temp_img)
                bbox = temp_draw.textbbox((0, 0), codigo_texto, font=fuente_test)
                text_width = bbox[2] - bbox[0]
                
                if text_width > ancho_codigo:
                    break
                    
                fuente_codigo_final = fuente_test
                fuente_size += 1
        
        # Calcular posiciones centradas
        y_actual = padding
        
        # Dibujar nombre del producto (centrado)
        bbox_nombre = draw.textbbox((0, 0), nombre, font=fuente_nombre)
        ancho_nombre = bbox_nombre[2] - bbox_nombre[0]
        x_nombre = (ancho_etiqueta - ancho_nombre) // 2
        draw.text((x_nombre, y_actual), nombre, font=fuente_nombre, fill="black")
        y_actual += 25
        
        # Dibujar precio (centrado y destacado)
        precio_texto = f"${precio}"
        bbox_precio = draw.textbbox((0, 0), precio_texto, font=fuente_precio)
        ancho_precio = bbox_precio[2] - bbox_precio[0]
        x_precio = (ancho_etiqueta - ancho_precio) // 2
        draw.text((x_precio, y_actual), precio_texto, font=fuente_precio, fill="black")
        y_actual += 35
        
        # Centrar el código de barras horizontalmente
        x_codigo = (ancho_etiqueta - ancho_codigo) // 2
        etiqueta.paste(codigo_img, (x_codigo, y_actual))
        y_actual += alto_codigo + 10
        
        # Dibujar el código numérico debajo del código de barras (ajustado al ancho exacto)
        bbox_codigo_num = draw.textbbox((0, 0), codigo, font=fuente_codigo_final)
        ancho_codigo_num = bbox_codigo_num[2] - bbox_codigo_num[0]
        x_codigo_num = (ancho_etiqueta - ancho_codigo_num) // 2
        draw.text((x_codigo_num, y_actual), codigo, font=fuente_codigo_final, fill="black")
        
        # Convertir a base64
        buffer = BytesIO()
        etiqueta.save(buffer, format='PNG')
        buffer.seek(0)
        
        imagen_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        imagen_data_url = f"data:image/png;base64,{imagen_base64}"
        
        # Limpiar archivo temporal
        try:
            os.remove(barcode_filename)
        except:
            pass
        
        return render(request, 'entidad/mostrar_etiqueta.html', {
            'imagen_data_url': imagen_data_url,
            'productos': productos
        })
    
    return render(request, 'entidad/mostrar_etiqueta.html', {'productos': productos})


#NUEVO AGREGADO 25/5 ESTEBAN
@login_required
def elegir_sucursal(request):
    if request.method == 'POST':
        sucursal_id = request.POST.get('sucursal')
        sucursal = Sucursal.objects.get(id=sucursal_id)
        request.session['sucursal_id'] = sucursal.id
        request.session['sucursal_nombre'] = sucursal.nombre
        return redirect('home')  # o redirigir al dashboard
    sucursales = Sucursal.objects.all()
    return render(request, 'login/elegir_sucursal.html', {'sucursales': sucursales})






# Tu Access Token de Mercado Pago
MERCADO_PAGO_ACCESS_TOKEN = 'APP_USR-2566497799915459-061820-7db005db4a996ca46d987b74034d4c02-303081609' 

@csrf_exempt
def webhook_mercadopago(request):
    """Webhook que guarda notificaciones en BD para Gunicorn"""
    try:
        print("🔔 Webhook recibido!")
        
        # Responder OK inmediatamente
        response = HttpResponse("OK", status=200)
        
        if request.method == 'POST':
            try:
                # Obtener payment_id de los parámetros de la URL
                payment_id = request.GET.get('id')
                topic = request.GET.get('topic')
                
                print(f"💳 Payment ID: {payment_id}")
                print(f"📋 Topic: {topic}")
                
                if topic == 'payment' and payment_id:
                    # Obtener detalles del pago de Mercado Pago
                    url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
                    headers = {'Authorization': f'Bearer {MERCADO_PAGO_ACCESS_TOKEN}'}
                    
                    try:
                        pago_response = requests.get(url, headers=headers, timeout=5)
                        
                        if pago_response.status_code == 200:
                            payment = pago_response.json()
                            print(f"💰 Status del pago: {payment['status']}")
                            
                            if payment['status'] == 'approved':
                                # GUARDAR NOTIFICACIÓN EN BASE DE DATOS
                                NotificacionPago.objects.create(
                                    monto=payment['transaction_amount'],
                                    moneda=payment['currency_id'],
                                    email_cliente=payment.get('payer', {}).get('email', 'Cliente'),
                                    payment_id=payment_id,
                                    descripcion=payment.get('description', 'Transferencia')
                                )
                                
                                print("✅ ¡NOTIFICACIÓN GUARDADA EN BD!")
                                
                                # También mostrar en terminal (para debug)
                                print("\n" + "=" * 50)
                                print(f"💰 PAGO APROBADO: ${payment['transaction_amount']} {payment['currency_id']}")
                                print(f"👤 De: {payment.get('payer', {}).get('email', 'Cliente')}")
                                print(f"🆔 ID: {payment_id}")
                                print("=" * 50 + "\n")
                                
                            elif payment['status'] == 'rejected':
                                print(f"❌ Pago rechazado: {payment_id}")
                            elif payment['status'] == 'pending':
                                print(f"⏳ Pago pendiente: {payment_id}")
                        else:
                            print(f"❌ Error API Mercado Pago: {pago_response.status_code}")
                            
                    except requests.exceptions.RequestException as e:
                        print(f"❌ Error consultando Mercado Pago: {e}")
                        
            except Exception as e:
                print(f"❌ Error procesando webhook: {e}")
        
        return response
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        return HttpResponse("OK", status=200)

# 3. AGREGAR VISTA PARA OBTENER NOTIFICACIONES (en views.py)
@login_required
def obtener_notificaciones(request):
    """API para obtener notificaciones nuevas"""
    notificaciones = NotificacionPago.objects.filter(mostrada=False)
    
    data = []
    for notif in notificaciones:
        data.append({
            'monto': float(notif.monto),
            'moneda': notif.moneda,
            'email_cliente': notif.email_cliente,
            'payment_id': notif.payment_id,
            'descripcion': notif.descripcion,
            'fecha': notif.fecha.isoformat()
        })
        notif.mostrada = True
        notif.save()
    
    return JsonResponse({'notificaciones': data})


@login_required
@require_http_methods(["GET"])
def buscar_producto_por_codigo(request):
    """
    Vista AJAX para buscar un producto por su código
    """
    codigo = request.GET.get('codigo', '').strip()
    
    if not codigo:
        return JsonResponse({
            'success': False, 
            'error': 'Código no proporcionado'
        })
    
    try:
        producto = Producto.objects.get(codigo=codigo, activo=True)
        
        return JsonResponse({
            'success': True,
            'producto': {
                'id': producto.id,
                'codigo': producto.codigo,
                'nombre': producto.nombre,
                'marca': producto.marca or '',
                'precio': float(producto.precio),
                'stock': producto.cantidad,
                'categoria': producto.categoria.nombre if producto.categoria else '',
                'descripcion': producto.descripcion or ''
            }
        })
        
    except Producto.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f'Producto con código "{codigo}" no encontrado'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        })

@login_required
@require_http_methods(["GET"])
def buscar_productos_inteligente(request):
    termino = request.GET.get('termino', '').strip()
    limite = int(request.GET.get('limite', 10))
    
    if len(termino) < 2:
        return JsonResponse({'success': False, 'error': 'Término muy corto'})
    
    try:
        productos = Producto.objects.filter(
            Q(activo=True) &
            (Q(nombre__icontains=termino) | Q(marca__icontains=termino))
        ).order_by('nombre')[:limite]
        
        productos_data = []
        for producto in productos:
            productos_data.append({
                'id': producto.id,
                'codigo': producto.codigo,
                'nombre': producto.nombre,
                'marca': producto.marca or '',
                'precio': float(producto.precio),
                'stock': float(producto.cantidad),
                'unidad_medida': producto.unidad_medida,
            })
        
        return JsonResponse({'success': True, 'productos': productos_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})