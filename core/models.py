from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

class User(AbstractUser):

    is_passenger = models.BooleanField(default=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.username

class MetroLine(models.Model):

    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7, default='#6c757d', help_text="Hex code, e.g., #FF0000")
    is_active = models.BooleanField(default=True) 
    def __str__(self):
        return self.name

class Station(models.Model):

    name = models.CharField(max_length=100, unique=True)
    distance_from_hub = models.FloatField(default=0.0, help_text="Distance in km from the central station")
    def __str__(self):
        return self.name
    @property
    def lines(self):
        return [sol.line.name for sol in self.stationonline_set.all()]

class StationOnLine(models.Model):

    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    line = models.ForeignKey(MetroLine, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0, help_text="Order of station (1, 2, 3...)")
    is_interchange = models.BooleanField(default=False, help_text="Check if users can change lines here")

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.line.name} - {self.station.name}"
class Ticket(models.Model):

    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),   
        ('USED', 'Used'),      
        ('EXPIRED', 'Expired'), 
        ('CANCELLED', 'Cancelled'),
    )

    ticket_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    source = models.ForeignKey(Station, related_name='source_tickets', on_delete=models.CASCADE)
    destination = models.ForeignKey(Station, related_name='dest_tickets', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)

    price = models.DecimalField(max_digits=6, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    entry_time = models.DateTimeField(null=True, blank=True)
    exit_time = models.DateTimeField(null=True, blank=True)

    route_info = models.TextField(default="Direct Trip")

    def __str__(self):
        return f"Ticket {self.ticket_id} ({self.status})"
    
class SystemSettings(models.Model):
    is_metro_open = models.BooleanField(default=True)
    
    def __str__(self):
        return "Metro System Status"

    class Meta:
        verbose_name_plural = "System Settings"