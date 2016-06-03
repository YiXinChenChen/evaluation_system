# -*- coding: utf-8 -*-
__author__ = 'LibX'

from django import forms


class SuiteStartForm(forms.Form):
    suite_id = forms.IntegerField()
    start_date = forms.DateField(input_formats=['%Y-%m-%d'])
    end_date = forms.DateField(input_formats=['%Y-%m-%d'])
    case_count = forms.IntegerField(required=False)
