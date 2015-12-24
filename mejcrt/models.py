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

from google.appengine.api import users, memcache
from google.appengine.api.datastore_errors import BadValueError
from google.appengine.ext import ndb

from .util import iconv, tokenize

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
    __dict_include__ = ['userid', 'name', 'email', 'admin', 'added_at']

    object_version = ndb.IntegerProperty(default=1, required=True)
    added_at = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated_at = ndb.DateTimeProperty(auto_now=True, indexed=False)

    userid = ndb.ComputedProperty(lambda self: self.key.id())
    name = ndb.StringProperty(required=True, indexed=False)
    email = ndb.StringProperty(required=True, indexed=False)
    admin = ndb.BooleanProperty(required=True, indexed=True)
    authorized = ndb.BooleanProperty(required=True, indexed=True)

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
            pref = cls(id=str(userid), email=user.email(),
                       authorized=False, admin=False, name=user.nickname())

        # XXX: upgrade to admin account if is a cloud admin account
        if is_admin:
            pref.admin = True
            pref.authorized = True
        pref.put()
        return pref

    @classmethod
    def get_by_userid(cls, *args):
        return cls.get_by_id(*args)

    @classmethod
    def build_query(cls, admin=None, authorized=None):
        filters = []
        if admin is not None:
            filters.append(cls.admin == admin)
        if authorized is not None:
            filters.append(cls.authorized == authorized)

        if filters:
            return cls.query(ndb.OR(*filters))

        return cls.query()

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

    COUNT_KEY = 'Patient.count'

    object_version = ndb.IntegerProperty(default=1, required=True)
    added_at = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated_at = ndb.DateTimeProperty(auto_now=True, indexed=False)

    name = ndb.StringProperty(indexed=True, required=True)
    code = ndb.ComputedProperty(lambda self: self.key.id())
    blood_type = ndb.StringProperty(indexed=True, required=True, choices=blood_types)
    type_ = ndb.StringProperty(indexed=True, required=True,
        choices=patient_types)
    logs = ndb.StructuredProperty(LogEntry, repeated=True)

    name_tags = ndb.ComputedProperty(lambda self: self._gen_tokens_for_name(self.name), repeated=True)
    code_tags = ndb.ComputedProperty(lambda self: self._gen_tokens_for_code(self.code), repeated=True)

    _cache = memcache.Client()

    def _gen_tokens_for_name(self, name):
        name = iconv(name.lower())
        tokens = tokenize(name, minimum=4, maximum=16)
        tokens.add(name)
        return list(tokens)

    def _gen_tokens_for_code(self, code):
        code = iconv(code.lower())
        tokens = tokenize(code, minimum=4, maximum=16)
        tokens.add(code)
        return list(tokens)

    def delete(self):
        self.key.delete()
        self._count_decr()

    def put(self, update=False, **ctx_options):
        @ndb.transactional
        def put():
            if self.get_by_code(self.code):
                if not update:
                    raise BadValueError("Code %r is duplicated" % self.code)
            elif update:
                raise BadValueError("Code %r does not exist" % self.code)
            return super(Patient, self).put(**ctx_options)
        key = put()
        if not update:
            self._count_incr()
        return key

    @classmethod
    def count(cls):
        c = cls._cache.get(cls.COUNT_KEY)
        if c is None:
            c = cls.query().count()
            cls._cache.set(key=cls.COUNT_KEY, value=c, time=3600)
        return c

    @classmethod
    def _count_incr(cls):
        # It does nothing if KEY doesn't exists
        cls._cache.incr(cls.COUNT_KEY)
        return cls.count()

    @classmethod
    def _count_decr(cls):
        # It does nothing if KEY doesn't exists
        cls._cache.decr(cls.COUNT_KEY)
        return cls.count()

    @classmethod
    def get_by_code(cls, *args, **kwargs):
        result = cls.get_by_id(*args, **kwargs)
        return result

    @property
    def transfusions(self):
        return Transfusion.build_query(patient_key=self.key).fetch(keys_only=True)

    @classmethod
    def build_query(cls, name=None, code=None, exact=False):
        filters = []
        if name is not None:
            if exact:
                filters.append(cls.name == iconv(name).strip().lower())
            else:
                filters.append(cls.name_tags == iconv(name).strip().lower())
        if code is not None:
            if exact:
                filters.append(cls.code == code)
            else:
                filters.append(cls.code_tags == code)

        if filters:
            return cls.query(ndb.OR(*filters))

        return cls.query()

class BloodBag(Model):
    type_ = ndb.StringProperty(indexed=False, required=True, choices=blood_types)
    content = ndb.StringProperty()

class Transfusion(Model):
    __dict_exclude__ = ['object_version', 'added_at', 'updated_at']

    object_version = ndb.IntegerProperty(default=1, required=True)
    added_at = ndb.DateTimeProperty(auto_now_add=True, indexed=False)
    updated_at = ndb.DateTimeProperty(auto_now=True, indexed=False)

    patient = ndb.KeyProperty(Patient, required=True, indexed=True)
    code = ndb.ComputedProperty(lambda self: self.key.id())
    date = ndb.DateProperty(indexed=True, required=True)

    local = ndb.StringProperty(indexed=False, required=True,
        choices=valid_locals)
    bags = ndb.LocalStructuredProperty(BloodBag, repeated=True)

    tags = ndb.StringProperty(repeated=True, indexed=True,
        choices=transfusion_tags)
    text = ndb.TextProperty(required=False)
    logs = ndb.StructuredProperty(LogEntry, repeated=True)

    _cache = memcache.Client()

    @classmethod
    def _get_cache_key(cls, tag):
        return "%s.tag.%s" % (cls.__class__.__name__, tag)

    def put(self, update=False, **ctx_options):
        @ndb.transactional(xg=True)
        def put():

            if self.patient.get() is None:
                raise BadValueError("Patient %r does not exist" % self.patient)

            old = self.get_by_code(self.code)
            old_tags = []
            if old:
                old_tags = list(self.tags)
                if not update:
                    raise BadValueError("Code %r is duplicated" % self.code)
            elif update:
                raise BadValueError("Code %r does not exist" % self.code)

            return super(Transfusion, self).put(**ctx_options), old_tags

        r, old_tags = put()
        self._update_count_tags(old_tags)

        if not update:
            tag = 'all'
            self._cache.incr(self._get_cache_key(tag))
            self.count(tag)

        return r

    @classmethod
    def get_by_code(cls, *args, **kwargs):
        result = cls.get_by_id(*args, **kwargs)
        return result

    @classmethod
    def count(cls, tag=None):
        if tag is None:
            tag = 'all'
            query = cls.query()
        elif tag in transfusion_tags:
            query = cls.query(cls.tags == tag)
        else:
            return None

        key = cls._get_cache_key(tag)
        c = cls._cache.get(key)
        if c is None:
            c = query.count()
            cls._cache.set(key=key, value=c, time=3600)
        return c

    def _update_count_tags(self, old_tags):
        old = set(list(old_tags))
        cur = set(list(self.tags))
        for tag in cur - old:
            # tag was added
            self._cache.incr(self._get_cache_key(tag))
            self.count(tag)
        for tag in old - cur:
            # tag was removed
            self._cache.decr(self._get_cache_key(tag))
            self.count(tag)

    @classmethod
    def build_query(cls, exact=False, code=None, patient_code=None, patient_name=None, patient_key=None):
        filters = []
        if patient_code is not None or patient_name is not None:
            keys = Patient.build_query(name=patient_name, code=patient_code, exact=exact).fetch(keys_only=True)
            filters.append(cls.patient.IN(keys))
        if patient_key:
            filters.append(cls.patient == patient_key)
        if code is not None:
            filters.append(cls.code == code)

        if filters:
            return cls.query(ndb.OR(*filters))

        return cls.query()

    def delete(self):
        tags = self.tags
        self.key.delete()
        for tag in tags + ['all']:
            self._cache.decr(self._get_cache_key(tag))
            self.count(tag)
