from rest_framework import serializers
from accounts.models import User


class UserSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = super().create(validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        for attribute, value in validated_data.items():
            if attribute == 'password':
                instance.set_password(value)
            else:
                setattr(instance, attribute, value)
        instance.save()
        return instance

    class Meta:
        model = User
        fields = ['email', 'phone', 'password', 'avatar', 'first_name', 'last_name']
        extra_kwargs = {
            'password': {'write_only': True}
        }
