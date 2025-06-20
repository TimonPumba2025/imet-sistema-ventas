from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def format_cantidad(value, unidad_medida):
    """
    Formatea la cantidad según la unidad de medida
    Si es 'unidad', muestra como entero
    Si es peso/volumen, muestra con decimales
    """
    if not value:
        return "0"
    
    # Si la unidad es 'unidad' y el valor es un número entero
    if unidad_medida == 'unidad' and value == int(value):
        return str(int(value))
    else:
        # Para kg, g, l, ml - mostrar con decimales apropiados
        if unidad_medida in ['kg', 'l']:
            return f"{value:.3f}".rstrip('0').rstrip('.')
        elif unidad_medida in ['g', 'ml']:
            return f"{value:.1f}".rstrip('0').rstrip('.')
        else:
            return str(value)
