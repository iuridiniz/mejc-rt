# -*- coding: utf-8 -*-
# The MIT License (MIT)
#
# Copyright (c) 2015 Iuri Gomes Diniz
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
'''
Created on 10/12/2015

@author: Iuri Diniz <iuridiniz@gmail.com>
'''

import functools

from flask.helpers import make_response
from flask.json import jsonify

from mejcrt.models import UserPrefs


def require_admin():
    return _require_login(require_admin=True)

def require_login():
    return _require_login(require_admin=False)

def _require_login(require_admin=False):
    def decorate(fn):
        @functools.wraps(fn)
        def handler(*args, **kwargs):
            user = UserPrefs.get_current()
            if user is None:
                return make_response(jsonify(code="Unauthorized"), 401, {})

            if user.authorized is False:
                return make_response(jsonify(code="Forbidden"), 403, {})

            if require_admin and not user.admin:
                return make_response(jsonify(code="Forbidden"), 403, {})

            return fn(*args, **kwargs)
        return handler
    return decorate
