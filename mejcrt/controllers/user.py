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
from google.appengine.api import users
from google.appengine.ext.db import BadValueError

from mejcrt.controllers.patient import parse_fields, \
    make_response_list_paginator, str2bool

from ..app import app
from ..models import UserPrefs
from .decorators import require_login

def _get_multi():
    max_ = int(request.args.get("max", '20'))
    offset = int(request.args.get('offset', '0'))
    q = request.args.get('q', '') or None
    fields = dict([(f, q) for f in parse_fields(request.args.get('fields', ''))])

    total = UserPrefs.build_query().count()
    admin = str2bool(fields.get('admin', None))
    authorized = str2bool(fields.get('admin', None))

    query = UserPrefs.build_query(admin=admin, authorized=authorized)
    endpoint = "user.get"

    return make_response_list_paginator(max_=max_,
                                        offset=offset,
                                        q=q,
                                        fields=','.join(fields.keys()),
                                        dbquery=query,
                                        total=total,
                                        endpoint=endpoint)

@app.route("/api/v1/user", methods=['GET'],
           endpoint="user.get")
@app.route("/api/v1/user/<who>", methods=['GET'],
           endpoint="user.get")
@require_login()
def get(who=None):
    if who is None:
        return _get_multi()
    cur = UserPrefs.get_current()

    if who == 'me':
        u = cur
    else:
        u = UserPrefs.get_by_userid(who)

    if u is None:
        return make_response(jsonify(code="Not found"), 404, {})

    # XXX: any logged user can get info about any user
    # if u.userid != cur.userid and not cur.admin:
    #    logging.error("User %r cannot get info about user %r" % (cur, u))
    #    return make_response(jsonify(code="Forbidden"), 403, {})

    return make_response(jsonify(code="OK", data=dict(user=u.to_dict())))

@app.route("/api/v1/user/login/google", methods=['GET'],
           endpoint='user.login.google')
def login_google():
    continue_ = request.args.get('continue')
    if not continue_:
        return make_response(jsonify(code="Bad request"), 400, {})
    url = users.create_login_url(continue_)
    return make_response(jsonify({'code':"OK", 'continue':url}), 200, {})

@app.route("/api/v1/user/logout/google", methods=['GET'],
           endpoint='user.logout.google')
def logout_google():
    continue_ = request.args.get('continue')
    if not continue_:
        return make_response(jsonify(code="Bad request"), 400, {})
    url = users.create_logout_url(continue_)
    return make_response(jsonify({'code':"OK", 'continue':url}), 200, {})

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

    return make_response(jsonify(code="OK", data=dict(key=key.urlsafe())), 200, {})
