from rest_framework.views import APIView
from rest_framework.response import Response
import requests, json

N4J = "http://localhost:7474/db/data/cypher"

class IdeaAPIView(APIView):
  
  def get(self, request, ideaId=0, format=None):
    query = "start x=node({ideaId}) return x"
    params = {"ideaId": int(ideaId)}
    headers = {'content-type': 'application/json'}

    r = requests.post(N4J, data=json.dumps({"query": query, "params": params}), headers=headers)

    return Response(r.json())
#    {"id":ideaId,"name":"Idea"+str(ideaId)})

  def delete(self, request, ideaId=None, format=None):
    if ideaId:
      query = "start n=node({ideaId}) delete n;"
      params = {"ideaId": int(ideaId)}

      headers = {'content-type': 'application/json'}

      r = requests.post(N4J, data=json.dumps({"query": query, "params": params}), headers = headers)

      return Response(r.json())

class IdeaCollectionAPIView(APIView):
  def post(self, request, format=None):
    query = "create (n {title: {title}}) return ID(n);"
    params = {"title": request.DATA['title']}

    headers = {'content-type': 'application/json'}

    r = requests.post(N4J, data=json.dumps({"query": query, "params": params}), headers = headers)

    return Response(r.json())

class NeighbourAPIView(APIView):
  def get(self, request, ideaId=None, format=None):
    if ideaId:
      query = "start n=node({ideaId}) match n-[:IS_RELATED_TO]-m return m;"
      params = {"ideaId": int(ideaId)}

      headers = {'content-type': 'application/json'}

      r = requests.post(N4J, data=json.dumps({"query": query, "params": params}), headers = headers)

      return Response(r.json())

  def post(self, request, ideaId=None, format=None):
    if ideaId:
      query = "start node1=node({ideaId}), node2=node({neighbourId}) create node1-[:IS_RELATED_TO]->node2;"
      params = {"ideaId": int(ideaId), "neighbourId": request.DATA['neighbour']}

      headers = {'content-type': 'application/json'}

      r = requests.post(N4J, data=json.dumps({"query": query, "params": params}), headers = headers)

      return Response(r.json())

