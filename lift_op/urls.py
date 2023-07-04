from django.urls import path
from lift_op.views import *

urlpatterns = [
    path('initialize_building/', LiftInitialization.as_view(), name='initialize_building'),
]