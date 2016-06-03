# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.shortcuts import render_to_response


class RejectMobileMiddleware:
    def __init__(self):
        pass

    @classmethod
    def _is_mobile_request(cls, request):
        user_agent = request.META['HTTP_USER_AGENT']
        return user_agent.find('Mobile') >= 0

    # def process_request(self, request):
    #     if not self._is_mobile_request(request):
    #         return None
    #     return HttpResponse(request.META['HTTP_USER_AGENT'])

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not self._is_mobile_request(request):
            return None
        return render_to_response('sqa/mobile_not_allow.html')
