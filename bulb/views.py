from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import render
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


class IdeaAPIView(APIView):
  
  def get(self, request, ideaId=0, format=None):
    query = "start x=node({ideaId}) return ID(x) as id, x.title as title"
    params = {"ideaId": int(ideaId)}
    headers = {'content-type': 'application/json'}

    r = requests.post(N4J, data=json.dumps({"query": query, "params": params}), headers=headers)

    return Response(n4j2bulb(r))
#    {"id":ideaId,"name":"Idea"+str(ideaId)})

  def delete(self, request, ideaId=None, format=None):
    if ideaId:
      query = "start n=node({ideaId}) match n-[r]-() delete r delete n;"
      params = {"ideaId": int(ideaId)}

      headers = {'content-type': 'application/json'}

      r = requests.post(N4J, data=json.dumps({"query": query, "params": params}), headers = headers)

      return Response(r.json())

class IdeaCollectionAPIView(APIView):
  def get(self, request, format=None):
    query = "start x=node(*) where ID(x) <> 0 return ID(x) as id, x.title as title"
    headers = {'content-type': 'application/json'}

    r = requests.post(N4J, data=json.dumps({"query": query}), headers=headers)

    return Response(n4j2bulb(r))

  def post(self, request, format=None):
    query = "create (n {title: {title}}) return ID(n) as id, n.title as title;"
    params = {"title": request.DATA['title']}

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
