from django.urls import path

from django.conf import settings
from django.conf.urls.static import static
from .views import ProductoListView,index,producto_detalle,about,contacto,success,lista_productos

from .views import crear_producto, subir_imagenes,agregar_tallas,agregar_al_carrito,ver_carrito,eliminar_del_carrito,actualizar_carrito



urlpatterns = [
    
    
    path('crear/',crear_producto , name='crear_producto'),
    path('subir_imagenes/<slug:slug>/',subir_imagenes, name='subir_imagenes'),
    path('agregar_tallas/<slug:slug>/',agregar_tallas, name='agregar_tallas'),
    
    path('', index, name='index'),  # URL para ver la lista de productos
    path('about', about, name='about'),  # URL para ver la lista de productos
    path('contacto', contacto, name='contacto'),  # URL para ver la lista de productos
    path('success', success, name='success'),  # URL para ver la lista de productos
    
    
    path('listar/', lista_productos, name='listar'),  # URL para ver la lista de productos
     
     
    path('shop/', ProductoListView.as_view(), name='shop'),  # URL para ver la lista de productos
    path('producto/<slug:slug>/', producto_detalle.as_view(), name='producto_detalle'),
    
    path('agregar_al_carrito/<slug:slug>/', agregar_al_carrito, name='agregar_al_carrito'),
    path('ver_carrito/', ver_carrito, name='ver_carrito'),
    path('eliminar_del_carrito/<slug:slug>/', eliminar_del_carrito, name='eliminar_del_carrito'),
    path('actualizar_carrito/<slug:slug>/', actualizar_carrito, name='actualizar_carrito'),
]
