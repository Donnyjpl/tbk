from django.urls import path,include

from django.conf import settings
from django.conf.urls.static import static
from .views import ProductoListView,producto_detalle,about,contacto,successs,lista_productos,logout_view,custom_login,procesar_pago_success

from .views import crear_producto, subir_imagenes,agregar_tallas,agregar_al_carrito,ver_carrito,eliminar_del_carrito,actualizar_carrito

from .views import profile_view,register, ProfileUpdateView,custom_password_reset_request,CustomPasswordResetConfirmView,CustomPasswordResetDoneView,CustomPasswordResetCompleteView
from . import views
from .views import agregar_a_favoritos, ver_favoritos, eliminar_de_favoritos, actualizar_favoritos

from django.contrib.auth import views as auth_views
urlpatterns = [
    path('crear/',crear_producto , name='crear'),
    path('subir_imagenes/<slug:slug>/',subir_imagenes, name='subir_imagenes'),
    path('agregar_tallas/<slug:slug>/',agregar_tallas, name='agregar_tallas'),
    
    path('producto/editar/<slug:slug>/', views.editar_producto, name='editar_producto'),
    path('producto/modificar_imagenes/<slug:slug>/', views.modificar_imagenes, name='modificar_imagenes'),
    path('producto/modificar_tallas/<slug:slug>/', views.modificar_tallas, name='modificar_tallas'),
    path('producto/eliminar_talla/<int:talla_id>/', views.eliminar_talla, name='eliminar_talla'),
     path('producto/eliminar_imagen/<int:imagen_id>/', views.eliminar_imagen, name='eliminar_imagen'),
    
    path('', views.IndexView.as_view(), name='index'),  # URL para ver la lista de productos
    path('about/', about, name='about'),  # URL para ver la lista de productos
    path('contacto/', contacto, name='contacto'),  # URL para ver la lista de productos
    path('successs/', successs, name='successs'),  # URL para ver la lista de productos
    path('listar/', lista_productos, name='listar'),  # URL para ver la lista de productos
    
    
    path('procesar_pago/', views.procesar_pago, name='procesar_pago'),
    path('procesar_pago/exito/', views.procesar_pago_success, name='exito'),
    path('procesar_pago/failure/', views.failure, name='failure'),
    path('procesar_pago/pending/', views.pending, name='pending'),
    
    path('shop/', ProductoListView.as_view(), name='shop'),  # URL para ver la lista de productos
    path('producto/<slug:slug>/', producto_detalle.as_view(), name='producto_detalle'),
    path('dejar_opinion/', views.dejar_opinion, name='dejar_opinion'),
    
    path('agregar_al_carrito/<slug:slug>/', agregar_al_carrito, name='agregar_al_carrito'),
    path('ver_carrito/', ver_carrito, name='ver_carrito'),
    path('eliminar_del_carrito/<slug:slug>/<int:talla_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('actualizar_carrito/<slug:slug>/<int:talla_id>/', views.actualizar_carrito, name='actualizar_carrito'),
    
    
    path('favoritos/', ver_favoritos, name='ver_favoritos'),
    path('favoritos/agregar/<slug:slug>/', agregar_a_favoritos, name='agregar_a_favoritos'),
    path('favoritos/eliminar/<slug:slug>/', eliminar_de_favoritos, name='eliminar_de_favoritos'),
    path('favoritos/actualizar/<slug:slug>/', actualizar_favoritos, name='actualizar_favoritos'),

    
    
    path('editar-perfil/', ProfileUpdateView.as_view(), name='edit_profile'),
    #path('registro_exitoso/', registro_exitoso, name='registro_exitoso'),
    path('logout/', logout_view, name='logout'),
     path('login/', custom_login, name='login'),
    path('registro/', register, name='register'),
    path('profile/', profile_view, name='profile'),
    
    path('password_reset/', custom_password_reset_request, name='password_reset'),
    path('password_reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password_reset_confirm/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
]# Solo en desarrollo, servir archivos de medios

