from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from lift_op.models import *
from rest_framework.response import Response

class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = '__all__'
        extra_kwargs = {
                'name': {'validators': [UniqueValidator(queryset=Building.objects.all(),message="Building already exists.")]}
            }
        read_only_fields = ['id']

class LiftSerializer(serializers.ModelSerializer):

    building = serializers.PrimaryKeyRelatedField(
        queryset=Building.objects.all()
    )
    class Meta:
        model = Lift
        fields = ['building'] 
        read_only_fields = ['id']          

class MaintenanceLiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lift
        fields = '__all__'