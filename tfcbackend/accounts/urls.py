from django.urls import path
from accounts.views import CreateUserView, EditUserView, GetUserView
from rest_framework_simplejwt.views import TokenObtainPairView

app_name = 'accounts'

urlpatterns = [
    path('register/', CreateUserView.as_view()),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('edit/', EditUserView.as_view()),
    path('view/', GetUserView.as_view()),
]
