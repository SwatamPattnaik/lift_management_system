Lift Management System

Apis available:
1. /lms/api/v1/initialize_building/:
    POST: API to initialize number of lifts and number of floors in a building
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


2. /lms/api/v1/call_lift/:
    POST: API to call lift to a floor.
        Body format:
        {
            "building_id":int,
            "requested_floor":int
        }
        Return data format:
        {'msg':'Lift requested successfully.'}
3. /lms/api/v1/lift_data/:
    GET:API to get data about specific lift.
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
    
4. /lms/api/v1/request_floor/:
    POST:API to request destination floor for passenger from inside lift.
        Body format:
        {
            "building_id":int,
            "lift_id":int,
            "requested_floor":int
        }
        Return data format:
        {'msg':'You will reach your destination soon.'}

5. /lms/api/v1/maintenance/:
    GET: API to fetch all lifts under maintenance in a building.
        Query params format:
        building_id=str
        Return data format:
        [Array]
    POST: API to set status of lift in case of maintenance or end of maintenance.
        Body format:
        {
            "lift_id":int,
            "msg":"str",Possible values:In maintenance,Maintenance completed
        }
        Return data format:
        {'msg':'Lift status updated successfully'}

Working principles:
1.User initializes a building with number of floors and number of lifts.
2.A lift takes 5 seconds to move from one floor to the next.
3.When a passenger requests a lift from a floor,the closest lift to the floor in the moving direction of the lift(if moving) is assigned to the floor.Requests coming from a floor on which a lift is present will result in the doors of the lift opening automatically and will close once the lift starts moving again.
4.Once passenger has entered the lift,they can request which floor they want to travel to.Requesting a floor opposite to the direction of movement of lift will not result in immediate turnaround of the lift.
5.A lift moving either up or down will continue to do so until it reaches its highest/lowest requested floor and then only change directions or stop if there are no pending requests.
6.Once a lift reaches a requested floor,the doors will open automatically and stay open for 5 seconds,afterwhich they close and continue on their journey.
7.Live status of each lift can be obtained at any time.