# -*- coding:utf-8 -*-
from django import template

suite_status_map={}
suite_status_map['ready'] = '准备中'
suite_status_map['testing'] = '进行中'
suite_status_map['finished'] = '已完成'

suite_types_map={}
suite_status_map['manually'] = '手动创建'

register = template.Library()


@register.filter
def parse_suite_status(value):
    return suite_status_map.get(value, value)


@register.filter
def parse_suite_type(value):
    return suite_status_map.get(value, value)


@register.filter
def get_cases(value, arg_group_id):
    return [item for item in value if item.group_id == arg_group_id]