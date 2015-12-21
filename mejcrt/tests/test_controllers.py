from copy import deepcopy
import unittest

from flask import json
from flask.helpers import url_for
from flask_testing.utils import TestCase
from google.appengine.datastore import datastore_stub_util
from google.appengine.ext import testbed, ndb

from .fixtures import fixture_random

class TestBase(TestCase):
    def setUp(self):
        super(TestCase, self).setUp()
        from .. import controllers
        self.ctrl = controllers

        self.maxDiff = None

        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        policy = datastore_stub_util.PseudoRandomHRConsistencyPolicy(probability=1)
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub(consistency_policy=policy)
        self.testbed.init_memcache_stub()
        # Clear ndb's in-context cache between tests.
        # This prevents data from leaking between tests.
        # Alternatively, you could disable caching by
        # using ndb.get_context().set_cache_policy(False)
        ndb.get_context().clear_cache()

    @classmethod
    def fixtureCreateSomeData(cls):
        fixture_random()

    def login(self, is_admin=False, email=None, id_=None):
        if id_ is None or email is None:
            from .. import models
            u = models.UserPrefs.query().filter(models.UserPrefs.admin == is_admin).get()
            email = u.email
            id_ = u.userid

        self.testbed.setup_env(
            user_email=email,
            user_id=id_,
            user_is_admin='1' if is_admin else '0',
            overwrite=True)

    def tearDown(self):
        self.testbed.deactivate()

    def create_app(self):
        from ..app import app
        return app

class TestRoot(TestBase):
    def testRoot(self):
        rv = self.client.get("/")
        assert "MEJC RT" in rv.data

class TestPatient(TestBase):
    patient_data = {u'blood_type': u'O+',
                     u'name': u'John Heyder Oliveira de Medeiros Galv\xe3o',
                     u'type': u'Rec\xe9m-nascido',
                     u'code': u'123450', }

    def setUp(self):
        super(TestPatient, self).setUp()
        self.fixtureCreateSomeData()

    def testCreate(self):
        self.login()
        rv = self.client.post(url_for('patient.upinsert'),
                              data=json.dumps(self.patient_data),
                              content_type='application/json')
        self.assert200(rv)

        from ..models import Patient
        p = Patient.get_by_code(self.patient_data['code'])
        self.assertIsInstance(p, Patient)

    def testDuplicated(self):
        self.login()
        rv = self.client.post(url_for('patient.upinsert'),
                              data=json.dumps(self.patient_data),
                              content_type='application/json')
        self.assert200(rv)
        rv = self.client.post(url_for('patient.upinsert'),
                              data=json.dumps(self.patient_data),
                              content_type='application/json')
        self.assert400(rv)

    def testGet(self):
        self.login()
        from ..models import Patient
        key = Patient.query().get(keys_only=True).urlsafe()
        rv = self.client.get(url_for('patient.get', key=key))
        self.assert200(rv)
        data = rv.json['data']
        self.assertEquals(key, data['key'])

    def testStats(self):
        self.login()
        from ..models import Patient
        c = Patient.query().count()
        rv = self.client.get(url_for('patient.stats'))
        self.assert200(rv)
        data = rv.json['data']
        self.assertEquals(c, data['stats']['all'])

    def testHistoryCreateGetUpdateGet(self):
        self.login()

        data = self.patient_data.copy()

        # create
        rv = self.client.post(url_for('patient.upinsert'),
                              data=json.dumps(data),
                              content_type='application/json')
        self.assert200(rv)
        key = rv.json['data']['key']

        # get
        rv = self.client.get(url_for('patient.get', key=key))
        got_data = rv.json['data']
        self.assert200(rv)
        data['key'] = key
        self.assertEquals(len(got_data['logs']), 1)
        self.assertEquals(got_data['logs'][0]['action'], 'create')
        del got_data['logs']
        self.assertEquals(data, got_data)

        # update
        data['name'] = "Hello World"
        rv = self.client.post(url_for('patient.upinsert'),
                              data=json.dumps(data),
                              content_type='application/json')
        self.assert200(rv)
        key = rv.json['data']['key']
        self.assertEquals(data['key'], key)

        # get
        rv = self.client.get(url_for('patient.get', key=key))
        got_data = rv.json['data']
        self.assert200(rv)
        data['key'] = key
        self.assertEquals(len(got_data['logs']), 2)
        self.assertEquals(got_data['logs'][0]['action'], 'create')
        self.assertEquals(got_data['logs'][1]['action'], 'update')
        del got_data['logs']
        self.assertEquals(data, got_data)

    def testGetPatientTypes(self):
        self.login()
        rv = self.client.get(url_for('patient.types'))
        self.assert200(rv)

        from .. import models
        self.assertListEqual(rv.json['data']['types'], list(models.patient_types))

    def testSearchPatientName(self):
        from .. import models
        self.login()
        p = models.Patient.query().get()

        query = dict(query=p.name, fields="name")
        rv = self.client.get(url_for('patient.search', **query))
        self.assert200(rv)
        self.assertIsNotNone(rv.json)
        data = rv.json['data']
        self.assertEquals(len(data), 1)
        self.assertEquals(p.key.urlsafe(), data[0]['key'])

    def testSearchPatientCode(self):
        from .. import models
        self.login()
        p = models.Patient.query().get()

        query = dict(query=p.code, fields="code")
        rv = self.client.get(url_for('patient.search', **query))
        self.assert200(rv)
        self.assertIsNotNone(rv.json)
        data = rv.json['data']
        self.assertEquals(len(data), 1)
        self.assertEquals(p.key.urlsafe(), data[0]['key'])

class TestTransfusion(TestBase):
    tr_data = {u'bags': [{u'content': u'CHPLI', u'type': u'O-'}],
                u'date': u'2015-05-22',
                u'local': u'Sem registro',
                u'patient': None,
                u'code': u'20900',
                u'tags': [u'rt'],
                u'text': u'some test'}

    def setUp(self):
        super(TestTransfusion, self).setUp()
        self.fixtureCreateSomeData()
        self.data = deepcopy(self.tr_data)
        from .. import models
        self.data['patient'] = dict(
                key=models.Patient.query().get(keys_only=True).urlsafe())

    def testStats(self):
        self.login()
        from ..models import Transfusion
        c = Transfusion.query().count()
        rv = self.client.get(url_for('transfusion.stats'))
        self.assert200(rv)
        data = rv.json['data']
        self.assertEquals(c, data['stats']['all'])

    def testCreate(self):
        self.login()
        rv = self.client.post(url_for('transfusion.upinsert'), data=json.dumps(self.data),
                          content_type='application/json')
        self.assert200(rv)

    def testDuplicated(self):
        self.login()
        rv = self.client.post(url_for('transfusion.upinsert'),
                              data=json.dumps(self.data),
                              content_type='application/json')
        self.assert200(rv)
        rv = self.client.post(url_for('transfusion.upinsert'),
                              data=json.dumps(self.data),
                              content_type='application/json')
        self.assert400(rv)

    def testCreateEmpty(self):
        self.login()
        rv = self.client.post(url_for('transfusion.upinsert'))
        self.assert400(rv)

    def testCreateNotLogged(self):
        rv = self.client.post(url_for('transfusion.upinsert'), data=json.dumps(self.data),
                          content_type='application/json')
        self.assert401(rv)

    def testCreateInvalid(self):
        self.login()
        data = self.data.copy()
        data['bags'][0]['type'] = 'invalid'
        rv = self.client.post(url_for('transfusion.upinsert'), data=json.dumps(data),
                          content_type='application/json')
        self.assert400(rv)

    def testGet(self):
        from .. import models
        self.login()
        key = models.Transfusion.query().get(keys_only=True)
        rv = self.client.get(url_for('transfusion.get', key=key.urlsafe()))
        got_data = rv.json['data']
        self.assertEquals(len(got_data), 1)
        self.assertEquals(key.urlsafe(), got_data[0]['key'])

    def testGetLast10(self):
        self.login()
        query = dict(max=10)
        rv = self.client.get(url_for('transfusion.get', **query))
        self.assert200(rv)
        data = rv.json['data']
        self.assertLessEqual(len(data), query['max'])

    def testGetNotLogged(self):
        rv = self.client.get(url_for('transfusion.get', key=123))
        self.assert401(rv)

    def testSearchPatientCode(self):
        from .. import models
        self.login()
        tr = models.Transfusion.query().get()

        query = dict(patient_code=tr.patient.get().code)
        rv = self.client.get(url_for('transfusion.search', **query))
        self.assert200(rv)
        self.assertIsNotNone(rv.json)
        data = rv.json['data']
        self.assertIn(tr.key.urlsafe(), data['keys'])

    def testSearchPatientName(self):
        from .. import models
        self.login()
        tr = models.Transfusion.query().get()

        query = dict(patient_name=tr.patient.get().name)
        rv = self.client.get(url_for('transfusion.search', **query))
        self.assert200(rv)
        self.assertIsNotNone(rv.json)
        data = rv.json['data']
        self.assertIn(tr.key.urlsafe(), data['keys'])

    def testSearchCode(self):
        from .. import models
        self.login()
        tr = models.Transfusion.query().get()

        query = dict(code=tr.code)
        rv = self.client.get(url_for('transfusion.search', **query))
        self.assert200(rv)
        self.assertIsNotNone(rv.json)
        data = rv.json['data']
        self.assertIn(tr.key.urlsafe(), data['keys'])

    def testSearchNotLogged(self):
        rv = self.client.get(url_for('transfusion.search', q=123))
        self.assert401(rv)

    def testSearchNone(self):
        self.login()
        rv = self.client.get(url_for('transfusion.search', q=123))
        self.assert200(rv)
        data = rv.json['data']
        self.assertEquals(data['keys'], [])

    def testHistoryCreateGetUpdateGet(self):
        self.login()
        data = self.data

        # create
        rv = self.client.post(url_for('transfusion.upinsert'), data=json.dumps(data),
                          content_type='application/json')
        self.assert200(rv)

        # get
        data[u'key'] = rv.json['data']['key']

        rv = self.client.get(url_for('transfusion.get', key=data['key']))
        self.assert200(rv)

        got_data = rv.json['data'][0]
        self.assertEquals(len(got_data['logs']), 1)
        self.assertEquals(got_data['logs'][0]['action'], 'create')
        del got_data['logs']

        self.assertEquals(got_data['patient']['key'], data['patient']['key'])
        del got_data['patient']
        data_without_patient = data.copy()
        del data_without_patient['patient']
        self.assertDictEqual(got_data, data_without_patient)

        # update
        data['tags'] = ['semrt']
        rv = self.client.put(url_for('transfusion.upinsert'), data=json.dumps(self.data),
                          content_type='application/json')
        self.assert200(rv)

        # get
        rv = self.client.get(url_for('transfusion.get', key=rv.json['data']['key']))
        self.assert200(rv)

        got_data = rv.json['data'][0]
        self.assertEquals(len(got_data['logs']), 2)
        self.assertEquals(got_data['logs'][0]['action'], 'create')
        self.assertEquals(got_data['logs'][1]['action'], 'update')
        del got_data['logs']

        self.assertEquals(got_data['patient']['key'], data['patient']['key'])
        del got_data['patient']
        data_without_patient = data.copy()
        del data_without_patient['patient']
        self.assertDictEqual(got_data, data_without_patient)

    def testUpdateNotFound(self):
        self.login()
        data = self.data
        data['key'] = '123'
        rv = self.client.put(url_for('transfusion.upinsert'), data=json.dumps(self.data),
                          content_type='application/json')
        self.assert404(rv)

    def testGetLocals(self):
        self.login()
        rv = self.client.get(url_for('transfusion.locals'))
        self.assert200(rv)

        from .. import models
        self.assertListEqual(rv.json['data']['locals'], list(models.valid_locals))

    def testGetBloodTypes(self):
        self.login()
        rv = self.client.get(url_for('transfusion.blood.types'))
        from .. import models
        self.assertListEqual(rv.json['data']['types'], list(models.blood_types))

    def testGetBloodContents(self):
        self.login()
        rv = self.client.get(url_for('transfusion.blood.contents'))
        from .. import models
        self.assertListEqual(rv.json['data']['contents'], list(models.blood_contents))

class TestUser(TestBase):
    def testGetMeLogged(self):
        self.fixtureCreateSomeData()

        from .. import models
        u = models.UserPrefs.query(models.UserPrefs.admin == False).get()
        self.login(email=u.email, id_=u.userid)

        rv = self.client.get(url_for('user.get', who='me'))
        self.assert200(rv)
        data = rv.json['data']
        self.assertEquals(data['user'], u.to_dict())

    def testGetMeNotLogged(self):
        self.fixtureCreateSomeData()

        rv = self.client.get(url_for('user.get', who='me'))
        self.assert401(rv)

#     def testLoginGoogle(self):
#         self.fixtureCreateSomeData()
#         rv = self.client.get(url_for('user.login.google', **{'continue': 'http://localhost:8080/'}))
#         self.assert200(rv)
#         self.assertIsNotNone(rv.json.get('url'))
#
#     def testLogoutGoogle(self):
#         self.fixtureCreateSomeData()
#
#         rv = self.client.get(url_for('user.logout.google', **{'continue': 'http://localhost:8080/'}))
#         self.assert200(rv)
#         self.assertIsNotNone(rv.json.get('url'))

    def testUpdateUserNotLoggedAsAdmin(self):
        self.fixtureCreateSomeData()

        from .. import models
        u1, u2 = models.UserPrefs.query(models.UserPrefs.admin == False).fetch(2)
        self.login(email=u1.email, id_=u1.userid)

        user_data = {'id': u2.userid, 'authorized':False}

        rv = self.client.put(url_for('user.update'), data=json.dumps(user_data),
                          content_type='application/json')
        self.assert403(rv)

    def testUpdateUserLoggedAsAdmin(self):
        self.fixtureCreateSomeData()

        from .. import models
        u1, u2 = models.UserPrefs.query(models.UserPrefs.admin == False).fetch(2)
        self.login(email=u1.email, id_=u1.userid, is_admin=True)

        user_data = {'id': u2.userid,
                     'authorized':False,
                     'email': u2.email,
                     'name': u2.name}

        rv = self.client.put(url_for('user.update'), data=json.dumps(user_data),
                          content_type='application/json')
        self.assert200(rv)

    def testUpdateUserLoggedAsHimself(self):
        self.fixtureCreateSomeData()

        from .. import models
        u = models.UserPrefs.query(models.UserPrefs.admin == False).get()
        self.login(email=u.email, id_=u.userid)

        user_data = {'id': u.userid,
                     'email': u.email + "123",
                     'name': u.name + 'as'}

        rv = self.client.put(url_for('user.update'), data=json.dumps(user_data),
                          content_type='application/json')
        self.assert200(rv)

    def testUpdateUserLoggedAsHimselfInvalidFields(self):
        self.fixtureCreateSomeData()

        from .. import models
        u = models.UserPrefs.query(models.UserPrefs.admin == False).get()
        self.login(email=u.email, id_=u.userid)

        user_data = {'id': u.userid,
                     'email': u.email,
                     'name': u.name,
                     'authorized': True}

        rv = self.client.put(url_for('user.update'), data=json.dumps(user_data),
                          content_type='application/json')
        self.assert403(rv)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
