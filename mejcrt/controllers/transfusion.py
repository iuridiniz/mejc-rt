'''
Created on 10/12/2015

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


from datetime import datetime
import logging

from flask import request
from flask.helpers import make_response
from flask.json import jsonify
from google.appengine.api.datastore_errors import BadValueError
from google.appengine.ext import ndb
from google.net.proto.ProtocolBuffer import ProtocolBufferDecodeError

from mejcrt.models import valid_locals, blood_types, blood_contents, UserPrefs

from ..app import app
from ..models import Transfusion, Patient, BloodBag, LogEntry
from ..util import iconv
from .decorators import require_login

@app.route("/api/v1/transfusion/search", methods=['GET'], endpoint="transfusion.search")
@require_login()
def search():
    if not hasattr(request, 'args'):
        return make_response(jsonify(code="Bad Request"), 400, {})
    query_patient_code = request.args.get('patient_code')
    query_patient_name = request.args.get('patient_name')
    query_code = request.args.get('code')

    query = None

    if query_patient_code:
        keys = Patient.query().filter(Patient.code_tags == query_patient_code).fetch(keys_only=True)
        query = Transfusion.query().filter(Transfusion.patient.IN(keys))
    elif query_code:
        query = Transfusion.query().filter(Transfusion.code == query_code)
    elif query_patient_name:
        query_patient_name = iconv(query_patient_name).lower()
        keys = Patient.query().filter(Patient.name_tags == query_patient_name).fetch(keys_only=True)
        query = Transfusion.query().filter(Transfusion.patient.IN(keys))

    keys = []
    if query:
        for i, key in enumerate(query.iter(keys_only=True)):
            if i == 20:
                break
            keys.append(key.urlsafe())

    return make_response(jsonify(data=dict(keys=keys), code='OK'), 200, {})

@app.route("/api/v1/transfusion", methods=["GET"],
           endpoint="transfusion.get")
@app.route("/api/v1/transfusion/<key>", methods=["GET"],
           endpoint="transfusion.get")
@require_login()
def get(key=None):
    if key is not None:
        key = ndb.Key(urlsafe=key)
        tr = key.get()
        if tr is None or not isinstance(tr, Transfusion):
            return make_response(jsonify(code="Not Found"), 404, {})

        return make_response(jsonify(data=[tr.to_dict()], code='OK'), 200, {})

    max_ = int(request.args.get('max', '0'))
    if max_ > 40:
        max_ = 40
    if max_ > 0:
        objs = Transfusion.query().order(-Transfusion.date).fetch(max_)
        if objs:
            return make_response(jsonify(data=[tr.to_dict() for tr in objs], code='OK'), 200, {})

    return make_response(jsonify(code="Not Found"), 404, {})

@app.route("/api/v1/transfusion", methods=['POST', 'PUT'],
           endpoint="transfusion.upinsert")
@require_login()
def create_or_update():
    if not hasattr(request, 'json') or request.json is None:
        logging.error("Cannot create TR from %r: %r" % (request, 'no json'))
        return make_response(jsonify(code="Bad Request"), 400, {})

    tr_key = request.json.get('key', None)
    tr_code = request.json.get('code', None)
    tr = None
    is_new = False
    if tr_key and request.method == "PUT":
        # update a transfusion
        try:
            key = ndb.Key(urlsafe=tr_key)
            tr = key.get()
        except ProtocolBufferDecodeError:
            logging.error("Cannot create TR from %r: %r" % (request.json, 'invalid transfusion key'))
            return make_response(jsonify(code="Not Found"), 404, {})
        patient_key = tr.patient
        tr_code = tr.code
    elif tr_key is None and request.method == "POST":
        # create a new transfusion
        is_new = True

        patient_key = None
        patient_key_url_safe = request.json.get('patient_key', None)
        patient_record_code = request.json.get('record', None)
        patient_dict = request.json.get('patient', dict())

        if patient_key_url_safe is None and isinstance(patient_dict, dict):
            patient_key_url_safe = patient_dict.get('key')

        if patient_key_url_safe is not None:
            try:
                patient_key = ndb.Key(urlsafe=patient_key_url_safe)
            except ProtocolBufferDecodeError:
                pass
        elif patient_record_code:
            patient_key = Patient.get_by_code(patient_record_code, onlykey=True)

        if patient_key is None:
            # no patient key
            logging.error("Cannot create TR from %r: %r" % (request.json, 'no patient key'))
            return make_response(jsonify(code="Bad Request"), 400, {})

        tr = Transfusion()
    else:
        logging.error("Cannot create TR from %r: %r (%r)" % (request.json, 'incorrect method', request.method))
        return make_response(jsonify(code="Bad Request"), 400, {})

    transfusion_date = request.json.get('date', None)
    transfusion_local = request.json.get('local', None)
    bags = []
    for bag in request.json.get('bags', []):
        try:
            bags.append(BloodBag(type_=bag['type'], content=bag['content']))
        except BadValueError as e:
            logging.error("Cannot create TR from %r: %r" % (request.json, e))
            return make_response(jsonify(code="Bad Request"), 400, {})
    text = request.json.get('text', None) or None
    tags = request.json.get('tags', [])

    logs = tr.logs or []

    logs.append(LogEntry.from_user(UserPrefs.get_current(), is_new))
    try:

        tr.populate(patient=patient_key,
                    code=tr_code,
                    date=datetime.strptime(transfusion_date, "%Y-%m-%d"),
                    local=transfusion_local,
                    bags=bags,
                    logs=logs,
                    tags=tags,
                    text=text)
        key = tr.put()
    except BadValueError as e:
        logging.error("Cannot create TR from %r: %r" % (request.json, e))
        return make_response(jsonify(code="Bad Request"), 400, {})

    return make_response(jsonify(code="OK", data=dict(key=key.urlsafe())), 200, {})

@app.route("/api/v1/transfusion/locals", methods=["GET"], endpoint="transfusion.locals")
@require_login()
def get_locals():
    return make_response(jsonify(data=dict(locals=valid_locals), code="OK"), 200, {})

@app.route("/api/v1/transfusion/blood/types",
           methods=["GET"],
           endpoint="transfusion.blood.types")
@require_login()
def get_blood_types():
    return make_response(jsonify(data=dict(types=blood_types), code="OK"), 200, {})

@app.route("/api/v1/transfusion/blood/contents",
           methods=["GET"],
           endpoint="transfusion.blood.contents")
@require_login()
def get_blood_contents():
    return make_response(jsonify(data=dict(contents=blood_contents), code="OK"), 200, {})
