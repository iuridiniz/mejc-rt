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
Created on 08/12/2015

@author: Iuri Diniz <iuridiniz@gmail.com>
'''
from google.appengine.api.datastore_errors import BadValueError
from google.appengine.ext import ndb

from .util import onlynumbers, iconv, tokenize
# Models
blood_types = ('A+', 'B+', 'AB+', "O+", 'A-', 'B-', 'AB-', "O-")
blood_contents = ('CHPL', 'CP', 'PF', 'CHPLI')
patient_types = ("RN", "G", "O")
valid_locals = ["unidade-a", "unidade-b", 'unidade-b4', 'alto-risco',
        'uti-neonatal', 'uti-materna', 'sem-registro']
transfusion_tags = ['semrt', 'rt', "ficha-preenchida", "carimbo-plantao",
        "carimbo-nhh", "anvisa", "visitado"]

valid_actions = ["create", 'update']

class LogEntry(ndb.Model):
    userid = ndb.StringProperty(required=True, indexed=False)
    email = ndb.StringProperty(required=True, indexed=False)
    when = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    action = ndb.StringProperty(indexed=False, required=True, choices=valid_actions)

    @classmethod
    def from_user(cls, user, is_new):
        return cls(userid=user.user_id(), email=user.email(),
                   action="create" if is_new else "update")

class PatientCode(ndb.Model):
    pass

class Patient(ndb.Model):
    object_version = ndb.IntegerProperty(default=1, required=True)

    name = ndb.StringProperty(indexed=False, required=True)
    code = ndb.StringProperty(indexed=True, required=True, validator=onlynumbers)
    blood_type = ndb.StringProperty(indexed=False, required=True, choices=blood_types)
    type_ = ndb.StringProperty(indexed=False, required=True,
        choices=patient_types)
    logs = ndb.StructuredProperty(LogEntry, repeated=True)

    name_tags = ndb.ComputedProperty(lambda self: self._gen_tokens_for_name(self.name), repeated=True)
    code_tags = ndb.ComputedProperty(lambda self: self._gen_tokens_for_code(self.code), repeated=True)

    def _gen_tokens_for_name(self, name):
        return list(tokenize(iconv(name.lower()), minimum=4, maximum=4))
    def _gen_tokens_for_code(self, code):
        return list(tokenize(iconv(code.lower())))

    @ndb.transactional
    def put(self, **ctx_options):
        key = Patient.get_by_code(self.code, onlykey=True)
        if key and key != self.key:
            raise BadValueError("Patient.code %r is duplicated" % self.code)
        if self.key is None:
            self.key = ndb.Key(PatientCode, self.code, self.__class__, None)
        return super(Patient, self).put(**ctx_options)

    @classmethod
    def get_by_code(cls, code, onlykey=False):
        result = Patient.query(ancestor=ndb.Key(PatientCode, code)).get(keys_only=onlykey)
        return result

class BloodBag(ndb.Model):
    type_ = ndb.StringProperty(indexed=False, required=True, choices=blood_types)
    content = ndb.StringProperty()

class TransfusionCode(ndb.Model):
    pass

class Transfusion(ndb.Model):
    object_version = ndb.IntegerProperty(default=1, required=True)

    patient_key = ndb.KeyProperty(Patient, required=True, indexed=True)
    code = ndb.StringProperty(indexed=True, required=True, validator=onlynumbers)
    date = ndb.DateProperty(indexed=True, required=True)

    local = ndb.StringProperty(indexed=False, required=True,
        choices=valid_locals)
    bags = ndb.LocalStructuredProperty(BloodBag, repeated=True)

    tags = ndb.StringProperty(repeated=True, indexed=False,
        choices=transfusion_tags)
    text = ndb.TextProperty(required=False)
    logs = ndb.StructuredProperty(LogEntry, repeated=True)

    added_at = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated_at = ndb.DateTimeProperty(auto_now=True, indexed=False)

    @property
    def patient(self):
        return self.patient_key.get()

    @ndb.transactional
    def put(self, **ctx_options):
        key = self.get_by_code(self.code, onlykey=True)
        if key and key != self.key:
            raise BadValueError("Transfusion.code %r is duplicated" % self.code)

        # inject key
        if self.key is None:
#             key_flat = ndb.Key(TransfusionCode, self.code, self.__class__, None).flat()
#             key_flat = self.patient_key.flat() + key_flat
#             self.key = ndb.Key(*key_flat)
            self.key = ndb.Key(TransfusionCode, self.code, self.__class__, None)
        return ndb.Model.put(self, **ctx_options)

    @classmethod
    def get_by_code(cls, code, onlykey=False):
        result = Transfusion.query(ancestor=ndb.Key(TransfusionCode, code)).get(keys_only=onlykey)
        return result

