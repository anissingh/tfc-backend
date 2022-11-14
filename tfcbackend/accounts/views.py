from rest_framework.generics import CreateAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from accounts.serializers import UserSerializer


# Create your views here.
class CreateUserView(CreateAPIView):
    serializer_class = UserSerializer


class EditUserView(UpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

