'''
Created on 10/12/2015

@author: Iuri Diniz <iuridiniz@gmail.com>
'''

from flask.helpers import make_response

from ..app import app


@app.route("/")
def hello():
    return make_response("MEJC RT", 200, {})