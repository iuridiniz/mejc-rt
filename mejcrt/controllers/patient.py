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

from flask import request, json
from flask.helpers import make_response, url_for
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

@app.route("/api/v1/patient/stats", methods=['GET'], endpoint="patient.stats")
@require_login()
def stats():
    stats = {}
    stats['all'] = Patient.count()
    return make_response(
         jsonify(code="OK", data={'stats': stats}), 200, {})

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
    name = None
    code = None
    if "name" in fields:
        name = query
    if "code" in fields:
        code = query
    objs = Patient.build_query(name, code).fetch(max_)
    return make_response(jsonify(data=[p.to_dict() for p in objs],
                                 code='OK'), 200, {})

def _get_multi():
    max_ = int(request.args.get("max", '20'))
    offset = int(request.args.get('offset', '0'))

    if offset < 0:
        offset = 0

    if max_ > 50:
        max_ = 50
    if max_ < 0:
        max_ = 0

    total = Patient.count()

    objs = []
    if max_:
        objs = Patient.build_query().fetch(limit=max_, offset=offset)
    count = len(objs)

    query_next = {'max': max_, 'offset': max_ + offset}

    if count < max_:
        query_next['offset'] = count + offset

    query_prev = {'max': max_, 'offset': offset - max_}
    if offset - max_ < 0:
        query_prev['offset'] = 0
        query_prev['max'] = offset

    next_ = url_for("patient.get", **query_next)
    prev = url_for("patient.get", **query_prev)

    return make_response(jsonify(data=[p.to_dict() for p in objs],
                                 code='OK',
                                 total=total,
                                 next=next_,
                                 prev=prev,
                                 count=count),
                         200, {})


@app.route("/api/v1/patient/", methods=["GET"], endpoint="patient.get")
@app.route("/api/v1/patient/<key>", methods=["GET"], endpoint="patient.get")
@require_login()
def get(key=None):
    if key is None:
        return _get_multi()

    key = ndb.Key(urlsafe=key)

    p = key.get()
    if p is None:
        return make_response(jsonify(code="Not Found"), 404, {})

    return make_response(jsonify(data=p.to_dict(), code='OK'), 200, {})


@app.route("/api/v1/patient/list/columns", methods=["GET"], endpoint="patient.list_columns")
@require_login()
def list_columns():
    # TODO: use gettext
    defs = [
        {
            "data": "key",
            "title": "Chave",
            "visible": False,
            'searchable': False,
            'orderable': False,
        },
        {
            "data": "name",
            "title": "Nome",
            "visible": True,
            'searchable': True,
            'orderable': True
        },
        {
            "data": "code",
            "title": u"Prontu\xe1rio",
            "visible": True,
            'searchable': True,
            'orderable': True
        },
        {
            "data": "blood_type",
            "title": u"Tipo sangu\xedneo",
            "visible": True,
            'searchable': False,
            'orderable': False
        },
        {
            "data": "type",
            "title": u"Tipo de paciente",
            "visible": True,
            'searchable': False,
            'orderable': False
        },
    ]
    return make_response(json.dumps(defs), 200, {'content-type': "application/json"})

# TODO: remove this code or build a test
@app.route("/api/v1/patient/list", methods=["POST"], endpoint="patient.list")
@require_login()
def list_():

    # Validate
    if request.json is None:
        logging.error("Missing json on %r" % (request))
        return make_response(jsonify(code="Bad Request"), 400, {})

    required = ["columns", "draw", "start", "search", "length", "order"]
    if not all([c in request.json for c in required]):
        logging.error("Invalid JSON data in %r:%r" % (request.json,
                  [(c, c in request.json) for c in required]))
        return make_response(jsonify(code="Bad Request"), 400, {})

    # logging.info(request.json)
    fields = [c.get('data') for c in request.json['columns']]
    if not all(fields):
        logging.error("Missing 'data' on some columns of %r:%r" % (request.json,
                  [(c, c.get('data')) for c in request.json['columns']]))
        return make_response(jsonify(code="Bad Request"), 400, {})

    search = request.json['search'].get('value')
    if type(search) != unicode:
        logging.error("Invalid 'search' %r of %r" % (request.json['search'], request.json))
        return make_response(jsonify(code="Bad Request"), 400, {})

    start = request.json['start']
    if type(start) != int:
        logging.error("Invalid 'start' %r of %r" % (request.json['start'], request.json))
        return make_response(jsonify(code="Bad Request"), 400, {})

    length = request.json['length']
    if type(length) != int:
        logging.error("Invalid 'length' %r of %r" % (request.json['length'], request.json))
        return make_response(jsonify(code="Bad Request"), 400, {})

    order = request.json['order']
    orders = []
    for ord_ in order[:1]:  # only the first order
        column_index = ord_.get('column', -1)
        column_dir = ord_.get('dir', "")
        if (type(column_index) != int or
            column_index < 0 or
            column_index >= len(fields) or
            column_dir not in ("asc", 'desc')):
                logging.error("Invalid 'order' %r of %r" % (ord_, request.json))
                return make_response(jsonify(code="Bad Request"), 400, {})


        field = fields[column_index]
        if field in ('code', 'name'):
            if column_dir == 'desc':
                orders.append(-getattr(Patient, field))
            else:
                orders.append(getattr(Patient, field))

    draw = request.json['draw']

    filters = []

    if search:
        for field in fields:
            if field == "code":
                filters.append(Patient.code_tags == iconv(search).strip().lower())
            if field == "name":
                filters.append(Patient.name_tags == iconv(search).strip().lower())

    query = Patient.query()
    records_total = Patient.count()
    records_filtered = Patient.count()
    if filters:
        query = query.filter(ndb.OR(*filters))
        records_filtered = query.count()
    if orders:
        logging.info("%r" % orders)
        query = query.order(*orders)
    objs = query.fetch(limit=length,
                                      offset=start)

    data = []
    for o in objs:
        e = {}
        for f in fields:
            if f in ("name", "code", "blood_type"):
                e[f] = getattr(o, f)
                continue
            if f == "type":
                e[f] = o.type_
                continue
            if f == "key":
                e[f] = o.key.urlsafe()
                continue

        data.append(e)
    ret = dict(draw=draw,
               recordsTotal=records_total,
               recordsFiltered=records_filtered,
               data=data)

    return make_response(jsonify(ret), 200, {})

@app.route("/api/v1/patient/types",
           methods=["GET"],
           endpoint="patient.types")
@require_login()
def get_blood_contents():
    return make_response(jsonify(data=dict(types=patient_types), code="OK"), 200, {})
