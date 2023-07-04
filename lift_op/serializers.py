from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from lift_op.models import *
from rest_framework.response import Response

class BuildingSerializer(serializers.ModelSerializer):
    '''
    Serializer to create building object.
    '''
    class Meta:
        model = Building
        fields = '__all__'
        extra_kwargs = {
                'name': {'validators': [UniqueValidator(queryset=Building.objects.all(),message="Building already exists.")]}
            }
        read_only_fields = ['id']

class LiftSerializer(serializers.ModelSerializer):
    '''
    Serializer to initialize Lift objects.
    '''
    building = serializers.PrimaryKeyRelatedField(
        queryset=Building.objects.all()
    )
    class Meta:
        model = Lift
        fields = ['building'] 
        read_only_fields = ['id']          

class MaintenanceLiftSerializer(serializers.ModelSerializer):
    '''
    Serializer to update maintenance status of lifts.
    '''
    class Meta:
        model = Lift
        fields = '__all__'