# views.py
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView,ListView,DetailView
from .models import Producto, ProductoImagen,ProductoTalla,Categoria,Profile
from .forms import ProductoForm, ProductoImagenForm, ProductoFilterForm,ContactoForm,ProductoTallaForm,LoginForm
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
from .models import Producto, ProductoImagen, ProductoTalla
from .forms import ProductoForm
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.http import JsonResponse

#usuario
from .forms import ProfileForm
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import UpdateView
from .models import Profile
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login


from django.contrib.auth.views import (PasswordResetConfirmView, PasswordResetDoneView, PasswordResetCompleteView)
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.contrib.auth.models import User
from django.views.generic import ListView
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.core.mail import send_mail


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

        print(f"Producto actual ID: {producto.id}")
        related_products = Producto.objects.filter(categoria=producto.categoria).exclude(id=producto.id)[:10]
        print(related_products)
        
        # Agregar las imágenes a cada producto relacionado (solo para visualización en el template)
        for related_product in related_products:
            related_product.imagenes_list = related_product.imagenes.all()  # Agrega las imágenes al producto relacionado

        # Agregar productos relacionados al contexto
        context['productos_relacionados'] = related_products
        

        # Acceder a las imágenes y tallas asociadas al producto
        producto.imagenes_list = producto.imagenes.all()
        producto.tallas_list = producto.tallas.all()

        return context
    
# Vista de contacto
def contacto(request):
    if request.method == 'POST':
        formm = ContactoForm(request.POST)
        if formm.is_valid():
            formm.save()  # Guarda el formulario en la base de datos si es válido
            return HttpResponseRedirect('success')  # Redirige a donde sea apropiado después de enviar el formulario
    else:
        formm = ContactoForm()
    return render(request, 'contacto.html', {'formm': formm})


def success(request):
    return render(request, 'registro_exitoso.html')


def agregar_al_carrito(request, slug):
    # Obtener el producto usando el slug
    producto = get_object_or_404(Producto, slug=slug)
    
    # Obtener el carrito de la sesión o inicializarlo si no existe
    carrito = request.session.get('carrito', {})

    # Si el producto ya está en el carrito, incrementar su cantidad
    if str(slug) in carrito:
        carrito[str(slug)]['cantidad'] += 1
    else:
        # Si no, agregarlo con cantidad 1
        carrito[str(slug)] = {
            'nombre': producto.nombre,
            'precio': str(producto.precio),
            'cantidad': 1,
            'slug': producto.slug,  # Guardamos el slug para futuras referencias
        }

    # Guardar el carrito de vuelta en la sesión
    request.session['carrito'] = carrito

    # Redirigir a la página del carrito
    return redirect('ver_carrito')


def ver_carrito(request):
    # Obtener el carrito de la sesión
    carrito = request.session.get('carrito', {})
    
    # Calcular el total y la cantidad total de productos
    total = 0
    cantidad_total = 0  # Nueva variable para la cantidad total de productos
    
    for item in carrito.values():
        total += float(item['precio']) * item['cantidad']
        cantidad_total += item['cantidad']  # Sumar la cantidad de cada producto
    
    return render(request, 'carrito/carrito.html', {
        'carrito': carrito,
        'total': total,
        'cantidad_total': cantidad_total,  # Pasar la cantidad total al contexto
    })
    
def eliminar_del_carrito(request, slug):
    # Obtener el carrito de la sesión
    carrito = request.session.get('carrito', {})
    
    # Eliminar el producto del carrito
    if str(slug) in carrito:
        del carrito[str(slug)]
    
    # Guardar el carrito actualizado
    request.session['carrito'] = carrito
    
    return redirect('ver_carrito')

def actualizar_carrito(request, slug):
    cantidad = int(request.GET.get('cantidad', 1))  # Tomamos la cantidad pasada en la URL (GET)
    
    # Obtener el producto
    producto = Producto.objects.get(slug=slug)
    
    # Obtener el carrito actual
    carrito = request.session.get('carrito', {})

    # Si el producto ya está en el carrito, actualizamos la cantidad
    if slug in carrito:
        carrito[slug]['cantidad'] = cantidad
    else:
        # Si no está en el carrito, lo agregamos
        carrito[slug] = {
            'nombre': producto.nombre,
            'precio': str(producto.precio),
            'cantidad': cantidad
        }

    # Guardamos el carrito de nuevo en la sesión
    request.session['carrito'] = carrito

    # Respondemos con un JSON indicando que la actualización fue exitosa
    return JsonResponse({'success': True, 'cantidad': cantidad})

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
