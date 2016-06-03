# -*- coding: utf-8 -*-
__author__ = 'LibX'

import urllib
import requests


class WeChatOpen:
    def __init__(self, **kwargs):
        self.app_id = kwargs.get('app_id', None)
        self.app_secret = kwargs.get('app_secret', None)

    def get_qrconnect_url(self, redirect_uri, response_type='code', scope='snsapi_login', state=''):
        query = {
            'appid': self.app_id,
            'redirect_uri': redirect_uri,
            'response_type': response_type,
            'scope': scope,
            'state': state,
        }
        query = urllib.urlencode(query)
        return 'https://open.weixin.qq.com/connect/qrconnect?%s#wechat_redirect' % (query,)

    def get_access_token(self, code):
        query = {
            'appid': self.app_id,
            'secret': self.app_secret,
            'code': code,
            'grant_type': 'authorization_code',
        }
        query = urllib.urlencode(query)
        url = 'https://api.weixin.qq.com/sns/oauth2/access_token?%s' % (query,)
        r = requests.get(url)
        return r.json()

    def refresh_token(self, refresh_token):
        query = {
            'appid': self.app_id,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        query = urllib.urlencode(query)
        url = 'https://api.weixin.qq.com/sns/oauth2/refresh_token?%s' % (query,)
        r = requests.get(url)
        return r.json()

    def get_userinfo(self, access_token, open_id):
        query = {
            'access_token': access_token,
            'openid': open_id
        }
        query = urllib.urlencode(query)
        url = 'https://api.weixin.qq.com/sns/userinfo?%s' % (query,)
        r = requests.get(url)

        # TODO if wechat fix the bug, please delete this line
        # why? r.json() use r.encoding as encoding to decode r.content
        # wechat give us a utf-8 string but 'tell' us this is an ascii string by HTTP
        # so we have to set utf-8 encoding manually
        r.encoding = 'utf-8'

        return r.json()
