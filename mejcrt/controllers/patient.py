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

import logging

from flask import request
from flask.helpers import make_response
from flask.json import jsonify
from google.appengine.api.datastore_errors import BadValueError
from google.appengine.ext import ndb
from google.net.proto.ProtocolBuffer import ProtocolBufferDecodeError

from mejcrt.models import UserPrefs, patient_types
from mejcrt.util import iconv

from ..app import app
from ..models import Patient, LogEntry
from .decorators import require_login


def parse_fields(f):
    "transform to lowercase, remove any spaces and split on ','"
    return (''.join(f.lower().split())).split(',')

@app.route("/api/v1/patient", methods=['POST', 'PUT'], endpoint="patient.upinsert")
@require_login()
def create_or_update():
    if request.json is None:
        return make_response(jsonify(code="Bad Request"), 400, {})

    patient_key = request.json.get('key', None)
    code = request.json.get('code', None)
    patient = None
    is_new = False
    if patient_key:
        try:
            key = ndb.Key(urlsafe=patient_key)
            patient = key.get()
            code = patient.code
        except ProtocolBufferDecodeError:
            pass
    else:
        is_new = True
        patient = Patient(id=code)

    logs = patient.logs or []
    logs.append(LogEntry.from_user(UserPrefs.get_current(), is_new))

    name = request.json.get('name', None)

    type_ = request.json.get('type', '')
    blood_type = request.json.get('blood_type', None)
    try:
        patient.populate(name=name, type_=type_, blood_type=blood_type, logs=logs)
        key = patient.put(update=not is_new)
    except BadValueError as e:
        logging.error("Cannot create Patient from %r: %r" % (request.json, e))
        return make_response(jsonify(code="Bad Request"), 400, {})

    return make_response(jsonify(code="OK", data=dict(key=key.urlsafe())), 200, {})

@app.route("/api/v1/patient/search/<query>", methods=["GET"],
           endpoint="patient.search")
@require_login()
def search(query):
    if not hasattr(request, 'args'):
        return make_response(jsonify(code="Bad Request"), 400, {})
    fields = parse_fields(request.args.get('fields', 'name'))
    max_ = int(request.args.get('max', '20'))

    if max_ > 40:
        max_ = 40
    if max < 1:
        return make_response(jsonify(code="OK", data=[]), 200, {})
    filters = []
    if "name" in fields:
        filters.append(Patient.name_tags == iconv(query).strip().lower())
    if "code" in fields:
        filters.append(Patient.code_tags == query)
    objs = Patient.query(ndb.OR(*filters)).fetch(max_)
    return make_response(jsonify(data=[p.to_dict() for p in objs],
                                 code='OK'), 200, {})


@app.route("/api/v1/patient/<key>", methods=["GET"], endpoint="patient.get")
@require_login()
def get(key):
    key = ndb.Key(urlsafe=key)

    p = key.get()
    if p is None:
        return make_response(jsonify(code="Not Found"), 404, {})

    return make_response(jsonify(data=p.to_dict(), code='OK'), 200, {})

@app.route("/api/v1/patient/types",
           methods=["GET"],
           endpoint="patient.types")
@require_login()
def get_blood_contents():
    return make_response(jsonify(data=dict(types=patient_types), code="OK"), 200, {})
