# Librerías estándar de Python
from decimal import Decimal
import mercadopago

# Librerías de Django
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, ListView, DetailView, View
from django.views.generic.edit import UpdateView
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordResetConfirmView, PasswordResetDoneView, PasswordResetCompleteView
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy, reverse
from django.db.models import Avg, Prefetch
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes, smart_str
from django.db.models import Prefetch
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from django import forms


# Modelos y formularios de tu aplicación
from .models import Producto, ProductoImagen, ProductoTalla, Categoria, Profile, Venta, LineaVenta, Pago, Color, OpinionCliente, ProductoTallaColor
from .forms import  CustomUserCreationForm,ProductoForm, ProductoImagenForm, ProductoFilterForm, ContactoForm, ProductoTallaForm, LoginForm, OpinionClienteForm, ColorForm, CategoriaForm, ProfileForm, ProductoTallaColorForm
# Mensajes de Django
from django.contrib import messages



def pagina_no_encontrada(request, exception):
    return render(request, '404.html', status=404)

class MisComprasView(LoginRequiredMixin, ListView):
    model = Venta
    template_name = 'compras/mis_compras.html'
    context_object_name = 'ventas'
    paginate_by = 30

    def get_queryset(self):
        lineas_venta = LineaVenta.objects.prefetch_related('producto', 'talla')
        if self.request.user.is_staff:
            ventas = Venta.objects.prefetch_related(Prefetch('lineas', queryset=lineas_venta)).order_by('-fecha')
        else:
            ventas = Venta.objects.filter(user=self.request.user).prefetch_related(Prefetch('lineas', queryset=lineas_venta)).order_by('-fecha')
        return ventas

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Aquí recuperamos el perfil del usuario (si lo tiene)
        for venta in context['ventas']:
            venta.usuario_direccion = venta.user.profile.direccion if hasattr(venta.user, 'profile') else "No disponible"
            venta.usuario_rut = venta.user.profile.rut if hasattr(venta.user, 'profile') else "No disponible"
            venta.usuario_telefono = venta.user.profile.telefono if hasattr(venta.user, 'profile') else "No disponible"
            venta.numero_control = venta.id  # Usamos el ID como número de control
            # Obtener el tipo de envío
            venta.tipo_envio = venta.envio if hasattr(venta, 'envio') else 'retiro'  # Si no hay envío, es retiro


            # Agregar total de la venta
            venta.total_venta = sum(linea.precio_unitario * linea.cantidad for linea in venta.lineas.all())
            venta.total_venta_formateado = venta.total_venta

            # Agregar el estado del pago
            if venta.pago:  # Verificamos si la venta tiene un pago asociado
                venta.estado_pago = venta.pago.estado
            else:
                venta.estado_pago = "No disponible"
        return context

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
    items = []  # Aquí se guardarán los productos y tallas del carrito
    for producto_slug, producto_data in carrito.items():
        if 'tallas' in producto_data:  # Si el producto tiene tallas
            for talla_id, talla_data in producto_data['tallas'].items():
                # Calcular el total del carrito con tallas y cantidades
                total += float(talla_data['precio']) * talla_data['cantidad']
                cantidad_total += talla_data['cantidad']
                
                # Agregar cada talla como un item en los items de la preferencia
                items.append({
                    "title": f"{producto_data['nombre']} - Talla {talla_data['talla']}",  # Nombre con la talla
                    "quantity": talla_data['cantidad'],  # Cantidad de esta talla
                    "unit_price": float(talla_data['precio'])  # Precio de la talla
                })
        else:
            # Si no tiene tallas, agregar solo el producto
            total += float(producto_data['precio']) * producto_data['cantidad']
            cantidad_total += producto_data['cantidad']
            
            # Agregar el producto como un item en los items de la preferencia
            items.append({
                "title": producto_data['nombre'],
                "quantity": producto_data['cantidad'],
                "unit_price": float(producto_data['precio'])
            })
            
            
    envio = request.session.get('envio', 'retiro')
    if envio == 'envio':
        total += 5000  # Costo de envío
            

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
             "success": request.build_absolute_uri('/procesar_pago/exito'),  # URL absoluta
             "failure": request.build_absolute_uri('/procesar_pago/failure'),
             "pending": request.build_absolute_uri('/procesar_pago/pending'),
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

@login_required
def procesar_pago_transferencia(request):
    carrito = request.session.get('carrito', {})

    if not carrito or len(carrito) == 0:
        return redirect('shop')

    total = Decimal('0.00')  # Usar Decimal para evitar problemas con los decimales
    ventas = []  # Lista para registrar las ventas

    # Crear la venta principal y asociarla al usuario
    venta = Venta.objects.create(user=request.user)  # Crear una venta vacía

    # Procesar cada producto en el carrito
    for producto_slug, producto_data in carrito.items():
        try:
            producto = Producto.objects.get(slug=producto_slug)  # Obtener el producto de la DB
        except Producto.DoesNotExist:
            continue  # Si el producto no existe, lo saltamos

        if 'tallas' in producto_data:
            for talla_id, talla_data in producto_data['tallas'].items():
                talla = ProductoTalla.objects.get(id=talla_id)

                # Asegurarse de que los precios sean de tipo Decimal
                precio_unitario = Decimal(str(talla_data['precio']))  # Convertir a Decimal
                precio_total = Decimal(str(talla_data['precio'])) * Decimal(talla_data['cantidad'])

                # Procesar los colores si existen en esta talla
                if 'colores' in talla_data:
                    for color_id, color_data in talla_data['colores'].items():
                        color_nombre = color_data.get('color', 'N/A')  # Obtener el nombre del color
                        
                        # Obtener el objeto Color correspondiente al nombre
                        try:
                            color = Color.objects.get(nombre=color_nombre)
                        except Color.DoesNotExist:
                            color = None  # Si no existe el color, lo dejamos como None
                            messages.warning(request, f"El color '{color_nombre}' no está disponible para el producto {producto.nombre}.") 

                # Crear la línea de venta para este producto
                if color:  # Solo crear la línea si se obtuvo un color válido
                    linea_venta = LineaVenta.objects.create(
                        venta=venta,
                        producto=producto,
                        cantidad=talla_data['cantidad'],
                        talla=talla,
                        color=color,  # Ahora asignamos la instancia de Color
                        precio_unitario=precio_unitario  # Guardar el precio unitario
                    )

                    # Calcular total
                    total += precio_total  # Sumamos a total (asegurado que es Decimal)

                    ventas.append({
                        'producto': producto,
                        'cantidad': talla_data['cantidad'],
                        'talla': talla,
                        'color': color_nombre,  # Guardar el nombre del color en la venta
                        'precio': precio_unitario,
                        'precio_total': precio_total
                    })
                
    # Obtener el costo de envío de la sesión (si es aplicable)
    envio = request.session.get('envio', 'retiro')  # Valor predeterminado: retiro en tienda
    venta.envio = envio  # Guardamos el tipo de envío en la venta
    if envio == 'envio':
        total += Decimal('5000')  # Costo de envío, lo agregamos al total

    # Crear el pago pendiente
    pago = Pago.objects.create(user=request.user, total=total, estado='pendiente')
    
    # Asociar el pago con la venta
    venta.pago = pago  # Establecemos la relación en la venta
    venta.save()  # Guardamos la venta con el pago asociado

    # Vaciar el carrito de la sesión
    request.session['carrito'] = {}

    # Mostrar un mensaje de éxito
    messages.success(request, f'Pedido registrado con éxito. Tu pago está pendiente de confirmación.')

    # Obtener los datos del perfil del usuario
    profile = request.user.profile
    rut = profile.rut
    telefono = profile.telefono
    direccion = profile.direccion
    metodo_pago='transferencia'

    # Enviar correo al cliente
    #email_prueba = 'info@tbkdesire.cl'
    email_cliente = request.user.email
    subject = 'Confirmación de tu pedido - Transferencia Bancaria'
    message = render_to_string('correos/compra_confirmacion_trans.html', {
        'ventas': ventas,
        'total': total,
        'usuario': request.user,
        'envio': venta.envio
    })

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email_cliente],
        html_message=message
    )

    # Enviar correo al administrador
    admin_email = 'info@tbkdesire.cl'  # Correo del administrador
    admin_subject = 'Nuevo Pedido Realizado - Transferencia Bancaria'
    admin_message = render_to_string('correos/nuevo_pedido.html', {
        'ventas': ventas,
        'total': total,
        'usuario': request.user,
        'rut': rut,
        'telefono': telefono,
        'direccion': direccion,
        'metodo_pago': metodo_pago,
        'envio': venta.envio
    })

    send_mail(
        admin_subject,
        admin_message,
        settings.DEFAULT_FROM_EMAIL,
        [admin_email],
        html_message=admin_message
    )

    # Renderizar la página de confirmación después del pago
    return render(request, 'carrito/compra_confirmacion.html', {
        'ventas': ventas,
        'total': total,
        'pago_id': pago.id
    })

@login_required
def procesar_pago_success(request):
    carrito = request.session.get('carrito', {})

    if not carrito or len(carrito) == 0:
        return redirect('shop')

    total = Decimal('0.00')  # Usar Decimal para evitar problemas con los decimales
    ventas = []  # Lista para registrar las ventas

    # Crear la venta principal y asociarla al usuario
    venta = Venta.objects.create(user=request.user)  # Crear una venta vacía

    # Procesar cada producto en el carrito
    for producto_slug, producto_data in carrito.items():
        try:
            producto = Producto.objects.get(slug=producto_slug)  # Obtener el producto de la DB
        except Producto.DoesNotExist:
            continue  # Si el producto no existe, lo saltamos

        if 'tallas' in producto_data:
            for talla_id, talla_data in producto_data['tallas'].items():
                talla = ProductoTalla.objects.get(id=talla_id)

                # Asegurarse de que los precios sean de tipo Decimal
                precio_unitario = Decimal(str(talla_data['precio']))  # Convertir a Decimal
                precio_total = Decimal(str(talla_data['precio'])) * Decimal(talla_data['cantidad'])

                # Procesar los colores si existen en esta talla
                if 'colores' in talla_data:
                    for color_id, color_data in talla_data['colores'].items():
                        color_nombre = color_data.get('color', 'N/A')  # Obtener el nombre del color
                        
                        # Obtener el objeto Color correspondiente al nombre
                        try:
                            color = Color.objects.get(nombre=color_nombre)
                        except Color.DoesNotExist:
                            color = None  # Si no existe el color, lo dejamos como None
                            messages.warning(request, f"El color '{color_nombre}' no está disponible para el producto {producto.nombre}.") 

                # Crear la línea de venta para este producto
                if color:  # Solo crear la línea si se obtuvo un color válido
                    linea_venta = LineaVenta.objects.create(
                        venta=venta,
                        producto=producto,
                        cantidad=talla_data['cantidad'],
                        talla=talla,
                        color=color,  # Ahora asignamos la instancia de Color
                        precio_unitario=precio_unitario  # Guardar el precio unitario
                    )

                    # Calcular total
                    total += precio_total  # Sumamos a total (asegurado que es Decimal)

                    ventas.append({
                        'producto': producto,
                        'cantidad': talla_data['cantidad'],
                        'talla': talla,
                        'color': color_nombre,  # Guardar el nombre del color en la venta
                        'precio': precio_unitario,
                        'precio_total': precio_total
                    })
                    
    # Obtener el costo de envío de la sesión (si es aplicable)
    envio = request.session.get('envio', 'retiro')  # Valor predeterminado: retiro en tienda
    venta.envio = envio  # Guardamos el tipo de envío en la venta
    if envio == 'envio':
        total += Decimal('5000')  # Costo de envío, lo agregamos al total
                
    # Crear el pago pendiente
    pago = Pago.objects.create(user=request.user, total=total, estado='confirmado')
    # Asociar el pago con la venta
    venta.pago = pago  # Establecemos la relación en la venta
    venta.save()  # Guardamos la venta con el pago asociado

    # Vaciar el carrito de la sesión
    request.session['carrito'] = {}

    # Mostrar un mensaje de éxito
    messages.success(request, f'Pedido registrado con éxito. Tu pago está confirmado.')

    # Obtener los datos del perfil del usuario
    profile = request.user.profile
    rut = profile.rut
    telefono = profile.telefono
    direccion = profile.direccion

    # Enviar correo al cliente
    #email_prueba = 'info@tbkdesire.cl'
    email_cliente = request.user.email
    subject = 'Confirmación de tu pedido - Transferencia Bancaria'
    message = render_to_string('correos/compra_confirmacion.html', {
        'ventas': ventas,
        'total': total,
        'usuario': request.user,
        'envio': venta.envio
    })

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email_cliente],
        html_message=message
    )

    # Enviar correo al administrador
    admin_email = 'info@tbkdesire.cl'  # Correo del administrador
    admin_subject = 'Nuevo Pedido Realizado - Mercado Pago'
    admin_message = render_to_string('correos/nuevo_pedido.html', {
        'ventas': ventas,
        'total': total,
        'usuario': request.user,
        'rut': rut,
        'telefono': telefono,
        'direccion': direccion,
        'envio': venta.envio
    })

    send_mail(
        admin_subject,
        admin_message,
        settings.DEFAULT_FROM_EMAIL,
        [admin_email],
        html_message=admin_message
    )

    # Renderizar la página de confirmación después del pago
    return render(request, 'carrito/compra_confirmacion.html', {
        'ventas': ventas,
        'total': total,
        'pago_id': pago.id
    })



def ver_carrito(request):
    resumen_carrito = obtener_resumen_carrito(request)
    
    # También necesitamos verificar si hay información de envío en la sesión
    envio = request.session.get('envio', 'retiro')  # Valor predeterminado: retiro en tienda
    
    # Si hay envío, calculamos el total con envío
    total = resumen_carrito['total']
    if envio == 'envio':
        total += 5000  # Costo de envío
    
    context = {
        'carrito': resumen_carrito,
        'envio': envio,
        'total': total
    }
    
    return render(request, 'carrito/carrito.html', context)  # Corregido para llamar a render con los argumentos


def obtener_resumen_carrito(request):
    """
    Función para procesar el carrito y obtener un resumen detallado
    incluyendo la cantidad de cada producto por talla y color.
    """
    carrito = request.session.get('carrito', {})
    resumen_carrito = []
    
    # Calcular el total general
    total_carrito = 0
    
    for slug, producto_info in carrito.items():
        # Información general del producto
        producto_resumen = {
            'nombre': producto_info.get('nombre', 'Producto sin nombre'),
            'slug': slug,
            'cantidad_total': producto_info.get('cantidad', 0),
            'precio_unitario': producto_info.get('precio', 0),
            'subtotal': producto_info.get('cantidad', 0) * producto_info.get('precio', 0),
            'tallas': []
        }
        
        # Agregar el subtotal al total general
        total_carrito += producto_resumen['subtotal']
        
        # Verificar si el producto tiene tallas
        if 'tallas' in producto_info:
            # Procesar cada talla
            for talla_id, talla_info in producto_info['tallas'].items():
                talla_resumen = {
                    'id': talla_id,
                    'talla': talla_info.get('talla', 'Sin talla'),
                    'cantidad': talla_info.get('cantidad', 0),
                    'colores': []
                }
                
                # Verificar si la talla tiene colores
                if 'colores' in talla_info:
                    # Procesar cada color de esta talla
                    for color_id, color_info in talla_info['colores'].items():
                        color_resumen = {
                            'id': color_id,
                            'nombre': color_info.get('color', 'Sin color'),
                            'cantidad': color_info.get('cantidad', 0),
                            'precio': color_info.get('precio', 0),
                            'subtotal': color_info.get('cantidad', 0) * color_info.get('precio', 0)
                        }
                        
                        talla_resumen['colores'].append(color_resumen)
                
                producto_resumen['tallas'].append(talla_resumen)
        
        resumen_carrito.append(producto_resumen)
    
    return {
        'productos': resumen_carrito,
        'total': total_carrito,
        'cantidad_productos': sum(prod['cantidad_total'] for prod in resumen_carrito)
    }

def actualizar_color_carrito(request, slug, talla_id, color_id):
    if request.method == 'POST':
        carrito = request.session.get('carrito', {})
        cantidad = int(request.POST.get('cantidad', 1))
        
        if slug in carrito and talla_id in carrito[slug]['tallas'] and color_id in carrito[slug]['tallas'][talla_id]['colores']:
            # Obtener la cantidad anterior
            cantidad_anterior = carrito[slug]['tallas'][talla_id]['colores'][color_id]['cantidad']
            
            # Calcular la diferencia
            diferencia = cantidad - cantidad_anterior
            
            # Actualizar la cantidad del color
            carrito[slug]['tallas'][talla_id]['colores'][color_id]['cantidad'] = cantidad
            
            # Actualizar la cantidad total de la talla
            carrito[slug]['tallas'][talla_id]['cantidad'] += diferencia
            
            # Actualizar la cantidad total del producto
            carrito[slug]['cantidad'] += diferencia
            
            # Guardar los cambios
            request.session['carrito'] = carrito
            messages.success(request, 'Carrito actualizado correctamente.')
        else:
            messages.error(request, 'No se pudo actualizar el carrito.')
            
    return redirect('ver_carrito')

def eliminar_color_carrito(request, slug, talla_id, color_id):
    carrito = request.session.get('carrito', {})
    
    if slug in carrito and talla_id in carrito[slug]['tallas'] and color_id in carrito[slug]['tallas'][talla_id]['colores']:
        # Obtener la cantidad que vamos a eliminar
        cantidad_a_eliminar = carrito[slug]['tallas'][talla_id]['colores'][color_id]['cantidad']
        
        # Restar la cantidad del color del total de la talla
        carrito[slug]['tallas'][talla_id]['cantidad'] -= cantidad_a_eliminar
        
        # Restar la cantidad del color del total del producto
        carrito[slug]['cantidad'] -= cantidad_a_eliminar
        
        # Eliminar el color
        del carrito[slug]['tallas'][talla_id]['colores'][color_id]
        
        # Si no quedan colores en la talla, eliminar la talla
        if not carrito[slug]['tallas'][talla_id]['colores']:
            del carrito[slug]['tallas'][talla_id]
        
        # Si no quedan tallas en el producto, eliminar el producto
        if not carrito[slug]['tallas']:
            del carrito[slug]
        
        # Guardar el carrito actualizado en la sesión
        request.session['carrito'] = carrito
        
        messages.success(request, 'Producto eliminado del carrito.')
    else:
        messages.error(request, 'El producto no se encuentra en el carrito.')
    
    return redirect('ver_carrito')

def eliminar_del_carrito(request, slug):
    carrito = request.session.get('carrito', {})
    
    if slug in carrito:
        del carrito[slug]
        request.session['carrito'] = carrito
        messages.success(request, 'Producto eliminado completamente del carrito.')
    else:
        messages.error(request, 'El producto no se encuentra en el carrito.')
    
    return redirect('ver_carrito')

def vaciar_carrito(request):
    request.session['carrito'] = {}
    messages.success(request, 'Carrito vaciado con éxito.')
    return redirect('ver_carrito')


def agregar_al_carrito(request, slug):
    # Obtener el producto usando el slug
    producto = get_object_or_404(Producto, slug=slug)
    
    # Calcular el precio correcto (con o sin descuento)
    precio = float(producto.precio_con_descuento) if producto.tiene_descuento else float(producto.precio)
    
    # Obtener los valores de talla y color desde la solicitud POST
    talla_id = request.POST.get('talla')
    color_id = request.POST.get('color')
    
    # Obtener el carrito de la sesión o inicializarlo si no existe
    carrito = request.session.get('carrito', {})
    
    # Obtener la talla seleccionada
    try:
        talla = producto.tallas.get(id=talla_id)
    except ProductoTalla.DoesNotExist:
        messages.error(request, 'La talla seleccionada no existe para este producto.')
        return redirect('producto_detalle', slug=slug)
    
    # Obtener el color seleccionado
    try:
        color = ProductoTallaColor.objects.get(id=color_id)
    except ProductoTallaColor.DoesNotExist:
        messages.error(request, 'El color seleccionado no existe para esta talla.')
        return redirect('producto_detalle', slug=slug)
    
    # Si el producto ya está en el carrito
    if slug in carrito:
        # Incrementar la cantidad total del producto
        carrito[slug]['cantidad'] += 1
        
        if talla_id in carrito[slug]['tallas']:
            # Incrementar la cantidad total de esta talla
            carrito[slug]['tallas'][talla_id]['cantidad'] += 1
            
            if color_id in carrito[slug]['tallas'][talla_id]['colores']:
                # Si el producto con esta talla y color ya está en el carrito, incrementamos la cantidad
                carrito[slug]['tallas'][talla_id]['colores'][color_id]['cantidad'] += 1
            else:
                # Si el color no está, lo agregamos como una nueva entrada
                carrito[slug]['tallas'][talla_id]['colores'][color_id] = {
                    'color': color.color.nombre,
                    'cantidad': 1,
                    'precio': precio,
                }
        else:
            # Si la talla no está, la agregamos junto con el color
            carrito[slug]['tallas'][talla_id] = {
                'talla': talla.talla,
                'precio': precio,
                'cantidad': 1,
                'colores': {
                    color_id: {
                        'color': color.color.nombre,
                        'cantidad': 1,
                        'precio': precio,
                    }
                }
            }
    else:
        # Si el producto no está en el carrito, lo agregamos
        carrito[slug] = {
            'nombre': producto.nombre,
            'precio': precio,
            'cantidad': 1,
            'slug': producto.slug,
            'tallas': {
                talla_id: {
                    'talla': talla.talla,
                    'precio': precio,
                    'cantidad': 1,
                    'colores': {
                        color_id: {
                            'color': color.color.nombre,
                            'cantidad': 1,
                            'precio': precio,
                        }
                    }
                }
            }
        }
    
    # Guardar el carrito en la sesión
    request.session['carrito'] = carrito
    
    # Mensaje de éxito
    messages.success(request, f'{producto.nombre} con talla {talla.talla} y color {color.color.nombre} se ha agregado al carrito con éxito.')
    
    # Redirigir a la vista del producto
    return redirect('producto_detalle', slug=slug)

def actualizar_producto_simple(request, slug):
    if request.method == 'POST':
        carrito = request.session.get('carrito', {})
        cantidad = int(request.POST.get('cantidad', 1))
        
        if slug in carrito:
            carrito[slug]['cantidad'] = cantidad
            request.session['carrito'] = carrito
            messages.success(request, 'Carrito actualizado correctamente.')
        else:
            messages.error(request, 'No se pudo actualizar el carrito.')
            
    return redirect('ver_carrito')


class ProductoDetalleView(DetailView):
    model = Producto
    template_name = 'productos/detalle.html'
    context_object_name = 'producto'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        producto = context['producto']
        
        # Productos relacionados
        context['productos_relacionados'] = self._get_related_products(producto)
        
        # Información del producto actual
        self._add_product_info(producto)
        
        # Opiniones y formulario
        self._add_reviews_context(context, producto)
        
        # Colores por talla
        context['colores_por_talla'] = self._get_colors_by_size(producto)
        
        return context
    
    def _get_related_products(self, producto):
        related = Producto.objects.filter(
            categoria=producto.categoria, 
            activo=True
        ).exclude(id=producto.id)[:10]
        
        for prod in related:
            prod.imagenes_list = prod.imagenes.all()
        return related
    
    def _add_product_info(self, producto):
        producto.imagenes_list = producto.imagenes.all()
        producto.tallas_list = producto.tallas.all()
    
    def _add_reviews_context(self, context, producto):
        context['rango_estrellas'] = range(1, 6)
        producto.opiniones_list = producto.opiniones.all().order_by('-created_at')[:3]
        
        if self.request.user.is_authenticated:
            if producto.opiniones.filter(user=self.request.user).exists():
                context['usuario_tiene_opinion'] = True
            else:
                context['opinion_form'] = OpinionClienteForm()
    
    def _get_colors_by_size(self, producto):
        return {
            talla.id: [
                pcolor.color for pcolor in ProductoTallaColor.objects.filter(producto_talla=talla)
            ] for talla in producto.tallas.all()
        }
    
    
# 2. Actu@csrf_exempt

@csrf_exempt  # Mantén esto para pruebas, pero considera una solución más segura después
@require_POST  # Asegura que solo se acepten solicitudes POST
def get_colores_por_talla(request):
    """Obtiene los colores disponibles para una talla específica."""
    talla_id = request.POST.get('talla')
    
    if not talla_id:
        return JsonResponse({'colores': []})
    
    try:
        # Intenta convertir a entero para validar
        talla_id = int(talla_id)
        
        # Consulta los colores asociados a la talla
        talla_colores = ProductoTallaColor.objects.filter(producto_talla_id=talla_id)
        
        colores = [
            {'id': pcolor.id, 'nombre': pcolor.color.nombre} 
            for pcolor in talla_colores
        ]
        
        return JsonResponse({'colores': colores})
    
    except (ValueError, TypeError):
        # Si el ID no es un número válido
        return JsonResponse({'error': 'ID de talla no válido'}, status=400)
    
    except Exception as e:
        # Log el error pero no expongas detalles técnicos al usuario
        print(f"Error al obtener colores: {str(e)}")
        return JsonResponse({'error': 'Error al procesar la solicitud'}, status=500)

def terminos(request):
    return render(request, 'politicas/politicas.html')

def terminos_condiciones(request):
    return render(request, 'politicas/terminos_condiciones.html')

def politica_privacidad(request):
    return render(request, 'politicas/terminos_privacidad.html')

def terminos_rembolso(request):
    return render(request, 'politicas/terminos_rembolso.html')


def agregar_a_favoritos(request, slug):
    # Obtener el producto usando el slug
    producto = get_object_or_404(Producto, slug=slug)
    
    # Obtener las imágenes del producto (tomamos la primera imagen disponible)
    imagen_producto = producto.imagenes.first()  # Si no hay imagen, será None
    
    # Obtener los favoritos de la sesión o inicializarlo si no existe
    favoritos = request.session.get('favoritos', {})

    # Verificar si el producto ya está en favoritos
    if str(slug) not in favoritos:
        favoritos[str(slug)] = {
            'nombre': producto.nombre,
            'precio': str(producto.precio),
            'slug': producto.slug,
            'imagen': imagen_producto.imagen.url if imagen_producto else None,  # Usar la URL de la imagen
        }
        # Guardar los favoritos en la sesión
        request.session['favoritos'] = favoritos
        messages.success(request, f'{producto.nombre} ha sido agregado a tus favoritos.')
    else:
        messages.info(request, f'{producto.nombre} ya está en tus favoritos.')

    return redirect('producto_detalle', slug=slug)  # Redirige a la página del producto


def ver_favoritos(request):
    favoritos = request.session.get('favoritos', {})
    return render(request, 'favoritos/favoritos.html', {'favoritos': favoritos})

def eliminar_de_favoritos(request, slug):
    # Obtener los favoritos de la sesión
    favoritos = request.session.get('favoritos', {})

    # Eliminar el producto de los favoritos
    if str(slug) in favoritos:
        del favoritos[str(slug)]
        request.session['favoritos'] = favoritos
        messages.success(request, f'Producto {slug} ha sido eliminado de tus favoritos.')
    else:
        messages.error(request, 'Producto no encontrado en tus favoritos.')

    return redirect('ver_favoritos')  # Redirige a la vista de favoritos

def actualizar_favoritos(request, slug):
    # Obtener los favoritos de la sesión
    favoritos = request.session.get('favoritos', {})

    # Si el producto está en los favoritos
    if str(slug) in favoritos:
        # Aquí puedes actualizar detalles adicionales si lo necesitas
        # Por ejemplo, puedes agregar un campo de "comentarios" o algo similar
        favoritos[str(slug)]['comentarios'] = request.POST.get('comentarios', '')
        request.session['favoritos'] = favoritos
        messages.success(request, 'Favoritos actualizados correctamente.')
    else:
        messages.error(request, 'Producto no encontrado en tus favoritos.')

    return redirect('ver_favoritos')  # Redirige a la vista de favoritos


class IndexView(ListView):
    model = Producto
    template_name = 'index.html'  # Plantilla para mostrar productos
    context_object_name = 'productos_destacados'  # Nombre con el que accederemos a los productos en la plantilla
    paginate_by = 3  # Número de productos por página

    def get_queryset(self):
        # Filtramos los productos con una valoración promedio alta y los ordenamos por la valoración promedio
        productos = Producto.objects.annotate(promedio=Avg('opiniones__valoracion')) \
                                    .filter(promedio__gte=4,activo=True)  # Filtrar solo productos con promedio >= 4 estrellas

        # Ordenar los productos por la valoración promedio (puedes cambiar esto si quieres otro criterio)
        productos = productos.order_by('-promedio')  # Ordena de mayor a menor valoración promedio

        return productos

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rango_estrellas = range(1, 6)  # Rango de 1 a 5 estrellas
        context['rango_estrellas'] = rango_estrellas

        # Añadir listas de imágenes y tallas a cada producto (optimizamos con prefetch_related en la consulta)
        for producto in context['productos_destacados']:
            producto.imagenes_list = producto.imagenes.all()  # Accede a las imágenes del producto
            producto.tallas_list = producto.tallas.all()  # Accede a las tallas del producto
        
        return context
    
    
# Función que verifica si el usuario es un superusuario
def es_superusuario(user):
    return user.is_superuser

@login_required
def dejar_opinion(request, slug):
    producto = get_object_or_404(Producto, slug=slug)  # Obtener el producto por su slug

    if request.method == 'POST':
        form = OpinionClienteForm(request.POST)
        if form.is_valid():
            # Asignar el producto y el usuario a la opinión
            opinion = form.save(commit=False)
            opinion.producto = producto  # Asociar la opinión con el producto
            opinion.user = request.user  # Asignar el usuario autenticado
            opinion.save()  # Guardar la opinión

            # Mensaje de éxito
            messages.success(request, '¡Gracias por tu opinión!')
            return redirect('producto_detalle', slug=producto.slug)  # Redirigir a la página del producto
    else:
        form = OpinionClienteForm()

    return render(request, 'productos/dejar_opinion.html', {
        'form': form,
        'producto': producto
    })
    
@login_required
def actualizar_envio(request):
    if request.method == 'POST':
        envio = request.POST.get('envio')
        # Guarda la opción de envío en la sesión
        request.session['envio'] = envio
    # Redirige de vuelta al carrito o la página que corresponda
    return redirect('ver_carrito')

def ver_carrito1(request):
    # Recuperar el carrito de la sesión
    carrito = request.session.get('carrito', {})
    
    # Inicializar el total
    total = 0
    for producto_slug, producto_data in carrito.items():
        # Asegúrate de que 'tallas' está en el diccionario
        if 'tallas' in producto_data:
            for talla_id, talla_data in producto_data['tallas'].items():
                total += float(talla_data['precio']) * talla_data['cantidad']
    
    # Obtener la opción de envío de la sesión (por defecto es "retiro")
    envio = request.session.get('envio', 'retiro')
    
    # Si el usuario seleccionó envío, agregar un costo fijo
    if envio == 'envio':
        total += 5000  # Costo de envío
    
    # Pasar los datos al contexto de la plantilla
    return render(request, 'carrito/carrito.html', {
        'carrito': carrito,
        'total': total,
        'envio': envio,
    })
   
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
def failure(request):
    return render(request, 'carrito/compra_fallo.html')
@login_required
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


@user_passes_test(es_superusuario)
def editar_producto(request, slug):
    producto = get_object_or_404(Producto, slug=slug)  # Obtener el producto a editar por su slug

    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)  # Inicializamos el formulario con los datos del producto
        if form.is_valid():
            form.save()  # Guardamos los cambios en el producto
            messages.success(request, f'Producto {producto.nombre} actualizado exitosamente.')
            return redirect('producto_detalle', slug=producto.slug)  # Redirigimos a los detalles del producto
    else:
        form = ProductoForm(instance=producto)  # En GET, prellenamos el formulario con el producto existente

    return render(request, 'productos/editar_producto.html', {'form': form, 'producto': producto})

@user_passes_test(es_superusuario)
def modificar_imagenes(request, slug):
    producto = get_object_or_404(Producto, slug=slug)
    imagenes = producto.imagenes.all()  # Obtener las imágenes existentes
    
    if imagenes.count() >= 5:  # Corregir a `count()`
        # Limitar la cantidad de fotos a 5
        messages.warning(request, 'Ya no puedes agregar más de 5 fotos.')
        return render(request, 'productos/modificar_imagenes.html', {'producto': producto, 'imagenes': imagenes})
    
    # Asegurarse de que el formulario siempre esté presente, incluso para una solicitud GET
    form = ProductoImagenForm()

    if request.method == 'POST':
        form = ProductoImagenForm(request.POST, request.FILES)
        if form.is_valid():
            imagen = form.save(commit=False)
            imagen.producto = producto  # Asignar la imagen al producto
            imagen.save()
            messages.success(request, 'Imagen modificada exitosamente.')
            return redirect('modificar_imagenes', slug=producto.slug)
    
    return render(request, 'productos/modificar_imagenes.html', {'form': form, 'producto': producto, 'imagenes': imagenes})

@user_passes_test(es_superusuario)
def modificar_tallas(request, slug):
    producto = get_object_or_404(Producto, slug=slug)
    
     # Usamos prefetch_related con 'colores' para obtener los colores asociados a las tallas
    tallas = ProductoTalla.objects.prefetch_related('colores').filter(producto=producto)  # Obtener todas las tallas asociadas al productos

    if request.method == 'POST':
        # Para modificar o agregar talla
        form = ProductoTallaForm(request.POST, producto=producto)
        if form.is_valid():
            talla = form.save(commit=False)
            talla.producto = producto  # Asociar la talla al producto
            talla.save()
            messages.success(request, f'Talla {form.cleaned_data["talla"]} agregada correctamente.')
            return redirect('modificar_tallas', slug=producto.slug)

        # Para agregar color a una talla
        if 'agregar_color' in request.POST:
            talla_id = request.POST.get('talla_id')  # Obtener el ID de la talla seleccionada
            talla = get_object_or_404(ProductoTalla, id=talla_id)

            color_form = ProductoTallaColorForm(request.POST, producto_talla=talla)
            if color_form.is_valid():
                color_form.save()  # Guardar el nuevo color asociado a la talla
                messages.success(request, f'Color agregado correctamente a la talla {talla.talla}.')
                return redirect('modificar_tallas', slug=producto.slug)
            else:
                messages.error(request, f'Error al agregar el color: {color_form.errors}')

        # Lógica para eliminar color
        if 'eliminar_color' in request.POST:
            talla_color_id = request.POST.get('talla_color_id')  # Obtener el ID del color a eliminar
            talla_color = get_object_or_404(ProductoTallaColor, id=talla_color_id)
            talla_color.delete()
            messages.success(request, f'Color eliminado correctamente de la talla {talla_color.producto_talla.talla}.')
            return redirect('modificar_tallas', slug=producto.slug)

        # Lógica para eliminar talla
        if 'eliminar_talla' in request.POST:
            talla_id = request.POST.get('talla_id')  # Obtener el ID de la talla seleccionada para eliminar
            talla = get_object_or_404(ProductoTalla, id=talla_id)
            talla.delete()
            messages.success(request, f'Talla {talla.talla} eliminada correctamente.')
            return redirect('modificar_tallas', slug=producto.slug)

    else:
        form = ProductoTallaForm(producto=producto)

    # Crear un formulario vacío para agregar color
    color_form = ProductoTallaColorForm()

    return render(request, 'productos/modificar_tallas.html', {
        'form': form,
        'producto': producto,
        'tallas': tallas,
        'color_form': color_form,
    })


@user_passes_test(es_superusuario)
def eliminar_imagen(request, imagen_id):
    # Obtener la imagen por su ID
    imagen = get_object_or_404(ProductoImagen, id=imagen_id)

    # Guardar el producto relacionado
    producto_slug = imagen.producto.slug

    # Eliminar la imagen
    imagen.delete()

    # Mensaje de éxito
    messages.success(request, 'Imagen eliminada exitosamente.')

    # Redirigir al usuario a la página de modificación de imágenes del producto
    return redirect('modificar_imagenes', slug=producto_slug)

@user_passes_test(es_superusuario)
def eliminar_talla(request, talla_id):
    talla = get_object_or_404(ProductoTalla, id=talla_id)
    producto_slug = talla.producto.slug
    talla.delete()
    messages.success(request, f'Talla {talla.talla} eliminada correctamente.')
    return redirect('modificar_tallas', slug=producto_slug)

@user_passes_test(es_superusuario)
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

@user_passes_test(es_superusuario)
def subir_imagenes(request, slug):
    producto = get_object_or_404(Producto, slug=slug)  # Recuperamos el producto por su slug
    
    if request.method == 'POST':
        # Obtener la lista de imágenes actuales para el producto
        imagenes_actuales = producto.imagenes.all()

        # Si ya se han subido 5 imágenes, no permitir más
        if imagenes_actuales.count() >= 5:
            messages.error(request, 'Ya se han subido el máximo de imágenes (5).')
            return redirect('agregar_tallas', slug=producto.slug)
        
        form = ProductoImagenForm(request.POST, request.FILES)
        if form.is_valid():
            imagen = form.save(commit=False)  # No guardar aún
            imagen.producto = producto  # Asignamos el producto a la imagen
            imagen.save()  # Guardamos la imagen
            messages.success(request, 'Imagen subida exitosamente.')

            # Si ya se subieron las 5 imágenes, redirigir a la siguiente fase
            if producto.imagenes.count() >= 5:
                messages.success(request, 'Se han subido todas las imágenes. Ahora puedes agregar las tallas.')
                return redirect('agregar_tallas', slug=producto.slug)
            else:
                # Mostrar el número de imágenes restantes
                restantes = 3 - producto.imagenes.count()
                messages.info(request, f'Aún te quedan {restantes} imágenes por subir.')
                return redirect('subir_imagenes', slug=producto.slug)
    else:
        form = ProductoImagenForm(initial={'producto': producto})  # Inicializamos el formulario con el producto

    return render(request, 'productos/subir_imagenes.html', {'form': form, 'producto': producto})


@user_passes_test(es_superusuario)
def agregar_tallas_y_colores(request, slug):
    producto = get_object_or_404(Producto, slug=slug)  # Recuperamos el producto por su slug

    # Inicializamos los formularios antes de usar
    talla_form = ProductoTallaForm(request.POST or None, producto=producto)  # Formulario para agregar talla
    color_form = ProductoTallaColorForm(request.POST or None)  # Formulario vacío para agregar color

    # Usamos prefetch_related para obtener las tallas con sus colores asociados
    tallas = ProductoTalla.objects.prefetch_related('colores').filter(producto=producto)  # Obtener todas las tallas asociadas al producto

    if request.method == 'POST':
        # Si el formulario de talla se ha enviado
        if 'agregar_talla' in request.POST and talla_form.is_valid():
            producto_talla = talla_form.save(commit=False)
            producto_talla.producto = producto  # Asignamos el producto manualmente
            producto_talla.save()  # Guardamos la talla
            messages.success(request, f'Talla {talla_form.cleaned_data["talla"]} agregada correctamente.')
            return redirect('agregar_tallas', slug=producto.slug)  # Redirige para seguir agregando

        # Si el formulario de color se ha enviado
         # Si el formulario de color se ha enviado
        elif 'agregar_color' in request.POST and color_form.is_valid():
            talla_id = request.POST.get('talla_id')
            talla = get_object_or_404(ProductoTalla, id=talla_id)

            # Para depurar: Imprimir errores del formulario
            print("Errores del formulario de color:", color_form.errors)

            # Crear formulario de color con los datos
            color_form = ProductoTallaColorForm(request.POST, producto_talla=talla)

            if color_form.is_valid():
                color_form.save()  # Guardar el color asociado a la talla
                messages.success(request, f'Color agregado correctamente a la talla {talla.talla}.')
                return redirect('agregar_tallas', slug=producto.slug)
            else:
                # Si el formulario no es válido, mostrar los errores
                print("Errores al intentar guardar el color:", color_form.errors)
                messages.error(request, 'Hubo un error al agregar el color. Por favor, verifica los datos.')
        # Eliminar una talla seleccionada
        elif 'eliminar_talla' in request.POST:
            talla_id = request.POST.get('talla_id')  # ID de la talla a eliminar
            talla = get_object_or_404(ProductoTalla, id=talla_id)

            # Eliminar la talla (esto también eliminará los colores asociados debido a la relación de muchos a muchos)
            talla.delete()
            messages.success(request, f'Talla {talla.talla} eliminada correctamente.')

            return redirect('agregar_tallas', slug=producto.slug)

        # Eliminar un color de una talla seleccionada
        elif 'eliminar_color' in request.POST:
            talla_id = request.POST.get('talla_id')  # ID de la talla de la que se eliminará el color
            color_id = request.POST.get('color_id')  # ID del color a eliminar
            talla = get_object_or_404(ProductoTalla, id=talla_id)
            color = get_object_or_404(ProductoTallaColor, id=color_id)

            # Eliminar la relación entre la talla y el color
            talla.colores.remove(color)  # Quitar la relación de la talla con el color
            messages.success(request, f'Color {color.color.nombre} eliminado correctamente de la talla {talla.talla}.')

            return redirect('agregar_tallas', slug=producto.slug)        

    # En el caso de que sea un GET, se inicializan los formularios vacíos
    return render(request, 'productos/agregar_tallas_y_colores.html', {
        'producto': producto,
        'talla_form': talla_form,
        'color_form': color_form,
        'tallas': tallas,  # Pasar 'tallas' en lugar de 'tallas_existentes'
    })


@user_passes_test(es_superusuario)
def agregar_tallas(request, slug):
    producto = get_object_or_404(Producto, slug=slug)  # Recuperamos el producto por su slug

    if request.method == 'POST':
        form = ProductoTallaForm(request.POST, producto=producto)  # Pasamos el producto al formulario como un argumento
        if form.is_valid():
            producto_talla = form.save(commit=False)
            producto_talla.producto = producto  # Asignamos el producto manualmente
            producto_talla.save()  # Guardamos el objeto ProductoTalla
            messages.success(request, f'Talla {form.cleaned_data["talla"]} agregada correctamente.')
            return redirect('agregar_tallas', slug=producto.slug)  # Redirige a la misma página para agregar más tallas
    else:
        form = ProductoTallaForm(producto=producto)  # Inicializamos el formulario pasando el producto

    tallas_existentes = producto.tallas.all()  # Listar las tallas existentes de este producto

    return render(request, 'productos/agregar_tallas.html', {'form': form, 'producto': producto, 'tallas_existentes': tallas_existentes})


@user_passes_test(es_superusuario)
def agregar_colores_talla(request, talla_id):
    talla = get_object_or_404(ProductoTalla, id=talla_id)
    producto = talla.producto

    if request.method == 'POST':
        # Pasamos 'producto_talla' al formulario para que lo use al guardarlo
        color_form = ProductoTallaColorForm(request.POST, producto_talla=talla)
        
        if color_form.is_valid():
            color_form.save()  # Ahora debería funcionar correctamente
            messages.success(request, f'Color agregado correctamente a la talla {talla.talla}.')
            return redirect('agregar_tallas', slug=producto.slug)  # Redirigir a la página de tallas para el producto
        else:
            messages.error(request, f'Hubo un error al agregar el color. Errores: {color_form.errors}')
    else:
        color_form = ProductoTallaColorForm(producto_talla=talla)

    return render(request, 'productos/agregar_colores.html', {
        'color_form': color_form,
        'talla': talla,
        'producto': producto,
    })
    

@user_passes_test(es_superusuario)
def lista_productos(request):
    form = ProductoFilterForm(request.GET)


    # Obtener todos los productos
    productos = Producto.objects.all()

    # Aplicar filtros según los datos del formulario
    slug_buscar = request.GET.get('slug', '')
    if slug_buscar:
        productos = productos.filter(slug__icontains=slug_buscar)

    # Ordenar productos por nombre (es importante hacerlo antes de la paginación)
    productos = productos.order_by('nombre')

    # Optimización: Usamos prefetch_related para obtener imágenes y tallas de una sola consulta
    productos = productos.prefetch_related('imagenes', 'tallas')

    # Paginación
    paginator = Paginator(productos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Pasar productos y formulario al contexto
    return render(request, 'productos/producto_list.html', {
        'page_obj': page_obj,  # Usamos 'page_obj' para el template
        'form': form,
    })

def about(request):
    return render(request, 'about.html')


class ProductoListView(ListView):
    model = Producto
    template_name = 'shop.html'
    context_object_name = 'productos'
    paginate_by = 30  # Número de productos por página

    def get_queryset(self):
        queryset = Producto.objects.filter(activo=True)  # Filtramos solo productos activos
        queryset = queryset.order_by('nombre')  # Asegúrate de ordenar


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
        order_by = self.request.GET.get('order_by', 'nombre')  # Establece un valor predeterminado
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
        
        # Aquí agregamos el rango de 1 a 5 para las estrellas
        context['rango_estrellas'] = range(1, 6)
        return context

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
            
            # Crear el correo en formato texto plano y HTML para el administrador
            subject = f'Nuevo mensaje de contacto de {nombre}'
            from_email = correo
            to_email = ['info@tbkdesire.cl']  # Reemplaza con el correo del administrador

            # Texto plano para el correo
            text_content = f'Nuevo mensaje de contacto de {nombre}\n\nCorreo: {correo}\n\nMensaje:\n{mensaje}'
            
            # HTML para el correo
            html_content = f"""
                <html>
                    <body>
                        <h2>Nuevo mensaje de contacto de {nombre}</h2>
                        <p><strong>Correo:</strong> {correo}</p>
                        <p><strong>Mensaje:</strong></p>
                        <p>{mensaje}</p>
                    </body>
                </html>
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

            # Enviar el correo al administrador
            email.send(fail_silently=False)

            # Si también deseas enviar un correo al usuario de confirmación
            user_subject = f'Gracias por tu mensaje, {nombre}'
            user_message = f"""
                <html>
                    <body>
                        <h2>Gracias por ponerte en contacto con nosotros, {nombre}!</h2>
                        <p>Hemos recibido tu mensaje y nos pondremos en contacto contigo pronto.</p>
                        <p><strong>Tu mensaje:</strong></p>
                        <p>{mensaje}</p>
                    </body>
                </html>
            """
            user_email = EmailMultiAlternatives(
                user_subject,
                user_message, 
                'info@tbkdesire.cl',  # Dirección del remitente (puedes cambiarla)
                [correo]
            )

            # Adjuntar el contenido HTML al correo del usuario
            user_email.attach_alternative(user_message, "text/html")
            user_email.send(fail_silently=False)

            # Mensaje de éxito para el usuario
            messages.success(request, 'Tu mensaje ha sido enviado al administrador. ¡Gracias!')

            # Redirige a la página que desees
            return redirect('shop')  # O usa otro nombre de URL adecuado, como 'success', si es necesario.
    else:
        formm = ContactoForm()

    # Renderiza la página con el formulario
    return render(request, 'contacto.html', {'formm': formm})


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
            # Verificamos que el usuario haya aceptado los términos
            if form.cleaned_data['acepta_terminos']:
                user = form.save()
                messages.success(request, '¡Cuenta registrada con éxito!')
                return redirect('login')  # Redirige a la página de inicio de sesión
            else:
                messages.error(request, 'Debes aceptar los términos y condiciones.')
        else:
            messages.error(request, 'Hubo un error en el registro. Por favor, corrige los errores.')
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})



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



# Vista para listar los colores
@user_passes_test(es_superusuario)
def color_list(request):
    colores = Color.objects.all()
    return render(request, 'color/color_list.html', {'colores': colores})

# Vista para crear un nuevo color
@user_passes_test(es_superusuario)
def color_create(request):
    if request.method == 'POST':
        form = ColorForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('color_list')
    else:
        form = ColorForm()
    return render(request, 'color/color_form.html', {'form': form})

# Vista para editar un color existente
@user_passes_test(es_superusuario)
def color_edit(request, pk):
    color = get_object_or_404(Color, pk=pk)
    if request.method == 'POST':
        form = ColorForm(request.POST, request.FILES, instance=color)
        if form.is_valid():
            form.save()
            return redirect('color_list')
    else:
        form = ColorForm(instance=color)
    return render(request, 'color/color_form.html', {'form': form})

# Vista para eliminar un color
@user_passes_test(es_superusuario)
def color_delete(request, pk):
    color = get_object_or_404(Color, pk=pk)
    if request.method == 'POST':
        color.delete()
        return redirect('color_list')
    return render(request, 'color/color_confirm_delete.html', {'color': color})


# Vista para listar las categorías
@user_passes_test(es_superusuario)
def categoria_list(request):
    categorias = Categoria.objects.all()
    return render(request, 'categoria/categoria_list.html', {'categorias': categorias})

# Vista para crear una nueva categoría
@user_passes_test(es_superusuario)
def categoria_create(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('categoria_list')
    else:
        form = CategoriaForm()
    return render(request, 'categoria/categoria_form.html', {'form': form})

# Vista para editar una categoría existente
@user_passes_test(es_superusuario)
def categoria_edit(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            return redirect('categoria_list')
    else:
        form = CategoriaForm(instance=categoria)
    return render(request, 'categoria/categoria_form.html', {'form': form})

# Vista para eliminar una categoría
@user_passes_test(es_superusuario)
def categoria_delete(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        categoria.delete()
        return redirect('categoria_list')
    return render(request, 'categoria/categoria_confirm_delete.html', {'categoria': categoria})

@user_passes_test(es_superusuario)
def cambiar_estado_pago(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)

    # Verificar si el usuario tiene permiso de administrador
    if not request.user.is_staff:
        messages.error(request, "No tienes permisos para realizar esta acción.")
        return redirect('mis_compras')

    if request.method == 'POST':
        # Cambiar el estado del pago
        estado_pago = request.POST.get('estado')
        if venta.pago:
            venta.pago.estado = estado_pago
            venta.pago.save()
            messages.success(request, f"El estado de pago ha sido actualizado a {estado_pago}.")
        else:
            messages.error(request, "No se encontró el pago para esta venta.")
        return redirect('mis_compras')  # Redirige a la vista de ventas

    return redirect('mis_compras')
