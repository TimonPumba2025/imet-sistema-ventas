from django.contrib import admin
from entidad.models import *
# Register your models here.

admin.site.register(Categoria)
admin.site.register(Cliente)
admin.site.register(ProveedorProducto)
admin.site.register(Producto)
admin.site.register(Caja)
admin.site.register(Venta)
admin.site.register(DetalleVenta)
admin.site.register(DetalleVentaXProducto)
admin.site.register(Sucursal)
admin.site.register(NotificacionPago)


from django.contrib import admin
from django.utils.html import format_html
from .models import RangoPuntos, HistorialPuntos


@admin.register(RangoPuntos)
class RangoPuntosAdmin(admin.ModelAdmin):
    list_display = ['rango_display', 'puntos_otorgados', 'activo', 'fecha_creacion']
    list_filter = ['activo', 'fecha_creacion']
    search_fields = ['monto_minimo', 'monto_maximo']
    list_editable = ['activo']
    ordering = ['monto_minimo']
    
    fieldsets = (
        ('Configuración del Rango', {
            'fields': ('monto_minimo', 'monto_maximo', 'puntos_otorgados')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
    )
    
    def rango_display(self, obj):
        """Muestra el rango en un formato legible"""
        return format_html(
            '<strong>${} - ${}</strong>',
            obj.monto_minimo,
            obj.monto_maximo
        )
    rango_display.short_description = 'Rango de Monto'
    
    def save_model(self, request, obj, form, change):
        """Validación adicional al guardar"""
        obj.full_clean()
        super().save_model(request, obj, form, change)


@admin.register(HistorialPuntos)
class HistorialPuntosAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'tipo', 'cantidad_display', 'saldo_resultante', 'fecha', 'empleado']
    list_filter = ['tipo', 'fecha']
    search_fields = ['cliente__nombre', 'cliente__apellido', 'descripcion']
    date_hierarchy = 'fecha'
    readonly_fields = ['fecha']
    
    fieldsets = (
        ('Información del Movimiento', {
            'fields': ('cliente', 'tipo', 'cantidad', 'descripcion')
        }),
        ('Detalles', {
            'fields': ('venta', 'saldo_resultante', 'empleado', 'fecha')
        }),
    )
    
    def cantidad_display(self, obj):
        """Muestra la cantidad con color según el tipo"""
        if obj.tipo == 'GANADO':
            color = 'green'
            simbolo = '+'
        elif obj.tipo in ['CANJEADO', 'VENCIDO']:
            color = 'red'
            simbolo = '-'
        else:
            color = 'orange'
            simbolo = ''
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}{} pts</span>',
            color,
            simbolo,
            obj.cantidad
        )
    cantidad_display.short_description = 'Cantidad'
    
    def has_add_permission(self, request):
        """No permitir agregar desde el admin (se hace desde el sistema)"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar (es historial)"""
        return False


# @admin.register(ConfiguracionNotificaciones)
# class ConfiguracionNotificacionesAdmin(admin.ModelAdmin):
#     list_display = ['estado_display', 'enviar_en_venta', 'fecha_actualizacion']
    
#     fieldsets = (
#         ('Estado General', {
#             'fields': ('activo', 'enviar_en_venta')
#         }),
#         ('Plantilla de Mensaje', {
#             'fields': ('mensaje_template',),
#             'description': 'Variables disponibles: {nombre}, {puntos}, {total_puntos}, {monto}'
#         }),
#         ('Configuración de Twilio', {
#             'fields': ('twilio_account_sid', 'twilio_auth_token', 'twilio_whatsapp_from'),
#             'classes': ('collapse',),
#             'description': 'Credenciales de Twilio para enviar mensajes de WhatsApp'
#         }),
#     )
    
#     def estado_display(self, obj):
#         """Muestra el estado con un ícono visual"""
#         if obj.activo:
#             return format_html(
#                 '<span style="color: green;">✓ Activo</span>'
#             )
#         return format_html(
#             '<span style="color: red;">✗ Inactivo</span>'
#         )
#     estado_display.short_description = 'Estado'
    
#     def has_add_permission(self, request):
#         """Solo permitir una configuración (Singleton)"""
#         return not ConfiguracionNotificaciones.objects.exists()
    
#     def has_delete_permission(self, request, obj=None):
#         """No permitir eliminar la configuración"""
#         return False