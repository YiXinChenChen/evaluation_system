# -*- coding: utf-8 -*-
__author__ = 'LibX'
__all__ = ['EncodingFormatter']

import logging


class EncodingFormatter(logging.Formatter):
    def __init__(self, fmt, datefmt=None, encoding=None):
        logging.Formatter.__init__(self, fmt, datefmt)
        self.encoding = encoding

    def format(self, record):
        result = logging.Formatter.format(self, record)
        if isinstance(result, unicode):
            result = result.encode(self.encoding or 'utf-8')
        return result
