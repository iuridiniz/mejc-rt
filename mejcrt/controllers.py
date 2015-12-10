# -*- coding: utf-8 -*-

'''
Created on 08/12/2015

@author: Iuri Diniz <iuridiniz@gmail.com>
'''
from datetime import datetime
import functools
import logging

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext.db import BadValueError
from google.net.proto.ProtocolBuffer import ProtocolBufferDecodeError

from __init__ import app
from flask import make_response, request
from flask.json import jsonify
from models import Transfusion, Patient, BloodBag, LogEntry
from utils import iconv

def require_login(admin=False):
    def decorate(fn):
        @functools.wraps(fn)
        def handler(*args, **kwargs):
            user = users.get_current_user()
            if user is None:
                return make_response(jsonify(code="Unauthorized"), 401, {})
            if admin and not users.is_current_user_admin():
                return make_response(jsonify(code="Forbidden"), 403, {})
            return fn(*args, **kwargs)
        return handler
    return decorate

@app.route("/")
def hello():
    return make_response("MEJC RT", 200, {})

@app.route("/api/v1/patient", methods=['POST', 'PUT'])
@require_login()
def create_or_update_patient():
    if request.json is None:
        return make_response(jsonify(code="Bad Request"), 400, {})

    patient_key = request.json.get('key', None)
    patient = None
    is_new = False
    if patient_key:
        try:
            key = ndb.Key(urlsafe=patient_key)
            patient = key.get()
        except ProtocolBufferDecodeError:
            pass
    else:
        is_new = True
        patient = Patient()

    logs = patient.logs or []
    logs.append(LogEntry.from_user(users.get_current_user(), is_new))

    name = request.json.get('name', None)
    code = request.json.get('record', '')
    kind = request.json.get('kind', '')
    blood_type = request.json.get('blood_type', None)
    try:
        patient.populate(name=name, code=code, type_=kind, blood_type=blood_type, logs=logs)
        key = patient.put()
    except BadValueError as e:
        logging.error("Cannot create Patient from %r: %r" % (request.json, e))
        return make_response(jsonify(code="Bad Request"), 400, {})

    return make_response(jsonify(code="OK", key=key.urlsafe()), 200, {})

@app.route("/api/v1/patient/<tr_key>", methods=["GET"])
@require_login()
def get_patient(tr_key):
    key = ndb.Key(urlsafe=tr_key)

    p = key.get()
    if p is None:
        return make_response(jsonify(code="Not Found"), 404, {})

    ret = {
        "key": p.key.urlsafe(),
        "name": p.name,
        "record": p.code,
        "kind": p.type_,
        "blood_type": p.blood_type,
        'logs': [
             {
                'email': log.email,
                'action': log.action,
                'when': log.when.strftime("%Y-%m-%d %H:%M:%S"),
              } for log in p.logs
         ]
    }
    return make_response(jsonify(ret), 200, {})

@app.route("/api/v1/transfusion/search", methods=['GET'])
@require_login()
def search():
    if not hasattr(request, 'args'):
        return make_response(jsonify(code="Bad Request"), 400, {})
    query_record = request.args.get('record')
    query_nhh = request.args.get('nhh_code')
    query_name = request.args.get('name')

    query = Transfusion.query()

    if query_record:
        keys = Patient.query().filter(Patient.code_tags == query_record).fetch(keys_only=True)
        query = query.filter(Transfusion.patient_key.IN(keys))
    elif query_nhh:
        query = query.filter(Transfusion.nhh_code == query_nhh)
    elif query_name:
        query_name = iconv(query_name).lower()
        keys = Patient.query().filter(Patient.name_tags == query_name).fetch(keys_only=True)
        query = query.filter(Transfusion.patient_key.IN(keys))
    else:
        query = None

    keys = []
    if query:
        for i, key in enumerate(query.iter(keys_only=True)):
            if i == 20:
                break
            keys.append(key.urlsafe())

    return make_response(jsonify({'keys':keys}), 200, {})

@app.route("/api/v1/transfusion/<tr_key>", methods=["GET"])
@require_login()
def get(tr_key):
    key = ndb.Key(urlsafe=tr_key)

    tr = key.get()
    if tr is None:
        return make_response(jsonify(code="Not Found"), 404, {})

    ret = {
        "key": tr.key.urlsafe(),
        "patient_key": tr.patient_key.urlsafe(),
        "date": tr.date.strftime("%Y-%m-%d"),
        "local": tr.local,
        "bags" :
        [
            {
                "type": bag.type_,
                "content": bag.content
            } for bag in tr.bags
        ],
        "text": tr.text,
        "tags": tr.tags,
        "nhh_code": tr.nhh_code,
        'logs': [
             {
                'email': log.email,
                'action': log.action,
                'when': log.when.strftime("%Y-%m-%d %H:%M:%S"),
              } for log in tr.logs
         ]
    }
    return make_response(jsonify(ret), 200, {})

@app.route("/api/v1/transfusion", methods=['POST', 'PUT'])
@require_login()
def create_or_update():
    if not hasattr(request, 'json') or request.json is None:
        return make_response(jsonify(code="Bad Request"), 400, {})

    tr_key = request.json.get('key', None)
    tr = None
    is_new = False
    if tr_key:
        # update a transfusion
        try:
            key = ndb.Key(urlsafe=tr_key)
            tr = key.get()
        except ProtocolBufferDecodeError:
            return make_response(jsonify(code="Not Found"), 404, {})
        patient_key = tr.patient_key
    else:
        # create a new transfusion
        is_new = True
        tr = Transfusion()
        patient_key = None
        patient_key_url_safe = request.json.get('patient_key', None)
        patient_record_code = request.json.get('record', None)
        if patient_key_url_safe is not None:
            try:
                patient_key = ndb.Key(urlsafe=patient_key_url_safe)
            except ProtocolBufferDecodeError:
                pass
        elif patient_record_code:
            patient_key = Patient.get_by_code(patient_record_code, onlykey=True)

    transfusion_date = request.json.get('date', None)
    transfusion_local = request.json.get('local', None)
    bags = []
    for bag in request.json.get('bags', []):
        bags.append(BloodBag(type_=bag['type'], content=bag['content']))
    text = request.json.get('text', None) or None
    tags = request.json.get('tags', [])

    nhh_code = request.json.get('nhh_code', None)
    logs = tr.logs or []

    logs.append(LogEntry.from_user(users.get_current_user(), is_new))
    try:
        tr.populate(patient_key=patient_key,
                    nhh_code=nhh_code,
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

    return make_response(jsonify(code="OK", key=key.urlsafe()), 200, {})
