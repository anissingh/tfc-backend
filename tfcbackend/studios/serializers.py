from rest_framework import serializers
from studios.models import Studio, ClassInstance, Class, StudioImage, StudioAmenities


class StudioSerializer(serializers.ModelSerializer):

    class Meta:
        model = Studio
        fields = ['id', 'name', 'address', 'latitude', 'longitude', 'postal_code', 'phone']


class StudioImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = StudioImage
        fields = ['image']


class StudioAmenitiesSerializer(serializers.ModelSerializer):

    class Meta:
        model = StudioAmenities
        fields = ['type', 'quantity']


class ClassSerializer(serializers.ModelSerializer):

    class Meta:
        model = Class
        fields = ['id', 'name']


class ClassInstanceSerializer(serializers.ModelSerializer):

    cls = ClassSerializer()
    date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()

    class Meta:
        model = ClassInstance
        fields = ['id', 'cls', 'date', 'start_time', 'end_time', 'enrolled', 'capacity', 'coach',
                  'cancelled']
