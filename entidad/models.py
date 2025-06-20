from django.db import models

from django.contrib.auth.models import User

from django.utils.timezone import datetime
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

    class Meta:
        verbose_name = ("Cliente")
        verbose_name_plural = ("Clientes")

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

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
        return f"{self.nombre} {self.marca} {self.precio} {self.codigo}  "

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
    subtotal_venta = models.DecimalField(max_digits=10, decimal_places=2, default=0) # True = acceso correcto, False = fallido
    


    class Meta:
        db_table = 'entidad_detalleventa_producto'
        verbose_name = ("Detalle Venta Producto")
        verbose_name = ("Detalles Ventas Productos")

    def str(self):
        return f"{self.detalle_venta} {self.productos} {self.cantidad}"
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




