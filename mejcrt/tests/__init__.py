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
from copy import deepcopy
'''
Created on 08/12/2015

@author: Iuri Diniz <iuridiniz@gmail.com>
'''

import datetime
from itertools import count
import random
import string
import time
import unittest
from urllib import urlencode

from flask import json
from flask.helpers import url_for
from flask_testing.utils import TestCase
from google.appengine.ext import testbed, ndb
import names


def random_date(start=None, end=None):
    """Get a random date between two dates"""
    def date_to_timestamp(d) :
        return int(time.mktime(d.timetuple()))

    if start is None and end is None:
        end = datetime.datetime.now()
        start = end - datetime.timedelta(days=365)

    stime = date_to_timestamp(start)
    etime = date_to_timestamp(end)

    ptime = stime + random.random() * (etime - stime)

    return datetime.date.fromtimestamp(ptime)

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
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        # Clear ndb's in-context cache between tests.
        # This prevents data from leaking between tests.
        # Alternatively, you could disable caching by
        # using ndb.get_context().set_cache_policy(False)
        ndb.get_context().clear_cache()


    @classmethod
    def fixtureCreateSomeData(cls):
        from .. import models
        code = count(24400)

        def get_text(n=100):
            return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(n))

        # patients
        p = models.Patient()
        # name with accent
        p.name = u'John Heyder Oliveira de Medeiros Galv\xe3o'
        p.code = str(code.next())
        p.blood_type = random.choice(models.blood_types)
        p.type_ = random.choice(models.patient_types)
        p.put()

        for _ in range(5):
            p = models.Patient()
            p.name = names.get_full_name()
            p.code = str(code.next())
            p.blood_type = random.choice(models.blood_types)
            p.type_ = random.choice(models.patient_types)
            p.put()

        for _ in range(10):
            tr = models.Transfusion()
            tr.patient_key = p.key
            tr.code = str(code.next())
            tr.date = random_date()
            tr.local = random.choice(models.valid_locals)
            tr.text = get_text()
            tr.bags = []
            for _ in range(2):
                bag = models.BloodBag()
                bag.type_ = random.choice(models.blood_types)
                bag.content = random.choice(models.blood_contents)
                tr.bags.append(bag)
            tr.put()

    def login(self, email='user@example.com', id_='123', is_admin=False):
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
                     u'type': u'RN',
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
        p = Patient.get_by_code(self.patient_data['code'], False)
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
        data = rv.json
        self.assertEquals(key, data['key'])

    def testHistoryCreateGetUpdateGet(self):
        self.login()

        data = self.patient_data.copy()

        # create
        rv = self.client.post(url_for('patient.upinsert'),
                              data=json.dumps(data),
                              content_type='application/json')
        self.assert200(rv)
        key = rv.json['key']

        # get
        rv = self.client.get(url_for('patient.get', key=key))
        got_data = rv.json
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
        key = rv.json['key']
        self.assertEquals(data['key'], key)

        # get
        rv = self.client.get(url_for('patient.get', key=key))
        got_data = rv.json
        self.assert200(rv)
        data['key'] = key
        self.assertEquals(len(got_data['logs']), 2)
        self.assertEquals(got_data['logs'][0]['action'], 'create')
        self.assertEquals(got_data['logs'][1]['action'], 'update')
        del got_data['logs']
        self.assertEquals(data, got_data)

class TestTransfusion(TestBase):
    tr_data = {u'bags': [{u'content': u'CHPLI', u'type': u'O-'}],
                u'date': u'2015-05-22',
                u'local': u'uti-neonatal',
                u'patient_key': None,
                u'code': u'20900',
                u'tags': [u'rt'],
                u'text': u'some test'}

    def setUp(self):
        super(TestTransfusion, self).setUp()
        self.fixtureCreateSomeData()
        self.data = deepcopy(self.tr_data)
        from .. import models
        self.data['patient_key'] = models.Patient.query().get(keys_only=True).urlsafe()
#     def _fixtureCreatePatient(self, data=None):
#         if data is None:
#             data = TestPatient.patient_data.copy()
#
#         rv = self.client.post("/api/v1/patient", data=json.dumps(data),
#                          content_type='application/json')
#
#         return rv.json['key']

#     def _fixtureCreateUpdate(self, data=None, update=False):
#         if data is None:
#             data = self.data.copy()
#             data['patient_key'] = self._fixtureCreatePatient()
#
#         method = self.client.post
#         if update:
#             method = self.client.put
#         rv = method("/api/v1/transfusion",
#                   data=json.dumps(data),
#                   content_type='application/json')
#         return rv

    def testCreate(self):
        self.login()
        rv = self.client.post(url_for('transfusion.upinsert'), data=json.dumps(self.data),
                          content_type='application/json')
        self.assert200(rv)

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

        self.assertEquals(key.urlsafe(), rv.json['key'])

    def testGetNotLogged(self):
        rv = self.client.get(url_for('transfusion.get', key=123))
        self.assert401(rv)

    def testSearchPatientCode(self):
        from .. import models
        self.login()
        tr = models.Transfusion.query().get()

        query = dict(patient_code=tr.patient.code)
        rv = self.client.get(url_for('transfusion.search', **query))
        self.assert200(rv)
        self.assertIsNotNone(rv.json)
        data = rv.json
        self.assertIn(tr.key.urlsafe(), data['keys'])

    def testSearchPatientName(self):
        from .. import models
        self.login()
        tr = models.Transfusion.query().get()

        query = dict(patient_name=tr.patient.name)
        rv = self.client.get(url_for('transfusion.search', **query))
        self.assert200(rv)
        self.assertIsNotNone(rv.json)
        data = rv.json
        self.assertIn(tr.key.urlsafe(), data['keys'])

    def testSearchCode(self):
        from .. import models
        self.login()
        tr = models.Transfusion.query().get()

        query = dict(code=tr.code)
        rv = self.client.get(url_for('transfusion.search', **query))
        self.assert200(rv)
        self.assertIsNotNone(rv.json)
        data = rv.json
        self.assertIn(tr.key.urlsafe(), data['keys'])

    def testSearchNotLogged(self):
        rv = self.client.get(url_for('transfusion.search', q=123))
        self.assert401(rv)

    def testSearchNone(self):
        self.login()
        rv = self.client.get(url_for('transfusion.search', q=123))
        self.assert200(rv)
        data = rv.json
        self.assertEquals(data['keys'], [])

    def testHistoryCreateGetUpdateGet(self):
        self.login()
        data = self.data

        # create
        rv = self.client.post(url_for('transfusion.upinsert'), data=json.dumps(data),
                          content_type='application/json')
        self.assert200(rv)
        data['key'] = rv.json['key']

        # get
        rv = self.client.get(url_for('transfusion.get', key=rv.json['key']))
        self.assert200(rv)

        got_data = rv.json
        self.assertEquals(len(got_data['logs']), 1)
        self.assertEquals(got_data['logs'][0]['action'], 'create')
        del got_data['logs']
        self.assertDictEqual(got_data, data)

        # update
        data['tags'] = ['semrt']
        rv = self.client.post(url_for('transfusion.upinsert'), data=json.dumps(self.data),
                          content_type='application/json')

        self.assert200(rv)

        # get
        rv = self.client.get(url_for('transfusion.get', key=rv.json['key']))
        self.assert200(rv)

        got_data = rv.json
        self.assertEquals(len(got_data['logs']), 2)
        self.assertEquals(got_data['logs'][0]['action'], 'create')
        self.assertEquals(got_data['logs'][1]['action'], 'update')
        del got_data['logs']
        self.assertDictEqual(got_data, data)

    def testUpdateNotFound(self):
        self.login()
        data = self.data
        data['key'] = '123'
        rv = self.client.post(url_for('transfusion.upinsert'), data=json.dumps(self.data),
                          content_type='application/json')
        self.assert404(rv)

    def testGetLocals(self):
        self.login()
        rv = self.client.get(url_for('transfusion.locals'))
        self.assert200(rv)

        from .. import models
        self.assertListEqual(rv.json['locals'], models.valid_locals)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
