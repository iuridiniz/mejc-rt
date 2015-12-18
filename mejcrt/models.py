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
import datetime

from google.appengine.api import users
from google.appengine.api.datastore_errors import BadValueError
from google.appengine.ext import ndb

from .util import onlynumbers, iconv, tokenize

# Models
blood_types = ('O-',
               'O+',
               'A-',
               'A+',
               'B-',
               'B+',
               'AB-',
               'AB+')
blood_contents = ('CH',
                  'CHPL',
                  'CHPLI',
                  'CHD',
                  'CHI',
                  'PF',
                  'CP',
                  'CRIO',
                  'ST')

patient_types = (u'Rec\xe9m-nascido',
                 u'Ginecol\xf3gico',
                 u'Obst\xe9trico')

valid_locals = ("Unidade A (Anexo)",
                "Unidade B",
                'Unidade B4',
                'Alto risco',
                'UTI Neonatal',
                'UTI Materna',
                'Sem registro')
transfusion_tags = ('semrt',
                    'rt',
                    'ficha-preenchida',
                    'carimbo-plantao',
                    'carimbo-nhh',
                    'anvisa',
                    'visitado')

valid_actions = ["create", 'update']


class Model(ndb.Model):
    __dict_include__ = None
    __dict_exclude__ = None

    @classmethod
    def _parse_data(cls, d):
        # FIXME: does not check if there's circular objects (make a set of ids?)
        ret = d
        if isinstance(d, ndb.Key):
            ret = cls._parse_data(d.get())
        elif isinstance(d, ndb.Model):
            ret = cls._parse_data(d.to_dict())
        elif isinstance(d, (datetime.datetime, datetime.date, datetime.time)):
            ret = cls._parse_data(str(d))
        elif isinstance(d, dict):
            ret = {}
            for k, v in d.iteritems():
                v = cls._parse_data(v)

                # remove _ at end
                new_key = k
                while len(new_key) and new_key[-1] == '_':
                    new_key = new_key[:-1]
                ret[new_key] = v

        elif isinstance(d, (list, tuple)):
            ret = []
            for v in iter(d):
                ret.append(cls._parse_data(v))

        return ret

    @ndb.utils.positional(1)
    def to_dict(self, include=None, exclude=None):
        if include is None and self.__dict_include__:
            include = self.__dict_include__
        if exclude is None and self.__dict_exclude__:
            exclude = self.__dict_exclude__

        ret = super(Model, self).to_dict(include=include, exclude=exclude)
        # insert key as urlsafe
        if (include and 'key' in include) or (exclude and 'key' not in exclude):
            ret['key'] = self.key.urlsafe()

        return self._parse_data(ret)

class UserPrefs(Model):
    __dict_include__ = ['userid', 'name', 'email', 'admin']

    object_version = ndb.IntegerProperty(default=1, required=True)
    added_at = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated_at = ndb.DateTimeProperty(auto_now=True, indexed=False)

    userid = ndb.ComputedProperty(lambda self: self.key.id())
    name = ndb.StringProperty(required=True, indexed=False)
    email = ndb.StringProperty(required=True, indexed=False)
    admin = ndb.BooleanProperty(required=True, indexed=True)
    authorized = ndb.BooleanProperty(indexed=True, required=True)

    @classmethod
    def get_current(cls):
        user = users.get_current_user()
        if user is None:
            # not logged
            return None
        userid = user.user_id()
        is_admin = users.is_current_user_admin()

        pref = cls.get_by_userid(userid)

        # always create a new pref
        if pref is None:
            pref = cls(id=userid, email=user.email(),
                       authorized=False, admin=False, name=user.nickname())

        # XXX: upgrade to admin account if is a cloud admin account
        if is_admin:
            pref.admin = True
            pref.authorized = True
        pref.put()
        return pref

    @classmethod
    def get_by_userid(cls, userid):
        return cls.query(cls.userid == userid).get()

class LogEntry(Model):
    user = ndb.KeyProperty(UserPrefs, required=True, indexed=True)
    when = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    action = ndb.StringProperty(indexed=False, required=True, choices=valid_actions)

    @classmethod
    def from_user(cls, user, is_new):
        return cls(user=user.key,
                   action="create" if is_new else "update")

class PatientCode(Model):
    pass

class Patient(Model):
    __dict_exclude__ = ['name_tags', 'code_tags', 'object_version', 'added_at',
                        'updated_at']

    object_version = ndb.IntegerProperty(default=1, required=True)
    added_at = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated_at = ndb.DateTimeProperty(auto_now=True, indexed=False)

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

class BloodBag(Model):
    type_ = ndb.StringProperty(indexed=False, required=True, choices=blood_types)
    content = ndb.StringProperty()

class TransfusionCode(Model):
    pass

class Transfusion(Model):
    __dict_exclude__ = ['object_version', 'added_at', 'updated_at']

    object_version = ndb.IntegerProperty(default=1, required=True)
    added_at = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated_at = ndb.DateTimeProperty(auto_now=True, indexed=False)

    patient = ndb.KeyProperty(Patient, required=True, indexed=True)
    code = ndb.StringProperty(indexed=True, required=True, validator=onlynumbers)
    date = ndb.DateProperty(indexed=True, required=True)

    local = ndb.StringProperty(indexed=False, required=True,
        choices=valid_locals)
    bags = ndb.LocalStructuredProperty(BloodBag, repeated=True)

    tags = ndb.StringProperty(repeated=True, indexed=False,
        choices=transfusion_tags)
    text = ndb.TextProperty(required=False)
    logs = ndb.StructuredProperty(LogEntry, repeated=True)

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
