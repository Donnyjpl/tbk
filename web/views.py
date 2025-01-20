# views.py
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView,ListView,DetailView
from .models import Producto, ProductoImagen,ProductoTalla,Categoria
from .forms import ProductoForm, ProductoImagenForm, ProductoFilterForm,ContactoForm,ProductoTallaForm
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.core.paginator import Paginator


# @method_decorator(login_required, name='dispatch')
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .models import Producto, ProductoImagen, ProductoTalla
from .forms import ProductoForm
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.http import JsonResponse



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
        # Accede a las imágenes y tallas asociadas al producto
        producto = context['producto']
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
    
    # Calcular el total del carrito
    total = 0
    for item in carrito.values():
        total += float(item['precio']) * item['cantidad']

    return render(request, 'carrito/carrito.html', {
        'carrito': carrito,
        'total': total,
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