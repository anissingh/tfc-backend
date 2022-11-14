from django.urls import path
from studios.views import StudioInfoView, ClosestStudiosView, EnrollOneView, EnrollAllView, \
    DropOneView, DropAllView, StudioClassScheduleView, UserClassScheduleView, UserClassHistoryView
from studios.search_views import SearchStudioView, SearchStudioClassSchedule


app_name = 'studios'

urlpatterns = [
    path('<int:studio_id>/info/', StudioInfoView.as_view()),
    path('closest/', ClosestStudiosView.as_view()),
    path('<int:class_id>/enroll/one/', EnrollOneView.as_view()),
    path('<int:class_id>/enroll/', EnrollAllView.as_view()),
    path('<int:class_id>/drop/one/', DropOneView.as_view()),
    path('<int:class_id>/drop/', DropAllView.as_view()),
    path('<int:studio_id>/class-schedule/', StudioClassScheduleView.as_view()),
    path('users/<int:user_id>/class-schedule/', UserClassScheduleView.as_view()),
    path('users/<int:user_id>/class-history/', UserClassHistoryView.as_view()),
    path('search/', SearchStudioView.as_view()),
    path('<int:studio_id>/classes/search/', SearchStudioClassSchedule.as_view()),
]
