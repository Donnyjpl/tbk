from django import template

register = template.Library()

@register.filter
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})

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

