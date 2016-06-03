# -*- coding: utf-8 -*-
__author__ = 'LibX'

from django import forms


class VoteForm(forms.Form):
    # suite_uuid = forms.CharField()
    case_id = forms.IntegerField()
    vote = forms.IntegerField()


class UserInfoForm(forms.Form):
    phone = forms.RegexField(regex=r'^\d{11}$', required=True,
                             error_messages={'required': u'请输入手机号', 'invalid': u'无效手机号，必须为11位数字'})
    yy = forms.RegexField(regex=r'^\d+$', required=True,
                          error_messages={'required': u'请输入YY号', 'invalid': u'无效YY号，必须为数字'})
