from django.urls import path
from studios.views import StudioInfoView, ClosestStudioView, EnrollOneView, EnrollAllView, \
    DropOneView, DropAllView, StudioClassScheduleView, UserClassScheduleView, UserClassHistoryView, \
    GetClassKeywordsView, GetClassDescriptionView, GetClassStudioView
from studios.search_views import SearchStudioView, SearchStudioClassSchedule


app_name = 'studios'

urlpatterns = [
    path('<int:studio_id>/info/', StudioInfoView.as_view()),
    path('closest/', ClosestStudioView.as_view()),
    path('classes/<int:class_id>/enroll/one/', EnrollOneView.as_view()),
    path('classes/<int:class_id>/enroll/', EnrollAllView.as_view()),
    path('classes/<int:class_id>/drop/one/', DropOneView.as_view()),
    path('classes/<int:class_id>/drop/', DropAllView.as_view()),
    path('<int:studio_id>/schedule/', StudioClassScheduleView.as_view()),
    path('classes/user/schedule/<int:user_id>/', UserClassScheduleView.as_view()),
    path('classes/user/history/<int:user_id>/', UserClassHistoryView.as_view()),
    path('search/', SearchStudioView.as_view()),
    path('<int:studio_id>/classes/search/', SearchStudioClassSchedule.as_view()),
    path('classes/<int:cls_id>/keywords/', GetClassKeywordsView.as_view()),
    path('classes/<int:cls_id>/description/', GetClassDescriptionView.as_view()),
    path('classes/<int:cls_id>/studio/name/', GetClassDescriptionView.as_view()),
]
