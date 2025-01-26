# views.py
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView,ListView,DetailView
from .models import Producto, ProductoImagen,ProductoTalla,Categoria,Profile,Venta
from .forms import ProductoForm, ProductoImagenForm, ProductoFilterForm,ContactoForm,ProductoTallaForm,LoginForm,OpinionClienteForm
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.core.paginator import Paginator
from .forms import CustomUserCreationForm
from django import forms  # Aquí debes importar forms
from django.contrib.auth import logout
# @method_decorator(login_required, name='dispatch')
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .models import Producto, ProductoImagen, ProductoTalla,OpinionCliente
from .forms import ProductoForm
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.http import JsonResponse
import mercadopago
#usuario
from .forms import ProfileForm
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import UpdateView
from .models import Profile
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login

from django.conf import settings
from django.contrib.auth.views import (PasswordResetConfirmView, PasswordResetDoneView, PasswordResetCompleteView)
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.contrib.auth.models import User
from django.views.generic import ListView
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import smart_str
from django.core.mail import EmailMessage
from django.core.mail import EmailMultiAlternatives



def dejar_opinion(request, slug):
    producto = get_object_or_404(Producto, slug=slug)  # Obtener el producto por su slug

    if request.method == 'POST':
        form = OpinionClienteForm(request.POST)
        if form.is_valid():
            # Asignar el producto a la opinión
            opinion = form.save(commit=False)
            opinion.producto = producto  # Asociar la opinión con el producto
            opinion.save()  # Guardar la opinión

            # Mensaje de éxito
            messages.success(request, '¡Gracias por tu opinión!')
            return redirect('detalle_producto', slug=producto.slug)  # Redirigir a la página del producto
    else:
        form = OpinionClienteForm()

    return render(request, 'productos/dejar_opinion.html', {
        'form': form,
        'producto': producto
    })
    
    
    
def procesar_pago_success(request):
    # Obtener el carrito de la sesión
    carrito = request.session.get('carrito', {})

    # Si el carrito está vacío, redirigir a la tienda o mostrar un mensaje adecuado
    if not carrito or len(carrito) == 0:
        return redirect('shop')  # O puedes redirigir a una página de error o de la tienda

    # Calcular el total de la compra
    total = 0
    for item in carrito.values():
        total += float(item['precio']) * item['cantidad']

    # Crear las ventas
    ventas = []
    for slug, item in carrito.items():
        producto = Producto.objects.get(slug=slug)  # Obtener el producto desde la base de datos

        # Crear una venta para cada producto
        venta = Venta.objects.create(
            producto=producto,
            cantidad=item['cantidad'],
            user=request.user
        )
        ventas.append(venta)

    # Vaciar el carrito
    request.session['carrito'] = {}

    # Mostrar un mensaje de éxito
    messages.success(request, f'Pago exitoso por un total de ${total}. ¡Gracias por tu compra!')

    # Obtener solo las ventas de la última compra del usuario
    last_venta = ventas[-1]  # La última venta es la de la compra actual
    ventas = Venta.objects.filter(user=request.user, fecha=last_venta.fecha)

    # Calcular el total final
    total = sum(venta.producto.precio * venta.cantidad for venta in ventas)
    
     # Obtener los datos del perfil del usuario
     # Obtener los datos del perfil del usuario
    profile = request.user.profile  # Asegúrate de que el usuario tenga un perfil asociado
    rut = profile.rut
    telefono = profile.telefono
    direccion = profile.direccion
    
    # Enviar correo al usuario con los detalles de la compra
    subject = 'Confirmación de tu compra en Nuestro Sitio'
    message = render_to_string('carrito/compra_confirmacion.html', {
        'ventas': ventas,
        'total': total,
        'usuario': request.user
        
    })

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [request.user.email]
    )

    # Enviar correo al administrador (correo del contacto del administrador)
    admin_email = 'donnyjpl@gmail.com'  # Cambiar al correo del administrador
    admin_subject = 'Nuevo Pedido Realizado'
    admin_message = render_to_string('correos/nuevo_pedido.html', {
        'ventas': ventas,
        'total': total,
        'usuario': request.user,
        'rut': rut,
        'telefono': telefono,
        'direccion': direccion,
    })

    send_mail(
        admin_subject,
        admin_message,
        settings.DEFAULT_FROM_EMAIL,
        [admin_email]
    )

    # Redirigir a la misma página para mostrar el resumen de la compra
    return render(request, 'carrito/compra_confirmacion.html', {
        'ventas': ventas,
        'total': total,
    })


def agregar_al_carrito(request, slug):
    # Obtener el producto usando el slug
    producto = get_object_or_404(Producto, slug=slug)
    talla_id = request.POST.get('talla')  # Asegúrate de que estás obteniendo correctamente la talla

    # Verificar si la talla existe para el producto
    try:
        talla = producto.tallas.get(id=talla_id)
    except ProductoTalla.DoesNotExist:
        messages.error(request, 'La talla seleccionada no existe para este producto.')
        return redirect('producto_detalle', slug=slug)  # Redirigir a la página del producto

    # Obtener el carrito de la sesión o inicializarlo si no existe
    carrito = request.session.get('carrito', {})

    # Verificar si el producto ya está en el carrito
    if str(slug) in carrito:
        if str(talla_id) in carrito[str(slug)]['tallas']:
            carrito[str(slug)]['tallas'][str(talla_id)]['cantidad'] += 1
        else:
            carrito[str(slug)]['tallas'][str(talla_id)] = {
                'talla': talla.talla,
                'precio': str(producto.precio),
                'cantidad': 1,
            }
    else:
        carrito[str(slug)] = {
            'nombre': producto.nombre,
            'precio': str(producto.precio),
            'cantidad': 1,
            'slug': producto.slug,
            'tallas': {
                str(talla_id): {
                    'talla': talla.talla,
                    'precio': str(producto.precio),
                    'cantidad': 1,
                }
            }
        }

    # Guardar el carrito en la sesión
    request.session['carrito'] = carrito

    # Agregar un mensaje de éxito
    messages.success(request, f'{producto.nombre} con talla {talla.talla} se ha agregado al carrito con éxito.')
    return redirect('ver_carrito')  # Redirige a la vista del carrito



def ver_carrito(request):
    carrito = request.session.get('carrito', {})
    print(carrito)  # Ver el contenido del carrito

    total = 0
    for producto_slug, producto_data in carrito.items():
        # Asegúrate de que 'tallas' está en el diccionario
        if 'tallas' in producto_data:
            for talla_id, talla_data in producto_data['tallas'].items():
                total += float(talla_data['precio']) * talla_data['cantidad']
        else:
            print(f"El producto {producto_slug} no tiene tallas.")
    
    return render(request, 'carrito/carrito.html', {'carrito': carrito, 'total': total})
   
def eliminar_del_carrito(request, slug, talla_id):
    producto = get_object_or_404(Producto, slug=slug)
    talla = get_object_or_404(ProductoTalla, id=talla_id, producto=producto)

    # Obtener el carrito de la sesión
    carrito = request.session.get('carrito', {})

    # Eliminar el producto de la talla seleccionada
    if str(slug) in carrito:
        if str(talla_id) in carrito[str(slug)]['tallas']:
            del carrito[str(slug)]['tallas'][str(talla_id)]
            if not carrito[str(slug)]['tallas']:  # Si ya no hay tallas, eliminar el producto
                del carrito[str(slug)]
            messages.success(request, f'{producto.nombre} con talla {talla.talla} ha sido eliminado del carrito.')
        else:
            messages.error(request, 'Error: Talla no encontrada en el carrito.')
    else:
        messages.error(request, 'Error: Producto no encontrado en el carrito.')

    # Guardar el carrito actualizado en la sesión
    request.session['carrito'] = carrito
    return redirect('ver_carrito')  # Redirige al carrito después de eliminar


def actualizar_carrito(request, slug, talla_id):
    producto = get_object_or_404(Producto, slug=slug)
    talla = get_object_or_404(ProductoTalla, id=talla_id, producto=producto)

    # Obtener el carrito de la sesión
    carrito = request.session.get('carrito', {})

    # Verificar si el producto y la talla están en el carrito
    if str(slug) in carrito and str(talla_id) in carrito[str(slug)]['tallas']:
        # Actualizar la cantidad de la talla
        cantidad = int(request.POST.get('cantidad', 1))
        carrito[str(slug)]['tallas'][str(talla_id)]['cantidad'] = cantidad

        # Guardar el carrito en la sesión
        request.session['carrito'] = carrito
        messages.success(request, f"La cantidad del producto {producto.nombre} con talla {talla.talla} ha sido actualizada.")
    else:
        messages.error(request, "El producto o talla no está en tu carrito.")

    return redirect('ver_carrito')

@login_required
def procesar_pago(request):
    # Obtener el carrito de la sesión
    carrito = request.session.get('carrito', {})
    
    # Verificar si el carrito está vacío
    if not carrito or sum(item['cantidad'] for item in carrito.values()) == 0:
        return JsonResponse({'error': 'El carrito está vacío o no tiene productos válidos.'}, status=400)
    
    # Calcular el total y la cantidad total de productos
    total = 0
    cantidad_total = 0
    for item in carrito.values():
        total += float(item['precio']) * item['cantidad']
        cantidad_total += item['cantidad']
        

    # Configuración del SDK de Mercado Pago
    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
    
    # Crear la preferencia de pago
    preference_data = {
        "items": [
            {
                "title": "Compra en nuestra tienda TBK",  # Nombre del producto (puedes personalizarlo)
                "quantity": 1,  # Cantidad total de productos en el carrito
                "unit_price": total  # Total del carrito
            }
        ],
        "back_urls": {
             "success": request.build_absolute_uri('/web/procesar_pago/exito'),  # URL absoluta
             "failure": request.build_absolute_uri('/web/procesar_pago/failure'),
             "pending": request.build_absolute_uri('/web/procesar_pago/pending'),
        },
        "auto_return": "approved",  # La redirección automática cuando el pago es aprobado
    }

    # Intentar crear la preferencia
    try:
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response.get("response", {})
        
        
        # Imprimir la respuesta de Mercado Pago para depuración

        # Verificar si la preferencia fue creada correctamente
        if 'init_point' in preference:
            # Redirigir al usuario a la página de pago de Mercado Pago
            return redirect(preference["init_point"])
        else:
            # Si no se pudo crear la preferencia, retornar un mensaje de error
            error_message = preference_response.get("message", "Error desconocido.")
            return JsonResponse({'error': error_message}, status=400)

    except Exception as e:
        # Si ocurre un error en el proceso de creación de la preferencia
        return JsonResponse({'error': str(e)}, status=500)
    

def failure(request):
    return render(request, 'carrito/compra_fallo.html')

def pending(request):
    return render(request, 'carrito/compra_pendiente.html')

def custom_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():

            # Recuperar los datos del formulario
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            # Intentar autenticar al usuario
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'¡Bienvenido de nuevo, {user.username}!')
                return redirect('index')  # Redirige después de login exitoso
            else:
                messages.error(request, 'Usuario o contraseña incorrectos.')  # Mensaje de error
        else:
            messages.error(request, 'Formulario inválido')  # En caso de que el formulario no sea válido
    else:
        form = LoginForm()
    return render(request, 'registration/login.html', {'form': form})

def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save()  # Guardar el producto
            messages.success(request, f'Producto {producto.nombre} creado exitosamente.')
            return redirect('subir_imagenes', slug=producto.slug)
    else:
        form = ProductoForm()

    return render(request, 'productos/crear_producto.html', {'form': form})

# views.py
def subir_imagenes(request, slug):
    producto = get_object_or_404(Producto, slug=slug)  # Recuperamos el producto por su slug
    if request.method == 'POST':
        form = ProductoImagenForm(request.POST, request.FILES)  # Para manejar archivos
        if form.is_valid():
            imagen = form.save()  # Guardamos la imagen
            messages.success(request, 'Imagen subida exitosamente.')
            # Si todas las imágenes se han subido, redirigir a la página para agregar tallas
            return redirect('agregar_tallas', slug=producto.slug)  # Cambiar a 'agregar_tallas' después de subir imágenes
    else:
        form = ProductoImagenForm(initial={'producto': producto})

    return render(request, 'productos/subir_imagenes.html', {'form': form, 'producto': producto})

def agregar_tallas(request, slug):
    producto = get_object_or_404(Producto, slug=slug)  # Recuperamos el producto por su slug

    if request.method == 'POST':
        form = ProductoTallaForm(request.POST, producto=producto)  # Pasamos el producto al formulario como un argumento
        if form.is_valid():
            # Creamos una instancia del modelo ProductoTalla sin guardar todavía
            producto_talla = form.save(commit=False)
            producto_talla.producto = producto  # Asignamos el producto manualmente
            producto_talla.save()  # Guardamos el objeto ProductoTalla
            messages.success(request, f'Talla {form.cleaned_data["talla"]} agregada correctamente.')
            return redirect('producto_detalle', slug=producto.slug)  # Redirigir a la vista de detalles del producto
    else:
        form = ProductoTallaForm(producto=producto)  # Inicializamos el formulario pasando el producto

    return render(request, 'productos/agregar_tallas.html', {'form': form, 'producto': producto})
    
    
def lista_productos(request):
    form = ProductoFilterForm(request.GET)  # Recibimos los datos del formulario a través de GET
    productos = Producto.objects.all()  # Comienza con todos los productos

    # Aplicar filtros según el formulario
    if form.is_valid():
        if form.cleaned_data.get('categoria'):
            productos = productos.filter(categorias=form.cleaned_data['categoria'])
        
        if form.cleaned_data.get('min_precio'):
            productos = productos.filter(precio__gte=form.cleaned_data['min_precio'])
        
        if form.cleaned_data.get('max_precio'):
            productos = productos.filter(precio__lte=form.cleaned_data['max_precio'])
             # Acceder a las imágenes y tallas de cada producto
    for producto in productos:
        producto.imagenes_list = producto.imagenes.all()  # Accede a las imágenes del producto
        producto.tallas_list = producto.tallas.all()  # Accede a las tallas del producto

    return render(request, 'producto_list.html', {'productos': productos, 'form': form})

    
    
def index(request):
    return render(request, 'index1.html')

def about(request):
    return render(request, 'about.html')


class ProductoListView(ListView):
    model = Producto
    template_name = 'shop.html'
    context_object_name = 'productos'
    paginate_by = 9  # Número de productos por página

    def get_queryset(self):
        queryset = Producto.objects.all()

        # Aplicar filtros según el formulario
        form = ProductoFilterForm(self.request.GET)
        if form.is_valid():
            categoria = form.cleaned_data.get('categoria')
            if categoria:
                queryset = queryset.filter(categoria=categoria)
            
            min_precio = form.cleaned_data.get('min_precio')
            if min_precio:
                queryset = queryset.filter(precio__gte=min_precio)
            
            max_precio = form.cleaned_data.get('max_precio')
            if max_precio:
                queryset = queryset.filter(precio__lte=max_precio)

        # Ordenar según el parámetro "order_by" en la URL
        order_by = self.request.GET.get('order_by')
        if order_by == 'name':
            queryset = queryset.order_by('nombre')
        elif order_by == 'item':
            queryset = queryset.order_by('slug')  # O cualquier otro campo relevante

        # Optimizar consultas
        queryset = queryset.prefetch_related('imagenes', 'tallas')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ProductoFilterForm(self.request.GET)  # Agregar el formulario a la vista
        return context


class producto_detalle(DetailView):
    model = Producto
    template_name = 'producto_detalle.html'
    context_object_name = 'producto'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Accede al producto actual
        producto = context['producto']
        related_products = Producto.objects.filter(categoria=producto.categoria).exclude(id=producto.id)[:10]
        
        # Agregar las imágenes a cada producto relacionado (solo para visualización en el template)
        for related_product in related_products:
            related_product.imagenes_list = related_product.imagenes.all()  # Agrega las imágenes al producto relacionado

        # Agregar productos relacionados al contexto
        context['productos_relacionados'] = related_products
        

        # Acceder a las imágenes y tallas asociadas al producto
        producto.imagenes_list = producto.imagenes.all()
        producto.tallas_list = producto.tallas.all()
        
         # Aquí ya estás calculando otros elementos, agrega el rango de 1 a 5
        context['rango_estrellas'] = range(1, 6)
        
        # Opcional: Agregar opiniones/valoraciones (si las tienes)
         # Mostrar las opiniones del producto
        producto.opiniones_list = OpinionCliente.objects.filter(producto=producto).order_by('-created_at')[:3]
        
        # Si el usuario está autenticado, permitir dejar una opinión
        # Si el usuario está autenticado, permitir dejar una opinión
        if self.request.user.is_authenticated:
            # Verificar si el usuario ya ha dejado una opinión sobre el producto
            if OpinionCliente.objects.filter(producto=producto, user=self.request.user).exists():
                context['usuario_tiene_opinion'] = True  # El usuario ya ha dejado una opinión
            else:
                context['opinion_form'] = OpinionClienteForm()  # Formulario para dejar opinión

        return context
 
    def post(self, request, *args, **kwargs):
        producto = self.get_object()  # Obtener el producto desde la URL
        if request.user.is_authenticated:
            # Verificar si el usuario ya dejó una opinión
            if OpinionCliente.objects.filter(producto=producto, user=request.user).exists():
                messages.error(request, '¡Ya has dejado una opinión sobre este producto!')
                return redirect('producto_detalle', slug=producto.slug)

            form = OpinionClienteForm(request.POST)
            if form.is_valid():
                # Crear una nueva opinión en la base de datos
                OpinionCliente.objects.create(
                    producto=producto,
                    user=request.user,
                    opinion=form.cleaned_data['opinion'],
                    valoracion=form.cleaned_data['valoracion']
                )
                messages.success(request, '¡Gracias por dejar tu opinión!')
                return redirect('producto_detalle', slug=producto.slug)

        return redirect('producto_detalle', slug=producto.slug)
    
# Vista de contacto
def contacto(request):
    if request.method == 'POST':
        formm = ContactoForm(request.POST)
        if formm.is_valid():
            # Guarda el formulario en la base de datos si es necesario
            formm.save()  # Este paso es opcional dependiendo de si deseas almacenar los datos

            # Obtener los datos del formulario
            nombre = formm.cleaned_data['customer_name']
            correo = formm.cleaned_data['customer_email']
            mensaje = formm.cleaned_data['message']
            
            
            
            # Crear el correo en formato texto plano y HTML
            subject = f'Nuevo mensaje de contacto de {nombre}'
            from_email = correo
            to_email = ['donnyjpl@gmail.com']  # Reemplaza con el correo del administrador

            text_content = f'Nuevo mensaje de contacto de {nombre}\n\nMensaje: {mensaje}'
            html_content = f"""
                <p><strong>Nuevo mensaje de contacto de {nombre}</strong></p>
                <p><strong>Mensaje:</strong></p>
                <p>{mensaje}</p>
            """

            # Crear el objeto de correo con texto plano y HTML
            email = EmailMultiAlternatives(
                subject,
                text_content,
                from_email,
                to_email,
            )

            # Adjuntar el contenido HTML al correo
            email.attach_alternative(html_content, "text/html")

            # Enviar el correo
            email.send(fail_silently=False)
            
            
            # Mensaje de éxito para el usuario
            messages.success(request, 'Tu mensaje ha sido enviado al administrador. ¡Gracias!')
            
            # Redirige a la página que desees
            return redirect('shop')  # O usa otro nombre de URL adecuado, como 'success', si es necesario.
    else:
        formm = ContactoForm()

    # Renderiza la página con el formulario
    return render(request, 'contacto.html', {'formm': formm})

def successs(request):
    return render(request, 'registro_exitoso.html')


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Profile
    fields = ['telefono', 'direccion']
    template_name = 'usuario/edit_profile.html'
    success_url = reverse_lazy('profile')  # Redirige al perfil después de la actualización
    
    def get_object(self, queryset=None):
        """
        Obtiene el perfil del usuario logueado.
        Si el perfil no existe, lo crea.
        """
        try:
            return self.request.user.profile
        except Profile.DoesNotExist:
            # Si no existe el perfil, lo creamos y lo asociamos al usuario
            profile = Profile.objects.create(user=self.request.user)
            return profile

    def get_form(self, form_class=None):
        """
        Sobrescribimos este método para incluir los campos adicionales del usuario (nombre, apellido, correo, direccion).
        """
        form = super().get_form(form_class)
        
        # Añadir los campos del User al formulario de actualización
        form.fields['username'] = forms.CharField(max_length=150)
        form.fields['email'] = forms.EmailField()
        form.fields['first_name'] = forms.CharField(max_length=30)
        form.fields['last_name'] = forms.CharField(max_length=30)
        
        # Campo dirección con tamaño personalizado (más grande)
        form.fields['direccion'] = forms.CharField(
            widget=forms.Textarea(attrs={'rows': 5, 'cols': 40})  # Cambié el tamaño del TextArea
        )

        # Inicializamos los valores de los campos con los valores del usuario logueado
        form.initial['username'] = self.request.user.username
        form.initial['email'] = self.request.user.email
        form.initial['first_name'] = self.request.user.first_name
        form.initial['last_name'] = self.request.user.last_name
        form.initial['direccion'] = self.request.user.profile.direccion  # Inicializamos direccion desde el perfil

        return form

    def form_valid(self, form):
        """
        Sobrescribimos este método para guardar los datos del User además de los del Profile.
        """
        user = self.request.user
        # Validar que el email no esté registrado
        email = form.cleaned_data['email']
        if User.objects.filter(email=email).exclude(username=user.username).exists():
            form.add_error('email', 'Este correo electrónico ya está registrado.')
            return self.form_invalid(form)

        # Validar que el teléfono no esté registrado
        telefono = form.cleaned_data['telefono']
        if Profile.objects.filter(telefono=telefono).exclude(user=user).exists():
            form.add_error('telefono', 'Este número de teléfono ya está registrado.')
            return self.form_invalid(form)

        # Guardar los campos de usuario
        user.first_name = form.cleaned_data['first_name']
        user.last_name = form.cleaned_data['last_name']
        user.email = email  # Asignar el email
        user.username = email  # Establecer el username como email si es necesario
        user.save()

        # Guardar los campos de perfil
        profile = form.save(commit=False)
        profile.user = user  # Asegurarse de que el perfil está vinculado al usuario
        profile.direccion = form.cleaned_data['direccion']  # Guardamos la dirección también
        profile.save()

        # Agregar un mensaje de éxito después de guardar los cambios
        messages.success(self.request, '¡Perfil actualizado correctamente!')

        return super().form_valid(form)
    
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            messages.success(request, '¡Cuenta registrada con éxito!')
            return redirect('login')  # Redirige a la página de éxito

        else:
            messages.error(request, 'Hubo un error en el registro. Por favor, corrige los errores.')

    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})

# Vista de registro exitoso
def registro_exitoso(request):
    return render(request, 'usuario/registro_exitoso.html')

def logout_view(request):
    logout(request)  # Cierra la sesión
    return redirect('index')  # Redirige a la página de inicio o a la página que desees

# Vista personalizada para solicitar el restablecimiento de contraseña
def custom_password_reset_request(request):
    if request.method == "POST":
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        if user:
            # Generar UID y token para el restablecimiento de contraseña
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            domain = request.get_host()
            reset_link = f"http://{domain}{reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})}"

            # Enviar el correo con el enlace de restablecimiento
            subject = "Restablecimiento de contraseña"
            message = f"""Hola {user.username},
Hemos recibido una solicitud para restablecer tu contraseña. Si no realizaste esta solicitud, puedes ignorar este correo.

Para restablecer tu contraseña, haz clic en el siguiente enlace:
<a href="{reset_link}">Restablecer contraseña</a>

Este enlace es válido solo por 24 horas.

Gracias,
Tu equipo"""

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
                html_message=message
            )
            
            return render(request, 'registration/password_reset_done.html')
        else:
            error_message = "No se encontró un usuario con ese correo electrónico."
            return render(request, 'registration/password_reset_form.html', {'error_message': error_message})

    return render(request, 'registration/password_reset_form.html')


# Vista personalizada para confirmar el restablecimiento de contraseña
class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['custom_message'] = "¡Tu contraseña ha sido restablecida con éxito!"
        return context

# Usamos las vistas por defecto para las siguientes dos etapas
class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'
    
    
@login_required
def profile_view(request):
    return render(request, 'usuario/profile.html')
