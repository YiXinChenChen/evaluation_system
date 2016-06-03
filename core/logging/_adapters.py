# -*- coding: utf-8 -*-
__author__ = 'LibX'
__all__ = ['ExecutionLoggerAdapter']

import logging


class ExecutionLoggerAdapter(logging.LoggerAdapter):
    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def process(self, msg, kwargs):
        request = self.extra['request']
        execution = self.extra['execution']

        ip = self.get_client_ip(request)
        path = request.path
        execution_id = execution.id if execution is not None else 'None'
        return '[%s] [IP:%s] [execution_id:%s] %s' % (path, ip, str(execution_id), msg), kwargs
