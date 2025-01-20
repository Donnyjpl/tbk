from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify  # Utilidad para crear el slug automáticamente
import uuid

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    rut = models.CharField(max_length=12, unique=True)  # RUT (Ej: 12.345.678-9)
    telefono = models.CharField(max_length=15)  # Teléfono
    direccion = models.CharField(max_length=255)  # Dirección

    def __str__(self):
        return f"Perfil de {self.user.username}"
    
class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    def __str__(self):
        return self.nombre

class Producto(models.Model):
    marca = models.CharField(max_length=100)
    nombre = models.CharField(max_length=255)
    precio =  models.IntegerField()
    activo = models.BooleanField(default=True)  # Nuevo campo activo para indicar si la talla está disponible
    slug = models.SlugField(unique=True, blank=True)  # Slug único y automáticamente generado
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, null=True, blank=True)  # Permite nulos
    descripcion = models.TextField(max_length=255, null=True)
    
    def save(self, *args, **kwargs):
        # Generar el slug automáticamente si no se ha proporcionado
        if not self.slug:
            self.slug = slugify(self.nombre)
        super(Producto, self).save(*args, **kwargs)


    def __str__(self):
        return self.nombre
    

    
class ProductoTalla(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='tallas')
    talla = models.CharField(max_length=10)  # Las tallas pueden ser S, M, L, XL o 40-44 para pantalones
    cantidad = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.producto.nombre} - Talla {self.talla}"

    
class ProductoImagen(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to='productos/')  # Carpeta donde se guardarán las imágenes

    def __str__(self):
        return f"Imagen de {self.producto.nombre}"
    
    

class Factura(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    
    def procesar_factura(self):
        self.producto.actualizar_stock(self.cantidad)

    def __str__(self):
        return f"Factura {self.id} - {self.producto.nombre}"

class Venta(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Relacionamos la venta con un usuario
    
    def procesar_venta(self):
        self.producto.reducir_stock(self.cantidad)

    def __str__(self):
        return f"Venta {self.id} - {self.producto.nombre} - Usuario: {self.user.username}"
    
class Contacto(models.Model):
    contact_form_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    customer_name = models.CharField(max_length=64)
    customer_email = models.EmailField()
    message = models.TextField()
    contacted = models.BooleanField(default=False)  # Campo para indicar si el mensaje ha sido contactado
    date_contacted = models.DateTimeField(null=True, blank=True)  # Fecha y hora en que se contactó al cliente 
  
    def __str__(self):
        return f"Formulario de Contacto - {self.contact_form_uuid}"
