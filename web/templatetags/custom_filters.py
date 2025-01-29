from django import template

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
    """Formatea el precio de un número entero, agregando puntos como separadores de miles."""
    try:
        # Convierte el valor en un número entero y luego lo formatea
        value = str(value)
        entero, decimal = value.split(".") if "." in value else (value, "")
        entero = entero[::-1]  # Invertir el entero
        entero = ".".join([entero[i:i+3] for i in range(0, len(entero), 3)])[::-1]  # Agregar puntos
        return f"{entero}{'.' + decimal if decimal else ''}"
    except ValueError:
        return value

