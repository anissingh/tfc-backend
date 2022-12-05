from rest_framework.generics import ListAPIView
from studios.serializers import StudioSerializer, ClassInstanceSerializer
from studios.models import Studio, ClassInstance, Class
from django.shortcuts import get_object_or_404
from datetime import datetime
from studios.utils import get_curr_datetime
from studios.pagination_classes import ClassSchedulePagination, StudioPagination
from studios.calculator import get_nearby_locs_qs


class SearchStudioView(ListAPIView):
    serializer_class = StudioSerializer
    model = Studio
    pagination_class = StudioPagination

    def get_queryset(self):
        latitude = self.request.GET.get('lat', '')
        longitude = self.request.GET.get('long', '')

        if latitude == '' or longitude == '':
            return Studio.objects.none()

        try:
            f_lat = float(latitude)
            f_long = float(longitude)
        except ValueError:
            return Studio.objects.none()

        if not (-90.0 <= f_lat <= 90.0 and -180.0 <= f_long <= 180.0):
            return Studio.objects.none()

        # Note: Multiple searches treated as AND requirements not OR requirements
        names = list(self.request.GET.getlist('name'))
        amenities = list(self.request.GET.getlist('amenity'))
        class_names = list(self.request.GET.getlist('class-name'))
        coaches = list(self.request.GET.getlist('coach'))

        studios = Studio.objects.all()
        studio_names = Studio.objects.none()
        studio_amenities = Studio.objects.none()
        studio_class_names = Studio.objects.none()
        studio_coaches = Studio.objects.none()

        # Begin filtering
        if len(names) > 0:
            for name in names:
                studio_names |= studios.filter(name__iexact=name)
            studios = studio_names
        if len(amenities) > 0:
            for amenity in amenities:
                studio_amenities |= studios.filter(studioamenities__type__iexact=amenity)
            studios = studio_amenities
        if len(class_names) > 0:
            for class_name in class_names:
                studio_class_names |= studios.filter(class__name__iexact=class_name)
            studios = studio_class_names
        if len(coaches) > 0:
            classes_with_coach = ClassInstance.objects.none()
            for coach in coaches:
                classes_with_coach |= ClassInstance.objects.filter(coach__iexact=coach)
            classes = classes_with_coach.values_list('cls', flat=True).order_by('id')
            studio_coaches |= studios.filter(class__in=classes)
            studios = studio_coaches

        qs = get_nearby_locs_qs(f_lat, f_long, studios.distinct())
        return qs


class SearchStudioClassSchedule(ListAPIView):
    serializer_class = ClassInstanceSerializer
    model = ClassInstance
    pagination_class = ClassSchedulePagination

    def get_queryset(self):
        # Parse input
        studio = get_object_or_404(Studio, id=self.kwargs['studio_id'])
        class_names = list(self.request.GET.getlist('class-name'))
        coaches = list(self.request.GET.getlist('coach'))
        date_strs = list(self.request.GET.getlist('date'))
        dates = []
        for d in date_strs:
            try:
                dates.append(datetime.strptime(d, '%Y-%m-%d').date())
            except ValueError:
                pass
        start_time_str = self.request.GET.get('start-time', '')
        try:
            start_time = datetime.strptime(start_time_str, '%H-%M-%S').time()
        except ValueError:
            start_time = 'E'

        end_time_str = self.request.GET.get('end-time', '')
        try:
            end_time = datetime.strptime(end_time_str, '%H-%M-%S').time()
        except ValueError:
            end_time = 'E'

        # Search
        curr_date_and_time = get_curr_datetime()
        classes = list(Class.objects.filter(studio=studio))
        class_instances = ClassInstance.objects.filter(cls__in=classes)
        ci_class_names = ClassInstance.objects.none()
        ci_coaches = ClassInstance.objects.none()

        if len(class_names) > 0:
            for class_name in class_names:
                ci_class_names |= class_instances.filter(cls__name__iexact=class_name)
            class_instances = ci_class_names
        if len(coaches) > 0:
            for coach in coaches:
                ci_coaches |= class_instances.filter(coach__iexact=coach)
            class_instances = ci_coaches
        if len(dates) > 0:
            class_instances = class_instances.filter(date__in=dates)
        if start_time != 'E':
            class_instances = class_instances.filter(start_time__gte=start_time)
        if end_time != 'E':
            class_instances = class_instances.filter(end_time__lte=end_time)

        return class_instances.filter(cancelled=False, start_date_and_time__gte=curr_date_and_time).distinct().order_by('start_date_and_time')
