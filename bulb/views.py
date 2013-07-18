from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework import permissions
from django.shortcuts import render
from lib import neo4j
import auth
import requests, json

N4J = neo4j.N4J("http://localhost:7474")

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
        # get idea from Neo4J
        obj = N4J.get_idea(ideaId).bulb()

        # if we are not allowed to manipulate this object with this request type
        # deny
        if not self.has_permission(self.request, obj):
            self.permission_denied(self.request)

        return obj

    def get(self, request, ideaId=0, format=None):
        return Response(self.get_object(ideaId))

    def delete(self, request, ideaId=None, format=None):
        if ideaId:
            get_object(ideaId) # see if we have permission
            return N4J.delete_idea(ideaId).bulb()

class IdeaGraphAPIView(APIView):
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get(self, request, format=None):
        ideas = N4J.get_all_ideas().bulb()
        connections = N4J.get_all_connections().bulb()
        return Response({"nodes":ideas, "links":connections})

    def post(self, request, format=None):
        # create idea
        title = request.DATA['title']
        properties = request.DATA
        del(properties['title'])

        return Response(N4J.add_idea(request.user.username, title, properties).bulb())

class IdeaCollectionAPIView(APIView):
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get(self, request, format=None):
        return Response(N4J.get_all_ideas().bulb())

    def post(self, request, format=None):
        # create idea
        title = request.DATA['title']
        properties = request.DATA
        del(properties['title'])

        return Response(N4J.add_idea(request.user.username, title, properties).bulb())

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

def network(request):
    return render(request, 'network.html')

def interface(request):
    return render(request, 'index.html')
