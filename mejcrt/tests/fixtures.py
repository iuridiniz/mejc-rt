import datetime
from itertools import count
import random
import string
import time

import names

from .. import models

__all__ = ['fixture_random']

ORDINARY_USERID = "42"
ADMIN_USERID = "666"

def date_to_timestamp(d) :
    return int(time.mktime(d.timetuple()))

def random_text(n=100):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(n))

def random_date(start=None, end=None):
    """Get a random date between two dates"""

    if start is None and end is None:
        end = datetime.datetime.now()
        start = end - datetime.timedelta(days=365)

    stime = date_to_timestamp(start)
    etime = date_to_timestamp(end)

    ptime = stime + random.random() * (etime - stime)

    return datetime.date.fromtimestamp(ptime)

def fixture_random():
    code = count(24400)

    # patients
    p = models.Patient(id=str(code.next()))
    # name with accent
    p.name = u'John Heyder Oliveira de Medeiros Galv\xe3o'
    p.blood_type = random.choice(models.blood_types)
    p.type_ = random.choice(models.patient_types)
    p.put()

    keys = [p.key]
    for _ in range(5):
        p = models.Patient(id=str(code.next()))
        p.name = names.get_full_name()
        p.blood_type = random.choice(models.blood_types)
        p.type_ = random.choice(models.patient_types)
        p.put()
        keys.append(p.key)

    # transfusions
    for _ in range(40):
        tr = models.Transfusion(id=str(code.next()))
        tr.patient = random.choice(keys)
        tr.date = random_date()
        tr.local = random.choice(models.valid_locals)
        tr.text = random_text()
        tr.bags = []
        for _ in range(2):
            bag = models.BloodBag()
            bag.type_ = random.choice(models.blood_types)
            bag.content = random.choice(models.blood_contents)
            tr.bags.append(bag)
        if random.choice((True, False)):
            tr.tags = ['naovisitado']
        else:
            if random.choice((True, False)):
                tr.tags.append('rt')
            else:
                tr.tags.append('semrt')

        tr.put()

    # users
    # admin user
    u = models.UserPrefs(id=ADMIN_USERID, name='admin',
                         email="admin@admin.com", admin=True, authorized=True)
    u.put()

    # ordinary user1
    u = models.UserPrefs(id=ORDINARY_USERID, name="user",
                         email="user1@user1.com", admin=False, authorized=True)
    u.put()

    # ordinary user1
    u = models.UserPrefs(id=ORDINARY_USERID * 2, name="user2",
                         email="user2@user2.com", admin=False, authorized=True)
    u.put()

