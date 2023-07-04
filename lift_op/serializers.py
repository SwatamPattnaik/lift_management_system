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
    # current_floor = serializers.IntegerField(default=0, initial=0)
    # destination = serializers.IntegerField(default=0, initial=0)
    # status = serializers.CharField(default='stop', initial='stop')
    # requests = serializers.CharField(default='[]', initial='[]')
    building = serializers.PrimaryKeyRelatedField(
        queryset=Building.objects.all()
    )
    class Meta:
        model = Lift
        fields = ['building'] 
        read_only_fields = ['id']          