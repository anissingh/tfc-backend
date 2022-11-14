from rest_framework.generics import ListAPIView
from studios.serializers import StudioSerializer, ClassInstanceSerializer
from studios.models import Studio, ClassInstance, Class
from django.shortcuts import get_object_or_404
from datetime import datetime


class SearchStudioView(ListAPIView):
    serializer_class = StudioSerializer
    model = Studio
    paginate_by = 100

    def get_queryset(self):
        # Note: Multiple searches treated as AND requirements not OR requirements
        names = list(self.request.GET.getlist('name'))
        amenities = list(self.request.GET.getlist('amenity'))
        class_names = list(self.request.GET.getlist('class-name'))
        coaches = list(self.request.GET.getlist('coach'))

        # First get all studios
        studios = Studio.objects.all()

        # Then begin filtering
        # TODO: Ignore case-sensitivity?
        if len(names) > 0:
            studios = studios.filter(name__in=names)
        if len(amenities) > 0:
            studios = studios.filter(studioamenities__type__in=amenities)
        if len(class_names) > 0:
            # TODO: What if all classes cancelled? Or class has passed?
            studios = studios.filter(class__name__in=class_names)
        if len(coaches) > 0:
            # TODO: What if all classes cancelled? Or class has passed?
            classes_with_coach = ClassInstance.objects.filter(coach__in=coaches)
            classes = classes_with_coach.values_list('cls', flat=True).order_by('id')
            studios = studios.filter(class__in=classes)

        return studios


class SearchStudioClassSchedule(ListAPIView):
    serializer_class = ClassInstanceSerializer
    model = ClassInstance
    paginate_by = 100

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
        # TODO: Ignore case-sensitivity?
        # Get all class instances in this studio
        classes = list(Class.objects.filter(studio=studio))
        class_instances = ClassInstance.objects.filter(cls__in=classes)

        if len(class_names) > 0:
            class_instances = class_instances.filter(cls__name__in=class_names)
        if len(coaches) > 0:
            class_instances = class_instances.filter(coach__in=coaches)
        if len(dates) > 0:
            class_instances = class_instances.filter(date__in=dates)
        if start_time != 'E':
            class_instances = class_instances.filter(start_time__gte=start_time)
        if end_time != 'E':
            class_instances = class_instances.filter(end_time__lte=end_time)

        return class_instances
