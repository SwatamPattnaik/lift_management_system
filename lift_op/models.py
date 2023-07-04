from django.db import models

# Create your models here.

class Building(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, blank=True, null=True)
    floors = models.IntegerField(default=1)
    lifts = models.IntegerField(default=1)

    class Meta:
        managed = True
        db_table = 'building'

class Lift(models.Model):
    id =models.AutoField(primary_key=True)
    building = models.ForeignKey(Building,models.DO_NOTHING,db_column='building')
    current_floor = models.IntegerField(default=0)
    destination = models.IntegerField(null=True,default=0)
    status = models.CharField(max_length=50,default='stop')
    requests = models.CharField(max_length=200,default='[]')
    door = models.CharField(max_length=50,default='close')

    class Meta:
        managed = True
        db_table = 'lift'