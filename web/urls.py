from django.urls import path,include

from django.conf import settings
from django.conf.urls.static import static
from .views import ProductoListView,about,contacto,successs,lista_productos,logout_view,custom_login,procesar_pago_success,ProductoDetalleView

from .views import crear_producto, subir_imagenes,ver_carrito,eliminar_del_carrito,actualizar_carrito

from .views import profile_view,register, ProfileUpdateView,custom_password_reset_request,CustomPasswordResetConfirmView,CustomPasswordResetDoneView,CustomPasswordResetCompleteView
from . import views
from .views import agregar_a_favoritos, ver_favoritos, eliminar_de_favoritos, actualizar_favoritos,MisComprasView,get_colores_por_talla

from django.contrib.auth import views as auth_views
urlpatterns = [
    path('crear/nuevo/',crear_producto , name='crear'),
    path('subir_imagenes/<slug:slug>/',subir_imagenes, name='subir_imagenes'),
    path('agregar_tallas/<slug:slug>/', views.agregar_tallas_y_colores, name='agregar_tallas'),
    path('agregar_colores_talla/<int:talla_id>/', views.agregar_colores_talla, name='agregar_colores_talla'),
    
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
    
    # Asegúrate de que esta URL esté antes de las URL con patrones de captura
    path('producto/get_colores/', views.get_colores_por_talla, name='get_colores_por_talla'),
    path('shop/', ProductoListView.as_view(), name='shop'),  # URL para ver la lista de productos
    path('producto/<slug:slug>/', ProductoDetalleView.as_view(), name='producto_detalle'),
    
    
    # URL para agregar al carrito
    path('producto/<slug:slug>/agregar-al-carrito/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('ver_carrito/', ver_carrito, name='ver_carrito'),
    path('actualizar_envio/', views.actualizar_envio, name='actualizar_envio'),
    
    
    path('eliminar_del_carrito/<slug:slug>/<int:talla_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('actualizar_carrito/<slug:slug>/<int:talla_id>/', views.actualizar_carrito, name='actualizar_carrito'),
    
    path('producto/<slug:slug>/opinion/', views.dejar_opinion, name='producto_opinion'),
    

    path('favoritos/', ver_favoritos, name='ver_favoritos'),
    path('favoritos/agregar/<slug:slug>/', agregar_a_favoritos, name='agregar_a_favoritos'),
    path('favoritos/eliminar/<slug:slug>/', eliminar_de_favoritos, name='eliminar_de_favoritos'),
    path('favoritos/actualizar/<slug:slug>/', actualizar_favoritos, name='actualizar_favoritos'),

    path('compras/',MisComprasView.as_view() , name='mis_compras'),
    
    path('editar-perfil/', ProfileUpdateView.as_view(), name='edit_profile'),
    #path('registro_exitoso/', registro_exitoso, name='registro_exitoso'),
    path('logout/', logout_view, name='logout'),
     path('login/', custom_login, name='login'),
    path('registro/', register, name='register'),
    path('profile/', profile_view, name='profile'),
    
    #####terminoos####
     path('terminos/', views.terminos, name='terminos'),  # URL para los términos
     path('terminos-condiciones/', views.terminos_condiciones, name='terminos_condiciones'),
    path('politica-privacidad/', views.politica_privacidad, name='politica_privacidad'),
    path('terminos-rembolso/', views.terminos_rembolso, name='terminos_rembolso'),
    
    path('password_reset/', custom_password_reset_request, name='password_reset'),
    path('password_reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password_reset_confirm/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    
    path('color', views.color_list, name='color_list'),
    path('crear_color/', views.color_create, name='color_create'),
    path('editar/<int:pk>/', views.color_edit, name='color_edit'),
    path('eliminar/<int:pk>/', views.color_delete, name='color_delete'),
    
    path('categorias/', views.categoria_list, name='categoria_list'),
    path('categorias/crear/', views.categoria_create, name='categoria_create'),
    path('categorias/editar/<int:pk>/', views.categoria_edit, name='categoria_edit'),
    path('categorias/eliminar/<int:pk>/', views.categoria_delete, name='categoria_delete'),
    
    
]# Solo en desarrollo, servir archivos de medios

