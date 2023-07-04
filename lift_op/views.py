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
import threading,json
from lift_op.helpers import *

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
            
            lift_serializer = LiftSerializer(data=[data for i in range(building_info['lifts'])],many=True)
            
            if lift_serializer.is_valid():
                lift_instance = lift_serializer.save()
                lift_ids = [instance.id for instance in lift_instance]
                return JsonResponse({'msg':'Lifts initialized successfully.','building_id':building_instance.id,'lift_ids':lift_ids},status=status.HTTP_201_CREATED,safe=False)
            else:
                return JsonResponse({'msg':'Invalid data.'},status=status.HTTP_400_BAD_REQUEST)
        except:
            return JsonResponse({'msg':'Something went wrong.'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    
class LiftCall(APIView):

    def post(self,request):
        data = JSONParser().parse(request)
        building_id = data.get('building_id',None)
        requested_floor = data.get('requested_floor',None)
        if not building_id or not requested_floor:
            return JsonResponse({'msg':'Please enter all data.'},status=status.HTTP_400_BAD_REQUEST)
        lifts = Lift.objects.filter(building_id=building_id).exclude(status='maintenance')
        if len(lifts) == 0:
            return JsonResponse({'msg':'No lifts available.'},status=status.HTTP_200_OK)
        
        closest_lift,lift_distance = get_closest_lift(lifts,requested_floor)
        if lift_distance == 0:
            Lift.objects.filter(id=closest_lift.id).update(door='open')
            return JsonResponse({'msg':'Lift already present.'},status=status.HTTP_200_OK)
        lift_requests = json.loads(closest_lift.requests)
        lift_requests.append(requested_floor)
        if (closest_lift.status=='going up' and requested_floor>closest_lift.destination) or (closest_lift.status=='going down' and requested_floor<closest_lift.destination) or closest_lift.status=='stop':
            closest_lift = Lift.objects.create_or_update(id=closest_lift.id,defaults={'requests':json.dumps(lift_requests),'destination':requested_floor})
        if closest_lift.status=='stop':
            lift_thread = threading.Thread(target=lift_control, args=(closest_lift,))
            lift_thread.start()
        return JsonResponse({'msg':'Lift requested successfully.'},status=status.HTTP_200_OK)
    
class LiftData(APIView):

    def get(self,request):
        data = request.query_params
        lift_id = data.get('lift_id',None)
        data_type = data.get('data_type',None)
        if not lift_id or not data_type:
            return JsonResponse({'msg':'Please enter all data.'},status=status.HTTP_400_BAD_REQUEST)
        lift = Lift.objects.get(id=lift_id)
        if data_type == 'requests':
            lift_requests = lift.lift_requests
            return JsonResponse({'msg':'Success','lift_requests':lift_requests},status=status.HTTP_200_OK)
        elif data_type == 'status':
            status = {
                'current_floor':lift.current_floor,
                'destination_floor':lift.destination_floor,
                'status':lift.status,
                'door_status':lift.door
            }
            return JsonResponse(status,status=status.HTTP_200_OK)   
    
class FloorRequest(APIView):

    def post(self,request):
        data = JSONParser().parse(request)
        lift_id = data['lift_id']
        requested_floor = data.get('requested_floor',None)
        if not lift_id or not requested_floor:
            return JsonResponse({'msg':'Please enter all data.'},status=status.HTTP_400_BAD_REQUEST)
        lift = Lift.objects.get(id=lift_id)
        if lift.current_floor == requested_floor:
            return JsonResponse({'msg':'Requesting current floor.Request not registered.'},status=status.HTTP_200_OK)
        lift_requests = json.loads(lift.requests)
        lift_requests.append(requested_floor)
        if (lift.status=='going up' and requested_floor>lift.destination) or (lift.status=='going down' and requested_floor<lift.destination) or lift.status=='stop':
            lift = Lift.objects.create_or_update(id=lift.id,defaults={'requests':json.dumps(lift_requests),'destination':requested_floor})
        else:
            lift = Lift.objects.create_or_update(id=lift.id,defaults={'requests':json.dumps(lift_requests)})
        if lift.status=='stop':
            lift_thread = threading.Thread(target=lift_control, args=(lift,))
            lift_thread.start()
        return JsonResponse({'msg':'You will reach your destination soon.'},status=status.HTTP_200_OK)

class LiftMaintenance(APIView):

    def get(self,request):
        building_id = request.query_params.get('building_id',None)
        if not building_id:
            return JsonResponse({'msg':'Building id missing.'},status=status.HTTP_400_BAD_REQUEST)
        lifts = Lift.objects.filter(status='maintenance')
        lifts_serializer = MaintenanceLiftSerializer(lifts,many=True)
        return JsonResponse(lifts_serializer.data,status=status.HTTP_200_OK)

    def post(self,request):
        lift_id = request.query_params.get('lift_id',None)
        msg = request.query_params.get('msg',None)
        if not lift_id or not status:
            return JsonResponse({'msg':'Please enter all data.'},status=status.HTTP_400_BAD_REQUEST) 
        if msg == 'In maintenance':
            data={'status':'maintenance'}
        elif msg == 'Maintenance completed':
            data={'status':'stop'}
        else:
            return JsonResponse({'msg':'Enter proper message'},status=status.HTTP_200_OK)
        lift = Lift.objects.get(id=lift_id)
        lift_serializer = MaintenanceLiftSerializer(lift,data=data)
        if lift_serializer.is_valid():
            lift_serializer.save()
            return JsonResponse({'msg':'Lift status updated successfully'})