from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import permissions
from rest_framework import authentication
from rest_framework import exceptions
import requests
import hashlib
import json
import logging
import base64
from django.utils.encoding import smart_unicode, DjangoUnicodeDecodeError

logger = logging.getLogger(__name__)

N4J = "http://localhost:7474/db/data/cypher"

def n4j2bulb(r, single=False):
  # JSON to Python dict
  j = r.json()

# How should this work exactly?
# -------------------------
# It breaks, returns:
# AssertionError at /idea/
# No exception supplied
# -------------------------
#  if single:
#   assert(len(j['data']) == 1)
  
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

class N4JBackend(authentication.BasicAuthentication):
  """
  HTTP Basic authentication against user based on data from Neo4J
  """

  def authenticate(self, request):
    """
    Returns a `User` if a correct username and password have been supplied
    using HTTP Basic authentication.  Otherwise returns `None`.
    """
    auth = request.META.get('HTTP_AUTHORIZATION', '').split()

    if not auth or auth[0].lower() != "n4jbasic":
        return None

    if len(auth) != 2:
        raise exceptions.AuthenticationFailed('Invalid N4JBasic header')

    try:
        auth_parts = base64.b64decode(auth[1]).partition(':')
    except TypeError:
        raise exceptions.AuthenticationFailed('Invalid N4JBasic header')

    try:
        userid = smart_unicode(auth_parts[0])
        password = smart_unicode(auth_parts[2])
    except DjangoUnicodeDecodeError:
        raise exceptions.AuthenticationFailed('Invalid N4JBasic header')

    return self.authenticate_credentials(userid, password)

  def authenticate_credentials(self, userid, password):
    shaHTTP = hashlib.sha224(password).hexdigest()
    
    query = "start user=node:users(username={username}) return user.password as password"
    params = {"username": userid}
    headers = {'content-type': 'application/json'}

    r = n4j2bulb(requests.post(N4J, data=json.dumps({"query": query, "params": params}), headers = headers), True)

    if (r['password'] == shaHTTP):
      # User found and right password given
      user = User(username=userid, password='')
      return (user, None)

     # User not found
    raise exceptions.AuthenticationFailed('Invalid username/password')

  def authenticate_header(self, request):
      return 'N4JBasic realm="%s"' % self.www_authenticate_realm

class IsOwnerOrReadOnly(permissions.BasePermission):
  
  def has_permission(self, request, view, obj=None):
    if request.method in permissions.SAFE_METHODS:
      return True

    if obj:
      return obj[0]['owner'] == request.user.username
    else:
      return True
