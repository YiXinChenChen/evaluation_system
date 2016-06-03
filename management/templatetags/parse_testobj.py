# -*- coding:utf-8 -*-
from django import template

register = template.Library()


@register.filter
def parse_testobj_app(v, args):
    if args is None:
        return '未知App'

    if v in args:
        return args.get(v)

    return '未知App'


@register.filter
def parse_testobj_scene(v, args):
    if args is None:
        return '未知Scene'

    if v in args:
        return args.get(v)

    return '未知Scene'
    
testObjTypes = {'image':'图片','media':'视频'}

@register.filter
def parse_testobj_type(v):
    if v in testObjTypes:
        return testObjTypes.get(v)

    return '未知类型'
    