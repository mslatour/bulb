from rest_framework.views import APIView
from rest_framework.response import Response

class IdeaAPIView(APIView):
  
  def get(self, request, ideaId):
    return Response()
#    {"id":ideaId,"name":"Idea"+str(ideaId)})
