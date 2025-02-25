from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def add_class(field, class_name):
    """Agrega una clase CSS a un campo de formulario"""
    return field.as_widget(attrs={'class': class_name})

@register.filter
def multiply(value, arg):
    """Multiplica dos números."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
    
@register.filter
def to(value):
    """Devuelve un rango hasta el número dado"""
    return range(1, value + 1)

@register.filter
def multiplicar(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
    
@register.filter
def formatear_precio(value):
    """Formatea el precio de un número, agregando puntos como separadores de miles y sin decimales."""
    try:
        # Asegúrate de que el valor sea un número Decimal o flotante
        value = Decimal(value) if not isinstance(value, Decimal) else value

        # Convertir el valor a un número entero
        value = int(value)  # Eliminar los decimales si los hay

        # Convertir el número en un string
        value_str = str(value)

        # Invertir el entero para agregar puntos cada tres caracteres
        entero = value_str[::-1]
        entero = ".".join([entero[i:i+3] for i in range(0, len(entero), 3)])[::-1]

        # Retornar el valor formateado sin decimales
        return entero
    except Exception as e:
        return value

@register.filter
def get_item(dictionary, key):
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def divide_into_groups(items, n):
    """Divide una lista en grupos de n elementos."""
    return [items[i:i+n] for i in range(0, len(items), n)]
