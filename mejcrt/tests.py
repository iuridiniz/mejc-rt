'''
Created on 08/12/2015

@author: Iuri Diniz <iuridiniz@gmail.com>
'''
import unittest

from google.appengine.ext import testbed, ndb

from flask import json
from flask.ext.testing import TestCase


class TestBase(TestCase):
    def setUp(self):
        super(TestCase, self).setUp()
        import controllers
        self.ctrl = controllers

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

    def create_app(self):
        from __init__ import app
        return app


class TestRoot(TestBase):
    def testRoot(self):
        rv = self.client.get("/")
        assert "MEJC RT" in rv.data

class TestTransfusion(TestBase):
    def setUp(self):
        super(TestBase, self).setUp()
        data = {u'blood_bags': [{u'content': u'CHPLI', u'type': u'O-'}],
                u'blood_type': u'O+',
                u'date': u'2015-05-22',
                u'local': u'uti-neonatal',
                u'name': u'John Heyder Oliveira de Medeiros Galv\xe3o',
                u'nhh_code': u'20900',
                u'kind': u'RN',
                u'record': u'12345/0',
                u'tags': [],
                u'text': u''}

        self.data = data

    def _fixtureCreate(self):
        rv = self.client.post("/api/transfusion",
                  data=json.dumps(self.data),
                  content_type='application/json')
        return rv

    def testCreate(self):
        rv = self._fixtureCreate()
        self.assert200(rv)



if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
