from .models import Categoria

def categorias_y_datos_adicionales(request):
    # Obtener las categorías
    categorias = Categoria.objects.all()

    # Obtener el carrito y contar los productos
    carrito = request.session.get('carrito', {})
    cantidad_carrito = sum(item['cantidad'] for producto in carrito.values() for item in producto.get('tallas', {}).values())

    # Obtener los favoritos y contar la cantidad de productos
    favoritos = request.session.get('favoritos', {})
    cantidad_favoritos = len(favoritos)

    # Retornar todo en un diccionario
    return {
        'categorias': categorias,
        'cantidad_carrito': cantidad_carrito,
        'cantidad_favoritos': cantidad_favoritos,
    }
