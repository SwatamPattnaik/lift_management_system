from django.shortcuts import render
from lift_op.serializers import *
from django.http.response import JsonResponse
from rest_framework.parsers import JSONParser 
from lift_op.models import *
from rest_framework import status
from rest_framework.views import APIView
from rest_framework import viewsets
from django.http.response import JsonResponse
from rest_framework.parsers import JSONParser 

# Create your views here.

class LiftInitialization(APIView):

    def post(self,request):
        try:
            data = JSONParser().parse(request)
            building_info = data.pop('building')
            building_serializer = BuildingSerializer(data=building_info)
            if building_serializer.is_valid():
                building_instance = building_serializer.save()
                data['building'] = building_instance.id
            else:
                return JsonResponse({'msg':'Invalid building data.'},status=status.HTTP_400_BAD_REQUEST)
            
            lift_serializer = LiftSerializer(data=[data for i in range(building_info['floors'])],many=True)
            if lift_serializer.is_valid():
                lift_serializer.save()
                return JsonResponse({'msg':'Lifts initialized successfully.'},status=status.HTTP_201_CREATED,safe=False)
            else:
                return JsonResponse({'msg':'Invalid data.'},status=status.HTTP_400_BAD_REQUEST)
        except:
            return JsonResponse({'msg':'Something went wrong.'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    
