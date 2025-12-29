from django.contrib import admin
from .models import User, Station, Ticket, SystemSettings, MetroLine, StationOnLine

admin.site.register(User)

class StationOnLineInline(admin.TabularInline):
    model = StationOnLine
    extra = 1
    ordering = ('order',) 
    
    autocomplete_fields = ['station', 'line']

@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ('name', 'distance_from_hub', 'display_lines')
    search_fields = ('name',) 
    
    inlines = [StationOnLineInline]

    def display_lines(self, obj):
        return ", ".join([sol.line.name for sol in obj.stationonline_set.all()])
    display_lines.short_description = 'Associated Lines'

@admin.register(MetroLine)
class MetroLineAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'is_active', 'station_count')
    list_editable = ('is_active', 'color') # Allow editing color directly in list
    search_fields = ('name',) 
    
    inlines = [StationOnLineInline]

    def station_count(self, obj):
        return obj.stationonline_set.count()
    station_count.short_description = 'Total Stations'

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'user', 'source', 'destination', 'price', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('ticket_id', 'user__username', 'source__name', 'destination__name')
    readonly_fields = ('ticket_id', 'created_at')

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'is_metro_open')
    list_editable = ('is_metro_open',)  
    
    def has_add_permission(self, request):
        return not SystemSettings.objects.exists()