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
from itertools import chain, combinations
from unicodedata import normalize

from google.appengine.ext import ndb

from flask import Flask, make_response, redirect, request
from flask.json import jsonify


# from google.appengine.api import users
app = Flask(__name__)
app.debug = True

# @app.route("/signin")
# def signin():
#     response = make_response()
#     user = users.get_current_user()

#     if user:
#         print "user"
#         response.headers['Content-Type'] = 'text/html; charset=utf-8'
#         response.set_data('Hello, ' + user.nickname())
#     else:
#         redirect(users.create_login_url(request.url))

#     return response

#################################################################
# Utility Functions

def iconv(input_str):
    if type(input_str) == str:
        # assume utf-8 strings
        input_str = input_str.decode('utf-8')
    return normalize("NFKD", input_str).encode('ascii', 'ignore')

def onlynumbers(obj, input_str, *args, **kwargs):
    return ''.join(filter(lambda x: x.isdigit(), str(input_str)))

def powerset(iterable):
    # from https://docs.python.org/2/library/itertools.html#recipes
    xs = list(iterable)
    # note we return an iterator rather than a list
    return chain.from_iterable(combinations(xs, n) for n in range(len(xs) + 1))

def tokenize(phrase, minimum=None, maximum=None, onlystart=True, combine=True):
    GOOD_NUMBER = 4
    if minimum is not None and maximum is None:
        # only minimum defined
        maximum = minimum + GOOD_NUMBER
    elif maximum is not None and minimum is None:
        # only maximum defined
        minimum = maximum - GOOD_NUMBER
    elif maximum is None and minimum is None:
        # both undefined
        minimum = GOOD_NUMBER
        maximum = minimum + GOOD_NUMBER

    if minimum < 1:
        minimum = 1
    if maximum < 1:
        maximum = 1

    tokens = set()
    words = filter(lambda x: len(x) >= minimum, str(phrase).split())
    # add each word and word combination
    if not combine:
        for word in words:
            tokens.add(word)
    else:
        for combination in [" ".join(s) for s in  powerset(words)]:
            if len(combination):
                tokens.add(combination)

    for word in words:
        # add partial words
        length = len(word)

        for i in xrange(1 if onlystart else length):
            first = i + minimum
            last = maximum + i
            if last > length:
                last = length
            if first > length:
                first = length
            for j in xrange(i + minimum, last + 1):
                tokens.add(word[i:j])

    return tokens

# Models
blood_types = ('A+', 'B+', 'AB+', "O+", 'A-', 'B-', 'AB-', "O-")

class Patient(ndb.Model):
    name = ndb.StringProperty(indexed=False, required=True)
    code = ndb.StringProperty(indexed=True, required=True, validator=onlynumbers)
    blood_type = ndb.StringProperty(indexed=False, required=True, choices=blood_types)
    name_tags = ndb.ComputedProperty(lambda self: self._gen_tokens_for_name(self.name), repeated=True)
    code_tags = ndb.ComputedProperty(lambda self: self._gen_tokens_for_code(self.code), repeated=True)

    def _gen_tokens_for_name(self, name):
        return list(tokenize(iconv(name.lower()), minimum=4, maximum=4))
    def _gen_tokens_for_code(self, code):
        return list(tokenize(iconv(code.lower())))

class BloodBag(ndb.Model):
    type_ = ndb.StringProperty(indexed=False, required=True, choices=blood_types)
    content = ndb.StringProperty()

class Transfusion(ndb.Model):
    patient = ndb.StructuredProperty(Patient)
    nhh_code = ndb.StringProperty(indexed=True, required=True, validator=onlynumbers)
    date = ndb.DateProperty(indexed=True, required=True)
    local = ndb.StringProperty(indexed=False, required=True)
    bags = ndb.LocalStructuredProperty(BloodBag, repeated=True)
    tags = ndb.StringProperty(repeated=True, indexed=False,
                              choices=['rt', "ficha_preenchida", "carimbo_plantao", "carimbo_nhh", "anvisa"])
    text = ndb.TextProperty(required=False)

    added_at = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated_at = ndb.DateTimeProperty(auto_now=True, indexed=False)

@app.route("/")
def hello():
    return make_response("MEJC RT", 200, {})

@app.route("/api/transfusion/<tr_key>", methods=["GET"])
def get(tr_key):
    key = ndb.Key(urlsafe=tr_key)

    tr = key.get()
    if tr is None:
        return make_response(jsonify(code="NOT FOUND"), 404, {})

    ret = {
        "key": tr.key.urlsafe(),
        "name": tr.patient.name,
        "record": tr.patient.code,
        "blood_type": tr.patient.blood_type,
        "date": tr.date.strftime("%Y-%m-%d"),
        "local": tr.local,
        "blood_bags" :
        [
            {
                "type": bag.type_,
                "content": bag.content
            } for bag in tr.bags
        ],
        "text": tr.text,
        "tags": tr.tags,
        "nhh_code": tr.nhh_code
    }
    return make_response(jsonify(ret), 200, {})

@app.route("/api/transfusion/create", methods=['POST'])
def create():
    """"
    example:
    {
        "name": "John Heyder Oliveira de Medeiros Galvão",
        "record": "12345/0",
        "blood_type": "O+",
        "date": "2015-05-22",
        "local": "UTINEO",
        "blood_bags" : 
        [
            {
                "type": "O-", 
                "content": "CHPLI"
            } 
        ],
        "text": "",
        "tags": [],
        "nhh_code": "20900"
    }
    
    """
    if not hasattr(request, 'json'):
        return make_response(jsonify(code="ERROR"), 500, {})

    patient = request.json.get('name', None)
    record_code = request.json.get('record', None)
    blood_type = request.json.get('blood_type', None)
    transfusion_date = request.json.get('date', None)
    transfusion_local = request.json.get('local', None)
    bags = []
    for bag in request.json.get('bags', []):
        bags.put(BloodBag(type_=bag['type'], content=bag['content']))
    text = request.json.get('text', None) or None
    tags = request.json.get('tags', [])

    nhh_code = request.json.get('nhh_code', None)
    tr = Transfusion(patient=Patient(name=patient,
                                     blood_type=blood_type,
                                     code=record_code),
                     nhh_code=nhh_code,
                     date=datetime.strptime(transfusion_date, "%Y-%m-%d"),
                     local=transfusion_local,
                     bags=bags,
                     tags=tags,
                     text=text)
    key = tr.put()

    return make_response(jsonify(code="OK", key=key.urlsafe()), 200, {})
