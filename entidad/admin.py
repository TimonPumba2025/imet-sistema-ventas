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
