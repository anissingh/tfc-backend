from studios.serializers import StudioSerializer
from rest_framework.generics import RetrieveAPIView
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from studios.serializers import ClassInstanceSerializer
from django.shortcuts import get_object_or_404
from studios.models import Studio, Class, ClassInstance
from accounts.models import User
from studios.calculator import get_nearby_locs, convert_date_to_django_date
from django.utils.dateparse import parse_date
from django.utils.timezone import now, localtime, localdate, make_aware
import datetime
from studios.utils import get_curr_datetime


# Create your views here.
class StudioInfoView(RetrieveAPIView):
    serializer_class = StudioSerializer

    def get_object(self):
        return get_object_or_404(Studio, id=self.kwargs['studio_id'])


class ClosestStudiosView(APIView):
    # TODO: Paginate

    def post(self, request, *args, **kwargs):
        latitude = request.data.get('latitude', '')
        longitude = request.data.get('longitude', '')

        if latitude == '' or longitude == '':
            return Response({
                'status': 'error'
            })

        try:
            f_lat = float(latitude)
            f_long = float(longitude)
        except ValueError:
            return Response({
                'status': 'error'
            })

        if not (-90.0 <= f_lat <= 90.0 and -180.0 <= f_long <= 180.0):
            return Response({
                'status': 'error'
            })

        qs = get_nearby_locs(f_lat, f_long)

        serializer = StudioSerializer(qs, many=True)

        return Response({
            'status': 'success',
            'data': serializer.data
        })


class EnrollOneView(APIView):
    # TODO: Only allow this to happen if user has active subscription
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        cls = get_object_or_404(Class, id=self.kwargs['class_id'])
        date_str = request.data.get('date', '')
        email = request.data.get('email', '')

        # Make sure request is valid
        error = _validate_enroll_or_drop_one_request(cls=cls, email=email, date_str=date_str)
        if error:
            return Response({
                error[0]: error[1]
            })

        user = User.objects.get(email=email)
        date = parse_date(date_str)
        # If no class takes place on this day (class was cancelled, class not offered this day,
        # etc.)
        if not ClassInstance.objects.filter(cls=cls, date=date, cancelled=False).exists():
            return Response({
                'status': 'this class is not offered on this day'
            })

        class_instance = ClassInstance.objects.get(cls=cls, date=date, cancelled=False)

        # Make sure class has not started
        if class_instance.start_date_and_time < get_curr_datetime():
            return Response({
                'status': 'class has already begun'
            })

        # Make sure class is not full
        if class_instance.enrolled == class_instance.capacity:
            return Response({
                'status': 'class is full'
            })

        # Make sure user is not already enrolled in this class
        if class_instance in user.enrolled_classes.all():
            return Response({
                'status': 'user already enrolled in this class'
            })

        # If we make it here, we can enroll the user in the class
        class_instance.enrolled += 1
        class_instance.save()
        user.enrolled_classes.add(class_instance)

        return Response({
            'status': 'success'
        })


class EnrollAllView(APIView):
    # TODO: Only allow with active subscription
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        cls = get_object_or_404(Class, id=self.kwargs['class_id'])
        email = request.data.get('email', '')

        # Make sure request is valid
        error = _validate_enroll_or_drop_all_request(email=email)
        if error:
            return Response({
                error[0]: error[1]
            })

        user = User.objects.get(email=email)
        response_msg = 'success'
        curr_date_and_time = get_curr_datetime()
        cls_to_enroll = ClassInstance.objects.filter(cls=cls,
                                                     start_date_and_time__gte=curr_date_and_time)
        enrolled_in_one = False

        for cls in cls_to_enroll:
            # Make sure class is not full and user is not already enrolled in this class
            if cls.enrolled == cls.capacity or cls in user.enrolled_classes.all() or cls.cancelled:
                response_msg = 'enrolled in all non-cancelled classes with availability ' \
                               'that user was not already enrolled in'
                continue
            else:
                # If we make it here, we can enroll the user in the class
                cls.enrolled += 1
                cls.save()
                user.enrolled_classes.add(cls)
                enrolled_in_one = True

        if not enrolled_in_one:
            response_msg = 'all classes user not enrolled in are full'

        return Response({
            'status': response_msg
        })


class DropOneView(APIView):
    # TODO: Only allow user to do this if they have a subscription
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        cls = get_object_or_404(Class, id=self.kwargs['class_id'])
        date_str = request.data.get('date', '')
        email = request.data.get('email', '')

        # Make sure request is valid
        error = _validate_enroll_or_drop_one_request(cls=cls, email=email, date_str=date_str)
        if error:
            return Response({
                error[0]: error[1]
            })

        user = User.objects.get(email=email)
        date = parse_date(date_str)

        # If no class takes place on this day (class was cancelled, class not offered this day,
        # etc.), return an error code
        if not ClassInstance.objects.filter(cls=cls, date=date).exists():
            return Response({
                'status': 'this class is not offered on this day'
            })

        class_instance = ClassInstance.objects.get(cls=cls, date=date)

        # Make sure user is already enrolled in this class
        if class_instance not in user.enrolled_classes.all():
            return Response({
                'status': 'user not enrolled in this class'
            })

        # Make sure class has not started
        if class_instance.start_date_and_time < get_curr_datetime():
            return Response({
                'status': 'class has already begun'
            })

        # If we make it here, we can drop the user from this class
        class_instance.enrolled -= 1
        class_instance.save()
        user.enrolled_classes.remove(class_instance)

        if class_instance.cancelled:
            return Response({
                'status': 'successfully dropped cancelled class'
            })
        else:
            return Response({
                'status': 'success'
            })


class DropAllView(APIView):
    # TODO: Ony allow if user has active subscription
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        cls = get_object_or_404(Class, id=self.kwargs['class_id'])
        email = request.data.get('email', '')

        # Make sure request is valid
        error = _validate_enroll_or_drop_all_request(email=email)
        if error:
            return Response({
                error[0]: error[1]
            })

        user = User.objects.get(email=email)
        response_msg = 'success'
        curr_date = localdate()
        curr_time = localtime().time()
        curr_date_and_time = make_aware(datetime.datetime.combine(curr_date, curr_time))
        cls_to_drop = ClassInstance.objects.filter(cls=cls,
                                                   start_date_and_time__gte=curr_date_and_time)
        dropped_one = False

        for cls in cls_to_drop:
            # Make sure user is already enrolled in this class
            if cls not in user.enrolled_classes.all():
                response_msg = 'dropped all classes user was already enrolled in'
                continue
            else:
                # If we make it here, we can drop the user from the class
                cls.enrolled -= 1
                cls.save()
                user.enrolled_classes.remove(cls)
                dropped_one = True

        if not dropped_one:
            response_msg = 'user was not enrolled in any classes'

        return Response({
            'status': response_msg
        })


class StudioClassScheduleView(ListAPIView):
    serializer_class = ClassInstanceSerializer
    model = ClassInstance
    paginate_by = 100

    def get_queryset(self):
        studio = get_object_or_404(Studio, id=self.kwargs['studio_id'])
        classes = list(Class.objects.filter(studio=studio))
        curr_date_and_time = get_curr_datetime()
        class_instances = ClassInstance.objects.filter(cls__in=classes,
                                                       start_date_and_time__gte=curr_date_and_time,
                                                       cancelled=False)
        return class_instances.order_by('start_date_and_time')


class UserClassScheduleView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ClassInstanceSerializer
    model = ClassInstance
    paginate_by = 100

    def get_queryset(self):
        user = get_object_or_404(User, id=self.kwargs['user_id'])
        curr_dt = get_curr_datetime()
        class_instances = user.enrolled_classes.all().filter(start_date_and_time__gte=curr_dt)
        return class_instances.order_by('start_date_and_time')


class UserClassHistoryView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ClassInstanceSerializer
    model = ClassInstance
    paginate_by = 100

    def get_queryset(self):
        user = get_object_or_404(User, id=self.kwargs['user_id'])
        curr_dt = get_curr_datetime()
        class_instances = user.enrolled_classes.all().filter(start_date_and_time__lt=curr_dt)
        return class_instances.order_by('start_date_and_time')


def _validate_enroll_or_drop_one_request(cls, email, date_str):
    if not User.objects.filter(email=email).exists():
        return ('status', 'no user with this email exists')

    date = parse_date(date_str)
    if not date:
        return ('status', 'invalid date')

    if date < localdate():
        return ('status', 'date has passed')

    if cls.end_date < date:
        return ('status', 'date must be before class stops being offered')
    if date < cls.start_date:
        return ('status', 'date cannot be before class starts being offered')

    return None


def _validate_enroll_or_drop_all_request(email):
    if not User.objects.filter(email=email).exists():
        return ('status', 'no user with this email exists')
    return None
