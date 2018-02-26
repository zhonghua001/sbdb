from django import template
import datetime
from dbmanage.myapp.include.encrypt import prpcrypt
register = template.Library()

@register.filter
def descrypt(values):
    py = prpcrypt()
    values = py.decrypt(values)
    return values


@register.filter
def s_to_d(values):
    # print(type(values))
    if isinstance(values,str):
        values = 0
    if values >0:
        days = int(values/(3600*24))
        hour = int((values%(3600*24))/3600)
        min = int(values%3600/60)

        return '{}d, {}h, {}m'.format(days,hour,min)
    else:
        return 0

@register.filter
def adjtime(values):
    values = values-datetime.timedelta(hours=8)
    return values