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

    def validate(self, data):
        errors = {}
        required_fields_extra = ['phone']
        if not self.partial:
            for field in required_fields_extra:
                if field not in data:
                    errors[field] = 'This field is required.'

        if 'phone' in data:
            phone = data['phone']
            if not phone.isnumeric() or len(phone) != 10:
                errors['phone'] = 'Invalid phone number.'

        if errors:
            raise serializers.ValidationError(errors)
        return data

    class Meta:
        model = User
        fields = ['email', 'phone', 'password', 'avatar', 'first_name', 'last_name']
        extra_kwargs = {
            'password': {'write_only': True}
        }
