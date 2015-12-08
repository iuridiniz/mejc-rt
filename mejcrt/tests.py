'''
Created on 08/12/2015

@author: Iuri Diniz <iuridiniz@gmail.com>
'''
import unittest
from urllib import urlencode

from google.appengine.ext import testbed, ndb

from flask import json
from flask_testing import TestCase

class TestBase(TestCase):
    def setUp(self):
        super(TestCase, self).setUp()
        import controllers
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

    def login(self, email='user@example.com', id='123', is_admin=False):
        self.testbed.setup_env(
            user_email=email,
            user_id=id,
            user_is_admin='1' if is_admin else '0',
            overwrite=True)

    def tearDown(self):
        self.testbed.deactivate()

    def create_app(self):
        from __init__ import app
        return app

class TestRoot(TestBase):
    def testRoot(self):
        rv = self.client.get("/")
        assert "MEJC RT" in rv.data

class TestTransfusion(TestBase):
    def setUp(self):
        super(TestTransfusion, self).setUp()
        data = {u'bags': [{u'content': u'CHPLI', u'type': u'O-'}],
                u'blood_type': u'O+',
                u'date': u'2015-05-22',
                u'local': u'uti-neonatal',
                u'name': u'John Heyder Oliveira de Medeiros Galv\xe3o',
                u'nhh_code': u'20900',
                u'kind': u'RN',
                u'record': u'123450',
                u'tags': [u'rt'],
                u'text': u'some test'}

        self.data = data

    def _fixtureCreateUpdate(self, data=None, update=False):
        if data is None:
            data = self.data

        method = self.client.post
        if update:
            method = self.client.put
        rv = method("/api/transfusion",
                  data=json.dumps(data),
                  content_type='application/json')
        return rv

    def testCreate(self):
        self.login()
        rv = self._fixtureCreateUpdate()
        self.assert200(rv)

    def testCreateEmpty(self):
        self.login()
        rv = self.client.post('/api/transfusion')
        self.assert400(rv)

    def testCreateNotLogged(self):
        rv = self._fixtureCreateUpdate()
        self.assert401(rv)

    def testCreateInvalid(self):
        self.login()
        data = self.data.copy()
        data['kind'] = 'invalid'
        rv = self._fixtureCreateUpdate(data)
        self.assert400(rv)

    def testGet(self):
        self.login()
        rv = self._fixtureCreateUpdate()
        key = rv.json['key']

        rv = self.client.get("/api/transfusion/%s" % key)

        self.assertEquals(key, rv.json['key'])
        data = rv.json
        del data['key']
        del data['logs']
        self.assertEquals(self.data, data)

    def testGetNotLogged(self):
        rv = self.client.get("/api/transfusion/%s" % 123)
        self.assert401(rv)

    def testSearchAny(self):
        self.login()
        key = self._fixtureCreateUpdate().json['key']

        query = dict(q=self.data['name'][0:4])
        rv = self.client.get('/api/transfusion/search?%s' % urlencode(query))
        data = rv.json
        self.assertEquals(data['keys'], [key])

    def testSearchName(self):
        self.login()
        from utils import iconv
        key = self._fixtureCreateUpdate().json['key']

        query = dict(name=iconv(self.data['name']))
        rv = self.client.get('/api/transfusion/search?%s' % urlencode(query))
        data = rv.json
        self.assertEquals(data['keys'], [key])

    def testSearchNhhcode(self):
        self.login()
        key = self._fixtureCreateUpdate().json['key']

        query = dict(nhh_code=self.data['nhh_code'])
        rv = self.client.get('/api/transfusion/search?%s' % urlencode(query))
        data = rv.json
        self.assertEquals(data['keys'], [key])

    def testSearchNotLogged(self):
        rv = self.client.get("/api/transfusion/search?%s" % 123)
        self.assert401(rv)

    def testSearchNone(self):
        self.login()
        rv = self.client.get("/api/transfusion/search?%s" % 123)
        self.assert200(rv)
        data = rv.json
        self.assertEquals(data['keys'], [])

    def testUpdate(self):
        self.login()
        # create one
        rv = self._fixtureCreateUpdate()
        key = rv.json['key']

        # alter the same key
        data = self.data
        data['key'] = key
        data['name'] = 'Iuri Gomes Diniz'
        rv = self._fixtureCreateUpdate(data, update=True)
        # must be 200 OK
        rv = self.assert200(rv)
        # check data
        rv = self.client.get("/api/transfusion/%s" % key)
        del rv.json['logs']
        self.assertEquals(data, rv.json)

    def testUpdateNotFound(self):
        self.login()
        # create one
        rv = self._fixtureCreateUpdate()
        key = rv.json['key']

        # alter invalid key
        data = self.data
        data['key'] = key + "NOTVALID"
        rv = self._fixtureCreateUpdate(data, update=True)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
