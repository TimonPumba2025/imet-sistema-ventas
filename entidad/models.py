"""
MODELOS ACTUALIZADOS PARA SISTEMA DE PUNTOS
Reemplaza tu archivo models.py con este
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import datetime
from django.core.exceptions import ValidationError

# ========== CHOICES EXISTENTES ==========
ESTADOS_CHOICES=(
    ("NOP","NO PAGADO"),
    ("PAG", "PAGADO")
)

METODO_PAGO_CHOICE=(
    ("TRAN","TRANSFERENCIA"),
    ("EFEC", "EFECTIVO"),
    ("TARJ", "TARJETA")
)

UNIDADES_CHOICE= [
    ('kg', 'Kilogramos'),
    ('g', 'Gramos'),
    ('l', 'Litros'),
    ('ml', 'Mililitros'),
    ('unidad', 'Unidad'),
]


# ========== MODELOS EXISTENTES (sin cambios) ==========

class Categoria(models.Model):
    nombre= models.CharField(max_length=50, unique=True, null=False, blank=False)
    activo= models.BooleanField(default=True)
    imagen = models.ImageField(upload_to='categorias/', null=True, blank=True)
    
    class Meta:
        verbose_name = ("Categoria")
        verbose_name_plural = ("Categorias")

    def __str__(self):
        return f"{self.nombre}"


class Cliente(models.Model):
    dni= models.CharField(max_length=8)
    nombre= models.CharField(max_length=30)
    apellido= models.CharField(max_length=30)
    correo= models.EmailField(max_length=40, blank=True)
    telefono= models.CharField(max_length=10)
    activo= models.BooleanField(default=True)
    
    # ===== NUEVOS CAMPOS PARA PUNTOS =====
    puntos_actuales = models.IntegerField(
        default=0, 
        help_text="Puntos disponibles del cliente"
    )
    puntos_totales_acumulados = models.IntegerField(
        default=0, 
        help_text="Total de puntos ganados históricamente"
    )
    fecha_ultima_actualizacion_puntos = models.DateTimeField(
        null=True, 
        blank=True
    )
    # ======================================

    class Meta:
        verbose_name = ("Cliente")
        verbose_name_plural = ("Clientes")

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
    
    def agregar_puntos(self, cantidad, descripcion="", empleado=None):
        """Agregar puntos al cliente"""
        self.puntos_actuales += cantidad
        self.puntos_totales_acumulados += cantidad
        self.fecha_ultima_actualizacion_puntos = datetime.now()
        self.save()
        
        # Registrar en historial
        HistorialPuntos.objects.create(
            cliente=self,
            tipo='GANADO',
            cantidad=cantidad,
            descripcion=descripcion,
            saldo_resultante=self.puntos_actuales,
            empleado=empleado
        )
    
    def restar_puntos(self, cantidad, descripcion="", empleado=None):
        """Restar puntos al cliente (canje)"""
        if cantidad > self.puntos_actuales:
            raise ValidationError("El cliente no tiene suficientes puntos")
        
        self.puntos_actuales -= cantidad
        self.fecha_ultima_actualizacion_puntos = datetime.now()
        self.save()
        
        # Registrar en historial
        HistorialPuntos.objects.create(
            cliente=self,
            tipo='CANJEADO',
            cantidad=cantidad,
            descripcion=descripcion,
            saldo_resultante=self.puntos_actuales,
            empleado=empleado
        )


class ProveedorProducto(models.Model):
    nombre= models.CharField(max_length=100)
    telefono= models.CharField(max_length=10)
    activo= models.BooleanField(default=True)

    class Meta:
        verbose_name = ("Proveedor de producto")
        verbose_name_plural = ("Proveedores de productos")

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    nombre= models.CharField(max_length=100, blank=False)
    marca= models.CharField(max_length=10, null=True ,blank=True)
    precio= models.DecimalField(max_digits=10, decimal_places=2)
    categoria= models.ForeignKey(Categoria, on_delete=models.PROTECT)
    descripcion= models.TextField(max_length=100, null=True, blank=True)
    cantidad = models.DecimalField(max_digits=10, decimal_places=3, default=0) 
    proveedores= models.ManyToManyField('ProveedorProducto' ,related_name='proveedores')
    activo= models.BooleanField(default=True)
    unidad_medida = models.CharField(max_length=10,choices=UNIDADES_CHOICE, default='unidad')

    class Meta:
        verbose_name = ("Producto")
        verbose_name_plural = ("Productos")

    def __str__(self):
        return f"{self.nombre} {self.marca} {self.precio} {self.codigo}"


class Sucursal(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class Caja(models.Model):
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE, null=True)
    empleado= models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_apertura= models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    monto_inicial= models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_ingresado= models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_egresado= models.DecimalField(max_digits=10, decimal_places=2, default=0)
    saldo_total= models.DecimalField(max_digits=10, decimal_places=2)
    activo= models.BooleanField(default=False)

    class Meta:
        verbose_name = "Caja"
        verbose_name_plural = "Cajas"

    def __str__(self):
        return f"{self.empleado.username} {self.fecha_apertura}"


class MovimientoCaja(models.Model):
    TIPO_MOVIMIENTO = [
        ('INGRESO', 'Ingreso'),
        ('RETIRO', 'Retiro'),
        ('VENTA', 'Venta')
    ]

    caja = models.ForeignKey(Caja, on_delete=models.CASCADE, related_name="movimientos")
    empleado= models.ForeignKey(User, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=7, choices=TIPO_MOVIMIENTO)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.tipo} de {self.cantidad} en {self.fecha}"


class Venta(models.Model):
    caja= models.ForeignKey(Caja, on_delete=models.PROTECT)
    empleado= models.ForeignKey(User, on_delete=models.PROTECT)
    cliente= models.ForeignKey(Cliente, null=True, blank=True, on_delete=models.PROTECT)  
    fecha= models.DateTimeField(auto_now_add=True)
    total= models.DecimalField(max_digits=10, decimal_places=2)
    estado= models.CharField(max_length=4, choices=ESTADOS_CHOICES, default="NOP")
    metodo_pago_1 = models.CharField(max_length=20, choices=METODO_PAGO_CHOICE, blank=True, null=True)
    monto_pago_1 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    metodo_pago_2 = models.CharField(max_length=20, choices=METODO_PAGO_CHOICE, blank=True, null=True)
    monto_pago_2 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    descuento= models.DecimalField(max_digits=10, default=0, decimal_places=2)
    
    # ===== NUEVO CAMPO PARA PUNTOS =====
    puntos_otorgados = models.IntegerField(
        default=0, 
        help_text="Puntos otorgados en esta venta"
    )
    # ====================================
    
    class Meta:
        verbose_name = ("Venta")
        verbose_name_plural = ("Ventas")

    def __str__(self):
        return f"{self.caja} {self.empleado.username} {self.cliente} {self.fecha} {self.total} {self.estado}"


class DetalleVenta(models.Model):
    venta= models.ForeignKey(Venta, on_delete=models.CASCADE)
    cantidad = models.DecimalField(max_digits=10, decimal_places=3) 
    sub_total= models.DecimalField(max_digits=10, decimal_places=2)
    producto= models.ManyToManyField(Producto, through='DetalleVentaXProducto')

    class Meta:
        verbose_name = ("Detalle de venta")
        verbose_name_plural = ("Detalles de ventas")

    def __str__(self):
        return f"{self.producto} {self.cantidad} {self.sub_total}"


class DetalleVentaXProducto(models.Model):
    detalle_venta = models.ForeignKey(DetalleVenta, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=10, decimal_places=3, default=0) 
    precio_unitario_venta = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subtotal_venta = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = 'entidad_detalleventa_producto'
        verbose_name = ("Detalle Venta Producto")
        verbose_name_plural = ("Detalles Ventas Productos")

    def __str__(self):
        return f"{self.detalle_venta} {self.producto} {self.cantidad}"


class AccesoUsuario(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_ingreso = models.DateField(auto_now_add=True)
    hora_ingreso = models.TimeField(auto_now_add=True)
    ip_address = models.CharField(max_length=30)
    tipo = models.BooleanField(default=False) 
   
    class Meta:
        verbose_name = ("Acceso Usuario")
        verbose_name_plural = ("Accesos Usuarios")

    def __str__(self):
        return f"{self.usuario} {self.ip_address}"


class NotificacionPago(models.Model):
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    moneda = models.CharField(max_length=10)
    email_cliente = models.CharField(max_length=100)
    payment_id = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=200, default='Transferencia')
    fecha = models.DateTimeField(auto_now_add=True)
    mostrada = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-fecha']


# ========== NUEVOS MODELOS PARA SISTEMA DE PUNTOS ==========

# ========== MODELO RANGOPUNTOS CORREGIDO ==========
# Reemplazar desde la línea 279 hasta 327 en tu models.py

class RangoPuntos(models.Model):
    """Define los rangos de montos y puntos a otorgar"""
    monto_minimo = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Monto mínimo de la compra"
    )
    monto_maximo = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Monto máximo de la compra"
    )
    puntos_otorgados = models.IntegerField(
        help_text="Cantidad de puntos que se otorgan"
    )
    activo = models.BooleanField(
        default=True,
        help_text="Solo rangos activos se aplicarán"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Rango de Puntos"
        verbose_name_plural = "Rangos de Puntos"
        ordering = ['monto_minimo']
    
    def __str__(self):
        return f"${self.monto_minimo} - ${self.monto_maximo} = {self.puntos_otorgados} puntos"
    
    def clean(self):
        """Validación mejorada con detección de rangos superpuestos"""
        from decimal import Decimal
        
        # Validar que mínimo sea menor que máximo
        if self.monto_minimo >= self.monto_maximo:
            raise ValidationError("El monto mínimo debe ser menor al máximo")
        
        # Verificar rangos superpuestos SOLO si está activo
        if self.activo:
            # Obtener rangos existentes (excluyendo el actual si se está editando)
            rangos_existentes = RangoPuntos.objects.filter(activo=True)
            if self.pk:  # Si está editando
                rangos_existentes = rangos_existentes.exclude(pk=self.pk)
            
            for rango in rangos_existentes:
                # Verificar si hay solapamiento
                # Caso 1: El nuevo mínimo está dentro de un rango existente
                if rango.monto_minimo <= self.monto_minimo <= rango.monto_maximo:
                    raise ValidationError(
                        f"El rango se solapa con: ${rango.monto_minimo} - ${rango.monto_maximo}. "
                        f"El monto mínimo ${self.monto_minimo} ya está dentro de ese rango."
                    )
                
                # Caso 2: El nuevo máximo está dentro de un rango existente
                if rango.monto_minimo <= self.monto_maximo <= rango.monto_maximo:
                    raise ValidationError(
                        f"El rango se solapa con: ${rango.monto_minimo} - ${rango.monto_maximo}. "
                        f"El monto máximo ${self.monto_maximo} ya está dentro de ese rango."
                    )
                
                # Caso 3: El nuevo rango contiene completamente a uno existente
                if self.monto_minimo <= rango.monto_minimo and self.monto_maximo >= rango.monto_maximo:
                    raise ValidationError(
                        f"El rango contiene completamente al rango existente: "
                        f"${rango.monto_minimo} - ${rango.monto_maximo}"
                    )
                
                # Caso 4: El nuevo rango está contenido en uno existente
                if rango.monto_minimo <= self.monto_minimo and rango.monto_maximo >= self.monto_maximo:
                    raise ValidationError(
                        f"El rango está completamente dentro del rango existente: "
                        f"${rango.monto_minimo} - ${rango.monto_maximo}"
                    )
    
    def save(self, *args, **kwargs):
        """Override save para ejecutar validaciones"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @staticmethod
    def calcular_puntos(monto_compra):
        """
        Calcula puntos según el monto - LÓGICA MEJORADA
        
        Si el monto supera todos los rangos, usa el rango más alto.
        Si el monto está dentro de un rango, usa ese rango.
        Si el monto es menor a todos los rangos, devuelve 0.
        """
        try:
            from decimal import Decimal
            monto_compra = Decimal(str(monto_compra))
            
            # Buscar rango exacto (monto dentro del rango)
            rango = RangoPuntos.objects.filter(
                activo=True,
                monto_minimo__lte=monto_compra,
                monto_maximo__gte=monto_compra
            ).order_by('-puntos_otorgados').first()
            
            if rango:
                return rango.puntos_otorgados
            
            # Si no encontró rango exacto, verificar si el monto supera todos los rangos
            # En ese caso, usar el rango más alto
            rango_mas_alto = RangoPuntos.objects.filter(
                activo=True,
                monto_maximo__lt=monto_compra  # Monto supera este rango
            ).order_by('-monto_maximo').first()
            
            if rango_mas_alto:
                # El monto supera el rango más alto, usar sus puntos
                return rango_mas_alto.puntos_otorgados
            
            # Si llegamos aquí, el monto es menor a todos los rangos
            return 0
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error al calcular puntos: {str(e)}")
            return 0


class HistorialPuntos(models.Model):
    """Registra todos los movimientos de puntos"""
    TIPO_MOVIMIENTO_CHOICES = [
        ('GANADO', 'Puntos Ganados'),
        ('CANJEADO', 'Puntos Canjeados'),
        ('AJUSTE', 'Ajuste Manual'),
        ('VENCIDO', 'Puntos Vencidos'),
    ]
    
    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.CASCADE,
        related_name='historial_puntos'
    )
    venta = models.ForeignKey(
        Venta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    tipo = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO_CHOICES)
    cantidad = models.IntegerField()
    descripcion = models.TextField(blank=True)
    saldo_resultante = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    empleado = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = "Historial de Puntos"
        verbose_name_plural = "Historial de Puntos"
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.cliente} - {self.tipo}: {self.cantidad} pts"