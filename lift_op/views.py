from lift_op.serializers import *
from django.http.response import JsonResponse
from rest_framework.parsers import JSONParser 
from lift_op.models import *
from rest_framework import status
from rest_framework.views import APIView
from rest_framework import viewsets
import threading,json
from lift_op.helpers import *

# Create your views here.

class LiftInitialization(APIView):

    def post(self,request):
        '''Function to initialize number of lifts and number of floors in a building
        Body format:
        {
            "building":{
                "name":"str",
                "floors":int,
                "lifts":int
            }
        }
        Return data format:
        {
            "msg": "Lifts initialized successfully.",
            "building_id": int,
            "lift_ids": [Array]
        }
        '''
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
        '''
        Function to call lift to a floor.
        Body format:
        {
            "building_id":int,
            "requested_floor":int
        }
        Return data format:
        {'msg':'Lift requested successfully.'}
        '''
        try:
            data = JSONParser().parse(request)
            building_id = data.get('building_id',None)
            requested_floor = data.get('requested_floor',None)
            if not building_id or requested_floor==None:
                return JsonResponse({'msg':'Please enter all data.'},status=status.HTTP_400_BAD_REQUEST)
            if requested_floor<0 or requested_floor>=Building.objects.get(id=building_id).floors:
                return JsonResponse({'msg':'Invalid floor number.'},status=status.HTTP_400_BAD_REQUEST)
            lifts = Lift.objects.filter(building_id=building_id).exclude(status='maintenance')
            if len(lifts) == 0:
                return JsonResponse({'msg':'No lifts available.'},status=status.HTTP_200_OK)
            
            closest_lift,lift_distance = get_closest_lift(lifts,requested_floor)
            if lift_distance == 0:
                Lift.objects.filter(id=closest_lift.id).update(door='open')
                return JsonResponse({'msg':f'Lift {closest_lift.id} already present.'},status=status.HTTP_200_OK)
            lift_requests = json.loads(closest_lift.requests)
            if requested_floor not in lift_requests:
                lift_requests.append(requested_floor)
                if (closest_lift.status=='going up' and requested_floor>closest_lift.destination) or (closest_lift.status=='going down' and requested_floor<closest_lift.destination) or closest_lift.status=='stop':
                    closest_lift = Lift.objects.update_or_create(id=closest_lift.id,defaults={'requests':json.dumps(lift_requests),'destination':requested_floor})[0]
                else:
                    closest_lift = Lift.objects.update_or_create(id=closest_lift.id,defaults={'requests':json.dumps(lift_requests)})[0]
                if closest_lift.status=='stop':
                    lift_thread = threading.Thread(target=lift_control, args=(closest_lift,))
                    lift_thread.start()
            return JsonResponse({'msg':'Lift requested successfully.'},status=status.HTTP_200_OK)
        except:
            return JsonResponse({'msg':'Something went wrong.'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class LiftData(APIView):

    def get(self,request):
        '''
        Function to get data about specific lift.
        Query params format:
        lift_id=int
        data_type="str",Possible values: requests,status,next_destination
        Return data format:
        1.{'lift_requests':[Array]}
        2.{
            'current_floor':int,
            'destination_floor':int,
            'status':'str',Possible values:stop,going up,going down,maintenance
            'door_status':'str',Possible values:open,close
        }
        3.{'next_destination':int}
        '''
        try:
            data = request.query_params
            lift_id = data.get('lift_id',None)
            data_type = data.get('data_type',None)
            if not lift_id or not data_type:
                return JsonResponse({'msg':'Please enter all data.'},status=status.HTTP_400_BAD_REQUEST)
            lift = Lift.objects.get(id=lift_id)
            if data_type == 'requests':
                lift_requests = lift.lift_requests
                return JsonResponse({'lift_requests':lift_requests},status=status.HTTP_200_OK)
            elif data_type == 'status':
                lift_status = {
                    'current_floor':lift.current_floor,
                    'destination_floor':lift.destination,
                    'status':lift.status,
                    'door_status':lift.door
                }
                return JsonResponse(lift_status,status=status.HTTP_200_OK)   
            elif data_type == 'next_destination':
                current_floor = lift.current_floor
                lift_requests = json.loads(lift.lift_requests)
                lift_status = lift.status
                if lift_status == 'going up':
                    destination = min(filter(lambda x:x>current_floor,lift_requests))
                elif lift_status == 'going down':
                    destination = max(filter(lambda x:x<current_floor,lift_requests))
                else:
                    return JsonResponse({'msg':'Invalid request'},status=status.HTTP_200_OK)
                return JsonResponse({'next_destination':destination},status=status.HTTP_200_OK)
            else:
                return JsonResponse({'msg':'Invalid request'},status=status.HTTP_200_OK)
        except:
            return JsonResponse({'msg':'Something went wrong.'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class FloorRequest(APIView):

    def post(self,request):
        '''
        Function to request destination floor for passenger from inside lift.
        Body format:
        {
            "building_id":int,
            "lift_id":int,
            "requested_floor":int
        }
        Return data format:
        {'msg':'You will reach your destination soon.'}
        '''
        try:
            data = JSONParser().parse(request)
            building_id = data['building_id']
            lift_id = data['lift_id']
            requested_floor = data.get('requested_floor',None)
            if not lift_id or requested_floor==None or not building_id:
                return JsonResponse({'msg':'Please enter all data.'},status=status.HTTP_400_BAD_REQUEST)
            if requested_floor<0 or requested_floor>=Building.objects.get(id=building_id).floors:
                return JsonResponse({'msg':'Invalid floor number.'},status=status.HTTP_400_BAD_REQUEST)
            lift = Lift.objects.get(id=lift_id)
            if lift.current_floor == requested_floor:
                return JsonResponse({'msg':'Requesting current floor.Request not registered.'},status=status.HTTP_200_OK)
            lift_requests = json.loads(lift.requests)
            if requested_floor not in lift_requests:
                lift_requests.append(requested_floor)
                if (lift.status=='going up' and requested_floor>lift.destination) or (lift.status=='going down' and requested_floor<lift.destination) or lift.status=='stop':
                    lift = Lift.objects.update_or_create(id=lift.id,defaults={'requests':json.dumps(lift_requests),'destination':requested_floor})[0]
                else:
                    lift = Lift.objects.update_or_create(id=lift.id,defaults={'requests':json.dumps(lift_requests)})[0]
                if lift.status=='stop':
                    lift_thread = threading.Thread(target=lift_control, args=(lift,))
                    lift_thread.start()
            return JsonResponse({'msg':'You will reach your destination soon.'},status=status.HTTP_200_OK)
        except:
            return JsonResponse({'msg':'Something went wrong.'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class LiftMaintenance(APIView):

    def get(self,request):
        '''
        Function to fetch all lifts under maintenance in a building.
        Query params format:
        building_id=str
        Return data format:
        [Array]
        '''
        try:
            building_id = request.query_params.get('building_id',None)
            if not building_id:
                return JsonResponse({'msg':'Building id missing.'},status=status.HTTP_400_BAD_REQUEST)
            lifts = Lift.objects.filter(status='maintenance')
            lifts_serializer = MaintenanceLiftSerializer(lifts,many=True)
            return JsonResponse(lifts_serializer.data,status=status.HTTP_200_OK,safe=False)
        except:
            return JsonResponse({'msg':'Something went wrong.'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def post(self,request):
        '''
        Function to set status of lift in case of maintenance or end of maintenance.
        Body format:
        {
            "lift_id":int,
            "msg":"str",Possible values:In maintenance,Maintenance completed
        }
        Return data format:
        {'msg':'Lift status updated successfully'}
        '''
        try:
            data = JSONParser().parse(request)
            lift_id = data.get('lift_id',None)
            msg = data.get('msg',None)
            if (not lift_id) or (not msg):
                return JsonResponse({'msg':'Please enter all data.'},status=status.HTTP_400_BAD_REQUEST) 
            if msg == 'In maintenance':
                updated_data={'status':'maintenance','current_floor':0,'destination':0,'requests':'[]','door':'close'}
            elif msg == 'Maintenance completed':
                updated_data={'status':'stop','current_floor':0,'destination':0,'requests':'[]','door':'close'}
            else:
                return JsonResponse({'msg':'Enter proper message'},status=status.HTTP_200_OK)
            lift = Lift.objects.get(id=lift_id)
            if lift.status == 'going up' or lift.status=='going down':
                return JsonResponse({'msg':'Lift in motion'},status=status.HTTP_200_OK)
            lift_serializer = MaintenanceLiftSerializer(lift,data=updated_data,partial=True)
            if lift_serializer.is_valid():
                lift_serializer.save()
                return JsonResponse({'msg':'Lift status updated successfully'},status=status.HTTP_200_OK)
            else:
                return JsonResponse({'msg':'Invalid data'},status=status.HTTP_400_BAD_REQUEST)
        except:
            return JsonResponse({'msg':'Something went wrong.'},status=status.HTTP_500_INTERNAL_SERVER_ERROR)