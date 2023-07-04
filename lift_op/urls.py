from django.urls import path
from lift_op.views import *

urlpatterns = [
    path('initialize_building/', LiftInitialization.as_view(), name='initialize_building'),
    path('call_lift/', LiftCall.as_view(), name='call_lift'),
    path('lift_data/', LiftData.as_view(), name='lift_data'),
    path('request_floor/', FloorRequest.as_view(), name='request_floor')
]