from rest_framework.generics import CreateAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from accounts.serializers import UserSerializer, UserIDSerializer
from accounts.models import User


# Create your views here.
class CreateUserView(CreateAPIView):
    serializer_class = UserSerializer


class EditUserView(UpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class GetUserView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email', '')
        if not User.objects.filter(email=email).exists():
            return Response({
                'status': 'user does not exist'
            }, status=400)

        user = User.objects.get(email=email)
        user_serializer = UserIDSerializer(user)

        return Response({
            'status': 'success',
            'user-info': user_serializer.data
        })
