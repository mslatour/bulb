from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework import permissions
from django.shortcuts import render
import auth
import requests, json

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

@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def loginStatus(request):
  if request.user and request.user.is_authenticated():
    return Response({'logged_in': True})
  else:
    return Response({'logged_in': False})

class IdeaAPIView(APIView):
  permission_classes = (permissions.IsAuthenticatedOrReadOnly, auth.IsOwnerOrReadOnly,)

  def get_object(self, ideaId):
    query = ("start x=node({ideaId}) "
            "match x<-[:OWNS]-user "
            "return ID(x) as id, x.title as title, user.username as owner")
    params = {"ideaId": int(ideaId)}
    headers = {'content-type': 'application/json'}

    r = requests.post(N4J, data=json.dumps({"query": query, "params": params}), headers=headers)

    obj = n4j2bulb(r)
    if not self.has_permission(self.request, obj):
        self.permission_denied(self.request)

    return obj

  def get(self, request, ideaId=0, format=None):
    return Response(self.get_object(ideaId))

  def delete(self, request, ideaId=None, format=None):
    if ideaId:
      idea = self.get_object(ideaId)
      query = "start n=node({ideaId}) match n-[r]-() delete r delete n;"
      params = {"ideaId": int(ideaId)}

      headers = {'content-type': 'application/json'}

      r = requests.post(N4J, data=json.dumps({"query": query, "params": params}), headers = headers)

      return Response(r.json())

class IdeaCollectionAPIView(APIView):
  permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

  def get(self, request, format=None):
    query = ("start ideaRoot=node:roots(root='idea') "
             "match ideaRoot-[:IDEA]->idea "
             "return ID(idea) as id, idea.title as title")#, user.username as owner")
    headers = {'content-type': 'application/json'}

    r = requests.post(N4J, data=json.dumps({"query": query}), headers=headers)

    return Response(n4j2bulb(r))

  def post(self, request, format=None):
    # create idea
    query = ("start ideaRoot=node:roots(root='idea'), "
            "user=node:users(username={username}) "
            "create (idea {title: {title}}) "
            "create ideaRoot-[:IDEA]->idea "
            "create user-[:OWNS]->idea "
            "return ID(idea) as id, idea.title as title;")

    if 'abstract' in request.DATA.keys():
      params = {"title": request.DATA['title'], "abstract": request.DATA['abstract'], "username": request.user.username}
    else:
      params = {"title": request.DATA['title'], "username": request.user.username}

    headers = {'content-type': 'application/json'}

    r = requests.post(N4J, data=json.dumps({"query": query, "params": params}), headers = headers)

    return Response(n4j2bulb(r, True)) # True because we need one single JSON object, not a list

class NeighbourAPIView(APIView):
  def get(self, request, ideaId=None, format=None):
    if ideaId:
      query = "start n=node({ideaId}) match n-[:IS_RELATED_TO]-m return ID(m) as id, m.title as title;"
      params = {"ideaId": int(ideaId)}

      headers = {'content-type': 'application/json'}

      r = requests.post(N4J, data=json.dumps({"query": query, "params": params}), headers = headers)

      return Response(n4j2bulb(r))

  def post(self, request, ideaId=None, format=None):
    if ideaId:
      query = "start node1=node({ideaId}), node2=node({neighbourId}) create node1-[:IS_RELATED_TO]->node2;"
      params = {"ideaId": int(ideaId), "neighbourId": int(request.DATA['neighbour'])}

      headers = {'content-type': 'application/json'}

      r = requests.post(N4J, data=json.dumps({"query": query, "params": params}), headers = headers)

      return Response(r.json())


def interface(request):
    return render(request, 'index.html')
