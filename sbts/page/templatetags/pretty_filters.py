from django import template

register = template.Library()


@register.filter
def pretty_nbytes(nbytes):
    units = ['B', 'kiB', 'MiB', 'GiB', 'TiB', 'PiB']
    i = 0
    while i < len(units) - 1 and nbytes >= 1024:
        nbytes /= 1024
        i += 1

    if f'{nbytes:.1f}'.endswith('.0'):
        return f'{nbytes:,.0f} {units[i]}'
    else:
        return f'{nbytes:,.1f} {units[i]}'
