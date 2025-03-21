from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify  # Utilidad para crear el slug automáticamente
import uuid

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rut = models.CharField(max_length=12, unique=True)  # RUT (Ej: 12.345.678-9)
    telefono = models.CharField(max_length=15,unique=True)  # Teléfono
    direccion = models.CharField(max_length=255)  # Dirección
    acepta_terminos = models.BooleanField(default=False)  # Campo para aceptar términos y condiciones


    def __str__(self):
        return f"Perfil de {self.user.username}"
    
class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    def __str__(self):
        return self.nombre
    
class Color(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    marca = models.CharField(max_length=100)
    nombre = models.CharField(max_length=255)
    precio =  models.IntegerField()
    activo = models.BooleanField(default=True)  # Nuevo campo activo para indicar si la talla está disponible
    slug = models.SlugField(unique=True, blank=True)  # Slug único y automáticamente generado
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, null=True, blank=True)  # Permite nulos
    descripcion = models.TextField(max_length=1000, null=True)
    descuento = models.IntegerField(default=0, help_text="Porcentaje de descuento (0-100)")
    
    def save(self, *args, **kwargs):

       # Si el nombre ha cambiado, actualizamos el slug

        # Si el nombre ha cambiado, actualizamos el slug
        if self.pk:  # Esto significa que el objeto ya existe (es una actualización)
            original = Producto.objects.get(pk=self.pk)
            if original.nombre != self.nombre:
                self.slug = slugify(self.nombre)  # Regeneramos el slug si el nombre ha cambiado
        else:  # Es una creación nueva, generamos el slug normalmente
            self.slug = slugify(self.nombre)
        super(Producto, self).save(*args, **kwargs)

    @property
    def promedio_valoracion(self):
        if self.opiniones.exists():
            total_valoraciones = sum(opinion.valoracion for opinion in self.opiniones.all())
            return total_valoraciones / self.opiniones.count()
        else:
            return 0  # Retorna 0 si no hay opiniones
        
    @property
    def precio_con_descuento(self):
        """Calcula el precio con descuento aplicado"""
        if self.descuento > 0:
            return int(self.precio * (1 - self.descuento / 100))
        return self.precio
    
    @property
    def tiene_descuento(self):
        """Determina si el producto tiene descuento"""
        return self.descuento > 0


    def __str__(self):
        return self.nombre
    
class ProductoTalla(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='tallas')
    talla = models.CharField(max_length=10)  # Las tallas pueden ser S, M, L, XL o 40-44 para pantalones
    def __str__(self):
        return f"{self.producto.nombre} - Talla {self.talla}"
    
    
class ProductoTallaColor(models.Model):
    producto_talla = models.ForeignKey(ProductoTalla, on_delete=models.CASCADE, related_name='colores')
    color = models.ForeignKey(Color, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.producto_talla.producto.nombre} - {self.producto_talla.talla} - {self.color.nombre}"


class ProductoImagen(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to='productos/')  # Carpeta donde se guardarán las imágenes

    def __str__(self):
        return f"Imagen de {self.producto.nombre}"
    
class OpinionCliente(models.Model):
        producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='opiniones')
        user = models.ForeignKey(User, on_delete=models.CASCADE)  # opinion la venta con un usuario
        opinion = models.TextField()
        valoracion = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')])
        created_at = models.DateTimeField(auto_now_add=True)  # Campo para la fecha de creación

        def __str__(self):
            return f'Opinión de {self.user.username} sobre {self.producto.nombre}'  # Acceso al nombre del producto usando self.producto.name

class Pago(models.Model):
    ESTADO_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('confirmado', 'Confirmado'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente')
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pago {self.id} - {self.estado}"


class Venta(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Relacionamos la venta con un usuario
    fecha = models.DateTimeField(auto_now_add=True)  # Fecha de la venta
    total = models.DecimalField(max_digits=10, decimal_places=0, default=0)  # Total de la venta, calculado automáticamente
    pago = models.OneToOneField(Pago, null=True, blank=True, on_delete=models.SET_NULL)  # Relacionamos con el pago (uno a uno)
    envio = models.CharField(max_length=20, choices=[('envio', 'Envío a domicilio'), ('retiro', 'Retiro en tienda')], default='envio')

    def calcular_total(self):
        """Método para calcular el total de la venta sumando los subtotales de las líneas de venta"""
        self.total = sum(linea.subtotal() for linea in self.lineas.all())
        self.save()

    def __str__(self):
        return f"Venta {self.id} - Usuario: {self.user.username}"
    
    def save(self, *args, **kwargs):
        """El número de control es el ID de la venta"""
        super().save(*args, **kwargs)  # Guardamos primero para generar el ID
    
    
class LineaVenta(models.Model):
    venta = models.ForeignKey('Venta', on_delete=models.CASCADE, related_name='lineas')  # Relaciona con la venta principal
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)  # El producto vendido
    talla = models.ForeignKey(ProductoTalla, null=True, blank=True, on_delete=models.SET_NULL)  # La talla del producto, si aplica
    color = models.ForeignKey(Color, null=True, blank=True, on_delete=models.SET_NULL)  # El color del producto en esta venta
    cantidad = models.PositiveIntegerField()  # Cantidad de este producto en la venta
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=0)  # Precio por unidad al momento de la venta

    def __str__(self):
        return f"{self.producto.nombre} - {self.cantidad} unidades"

    def subtotal(self):
        """Calcula el subtotal de esta línea de venta (cantidad * precio_unitario)"""
        return round(self.cantidad * self.precio_unitario)
    @property
    def total_formateado(self):
        """Devuelve el total formateado"""
        return f"{self.subtotal()}"  # Si deseas un formato diferente, cámbialo aquí

    
class Contacto(models.Model):
    contact_form_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    customer_name = models.CharField(max_length=64)
    customer_email = models.EmailField()
    message = models.TextField()
    contacted = models.BooleanField(default=False)  # Campo para indicar si el mensaje ha sido contactado
    date_contacted = models.DateTimeField(null=True, blank=True)  # Fecha y hora en que se contactó al cliente 
  
    def __str__(self):
        return f"Formulario de Contacto - {self.contact_form_uuid}"
    

