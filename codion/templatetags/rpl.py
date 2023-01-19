from django import template

register = template.Library()

@register.filter
def to_spc(value):
    return value.replace('_', " ")