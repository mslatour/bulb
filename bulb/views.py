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
    return Response({'username': request.user.username})
    #if request.user and request.user.is_authenticated():
    #    return Response({'logged_in': True})
    #else:
    #    return Response({'logged_in': False})

class IdeaAPIView(APIView):
    """
    API class for getting and deleting a particular idea
    """
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
            self.get_object(ideaId) # see if we have permission
            return Response(N4J.delete_idea(ideaId).bulb())

class IdeaCollectionAPIView(APIView):
    """
    API class for collection of ideas and creating new instances of ideas
    """
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
    """
    API class for getting and creating neighbours of ideas
    """
    def get(self, request, ideaId=None, format=None):
        if ideaId:
            query = "start n=node({ideaId}) match n-[:IS_RELATED_TO]-m return ID(m) as id, m.title as title;"
            params = {"ideaId": int(ideaId)}

            return Response(N4J._cypher(query, params).bulb())

    def post(self, request, ideaId=None, format=None):
        if ideaId:
            query = "start node1=node({ideaId}), node2=node({neighbourId}) create node1-[:IS_RELATED_TO]->node2;"
            params = {"ideaId": int(ideaId), "neighbourId": int(request.DATA['neighbour'])}

            return Response(N4J._cypher(query, params).bulb())

def interface(request):
    username = request.session.get('user')
    c = {'username': username}
    return render(request, 'index.html', c)

@api_view(['POST'])
def logout(request):
    request.session.flush()
    return Response({'logged_in': False})
