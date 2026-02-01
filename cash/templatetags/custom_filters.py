# myapp/templatetags/custom_filters.py
from django import template
from datetime import datetime
from django.template.defaultfilters import floatformat
register = template.Library()

@register.filter
def format_amount(value):
    """Format the amount with space as thousands separator and append 'FCFA'."""
    if value is None:
        return ''
    # Format the number with spaces as thousands separators
    formatted_value = f"{value:,.0f}".replace(',', ' ').replace('.', ',') 
    return formatted_value


@register.filter
def format_amount_compact(value):
    try:
        value = int(value)
        if value >= 1000000:
            return f"{value/1000000:.1f}M".replace('.', ',')
        elif value >= 1000:
            return f"{value/1000:.0f}k"
        else:
            return f"{value:,}".replace(',', ' ')
    except:
        return value

@register.filter
def format_date(value, date_format="DD/MM/YYYY"):
    if isinstance(value, datetime):
        return value.strftime(date_format)
    return value


@register.filter(name='unlocalize_amount')
def unlocalize_amount(value):
    """
    Removes localization formatting from a number.
    """
    if value is None:
        return '0'
    return str(value).replace(",", "")

@register.filter
def multiply(value, arg):
    """Multiplie value par arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def subtract(value, arg):
    """Soustrait arg de value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def add(value, arg):
    """Additionne value et arg"""
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return value    