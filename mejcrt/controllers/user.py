'''
Created on 17/12/2015

@author: Iuri Diniz <iuridiniz@gmail.com>
'''
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


import logging

from flask.globals import request
from flask.helpers import make_response
from flask.json import jsonify
from google.appengine.ext.db import BadValueError

from ..app import app
from ..models import UserPrefs
from .decorators import require_login


@app.route("/api/v1/user", methods=['PUT'],
           endpoint="user.update")
@require_login()
def update():
    if not hasattr(request, 'json') or request.json is None:
        logging.error("Cannot update user from %r: %r" % (request, 'no json'))
        return make_response(jsonify(code="Bad Request"), 400, {})

    userid = request.json.get('id', None)
    u = UserPrefs.get_by_userid(userid)
    if u is None:
        logging.error("Cannot update user from %r: %r" % (request.json, 'No such user'))
        return make_response(jsonify(code="Not found"), 404, {})

    # check for restricted fields
    authorized = request.json.get('authorized', None)
    admin = request.json.get('admin', None)
    cur = UserPrefs.get_current()
    if (authorized is not None or admin is not None) and not cur.admin:
        # only if admin could do this
        # forbidden
        logging.error("User %r is not admin, but tried to update user %r using %r" % (cur, u, request.json))
        return make_response(jsonify(code="Forbidden"), 403, {})

    if cur.userid != u.userid and not cur.admin:
        # only admin could change anyone
        logging.error("User %r cannot change user %r" % (cur, u))
        return make_response(jsonify(code="Forbidden"), 403, {})

    if authorized is None:
        authorized = u.authorized
    if admin is None:
        admin = u.admin

    email = request.json.get('email', u.email)
    name = request.json.get('name', u.name)

    try:
        u.populate(name=name,
                   authorized=authorized,
                   email=email,
                   admin=admin)
        key = u.put()
    except BadValueError as e:
        logging.error("Cannot update user from %r: %r" % (request.json, e))
        return make_response(jsonify(code="Bad Request"), 400, {})

    return make_response(jsonify(code="OK", key=key.urlsafe()), 200, {})
