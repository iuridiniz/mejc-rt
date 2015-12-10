'''
Created on 08/12/2015

@author: Iuri Diniz <iuridiniz@gmail.com>
'''
from google.appengine.api.datastore_errors import BadValueError
from google.appengine.ext import ndb

from utils import onlynumbers, iconv, tokenize

# Models
blood_types = ('A+', 'B+', 'AB+', "O+", 'A-', 'B-', 'AB-', "O-")
patient_types = ("RN", "G", "O")
valid_locals = ["unidade-a", "unidade-b", 'unidade-b4', 'alto-risco',
        'uti-neonatal', 'uti-materna', 'sem-registro']
transfusion_tags = ['rt', "ficha-preenchida", "carimbo-plantao",
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

class PatientRecord(ndb.Model):
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
        if not key:
            # pr = PatientRecord(id=self.code)
            self.key = ndb.Key(PatientRecord, self.code, Patient, None)
            return super(Patient, self).put(**ctx_options)

        raise BadValueError("Patient.code %r is duplicated" % self.code)

    @classmethod
    def get_by_code(cls, code, onlykey=False):
        result = Patient.query(ancestor=ndb.Key(PatientRecord, code)).get(keys_only=onlykey)
        return result

class BloodBag(ndb.Model):
    type_ = ndb.StringProperty(indexed=False, required=True, choices=blood_types)
    content = ndb.StringProperty()

class Transfusion(ndb.Model):
    object_version = ndb.IntegerProperty(default=1, required=True)

    patient_key = ndb.KeyProperty(Patient, required=True, indexed=True)
    nhh_code = ndb.StringProperty(indexed=True, required=True, validator=onlynumbers)
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
        return Patient.get_by_id(self.patient_key)

