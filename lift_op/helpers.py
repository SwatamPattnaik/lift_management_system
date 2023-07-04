from lift_op.models import *
import time,json

def get_closest_lift(lifts,requested_floor):
    '''
    Function to find closest lift to requested floor.
    '''
    closest_lift = ''
    min_distance = float('inf')
    for lift in lifts:
        status = lift.status
        if requested_floor<lift.current_floor:
            if status == 'going up':
                lift_distance = 2*lift.destination-lift.current_floor-requested_floor
            elif status == 'going down' or 'stop':
                lift_distance = lift.current_floor-requested_floor
        elif requested_floor>lift.current_floor:
            if status == 'going up' or 'stop':
                lift_distance = requested_floor-lift.current_floor
            elif status == 'going down':
                lift_distance = lift.current_floor+requested_floor-2*lift.destination
        else:
            lift_distance = 0
        if lift_distance<min_distance:
                    closest_lift = lift
                    min_distance = lift_distance
        print(lift_distance,lift.id,closest_lift)
    return closest_lift,lift_distance

def lift_control(lift):
    '''
    Function to control movement of lifts.
    '''
    while True:
        if lift.destination>lift.current_floor:
            change = 1
            status = 'going up'
        else:
            change = -1
            status = 'going down'
        time.sleep(5)
        lift = Lift.objects.update_or_create(id=lift.id,defaults={'current_floor':lift.current_floor+change,'door':'close','status':status})[0]
        lift_requests = json.loads(lift.requests)
        if lift.current_floor in lift_requests:
            lift_requests.remove(lift.current_floor)
            lift = Lift.objects.update_or_create(id=lift.id,defaults={'door':'open','requests':json.dumps(lift_requests)})[0]
            time.sleep(5)
            lift = Lift.objects.update_or_create(id=lift.id,defaults={'door':'close'})[0]
        if lift.current_floor == lift.destination:
            lift_requests = json.loads(lift.requests)
            if len(lift_requests)!=0:
                if lift.status=='going up':
                    lift = Lift.objects.update_or_create(id=lift.id,defaults={'destination':min(lift_requests)})[0]
                else:
                    lift = Lift.objects.update_or_create(id=lift.id,defaults={'destination':max(lift_requests)})[0]
            else:
                Lift.objects.update_or_create(id=lift.id,defaults={'status':'stop'})
                break