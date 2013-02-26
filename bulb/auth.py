from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import permissions
from rest_framework import authentication
import requests
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

N4J = "http://localhost:7474/db/data/cypher"

def n4j2bulb(r, single=False):
    # JSON to Python dict
    j = r.json()

    if single:
        assert(len(j['data']) == 1)
    
    # Returned list
    output = []

    for datapoint in j['data']:
        # Returned dict
        d = {}
        for i, c in enumerate(j['columns']):
            d[c] = datapoint[i]
        output.append(d)

    if single:
        return output[0]
    else:
        return output

class N4JBackend(authentication.BaseAuthentication):
  """
  Authenticate user based on data from Neo4J
  """

  def authenticate(self, request):
    username = request.META.get('HTTP_X_USERNAME')
    password = request.META.get('HTTP_X_PASSWORD')

    if (username and password):
      query = "start user=node:users(username={username}) return user.pass as pass"
      params = {"username": username}
      headers = {'content-type': 'application/json'}

      r = n4j2bulb(requests.post(N4J, data=json.dumps({"query": query, "params": params}), headers = headers), True)
#
      if (r['pass'] == password):
        # User found and right password given
        user = User(username=username, password='')
        return (user, None)


   # User not found
    return None

# def authenticate(self, username=None, password=None):
#   if password:
#     sha1hash = hashlib.sha224(password).hexdigest()
#   
#
# def get_user(self, user_id):
#   query = "start user=node:users(id={id}) return user.username as username"
#   params = {"id": user_id}
#   headers = {'content-type': 'application/json'}
#
#   r = requests.post(N4J, data=json.dumps({"query": query, "params": params}), headers = headers)
#
#   if (len(r.json()['data']) != 0):
#     return User(username=n4j2bulb(r, True)['username'])
#
#   return None
