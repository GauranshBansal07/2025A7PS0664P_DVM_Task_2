from django.contrib import admin
from .models import User, Station, Ticket, SystemSettings, MetroLine, StationOnLine

# 1. Register User
admin.site.register(User)

# 2. Inline for Station-to-Line relationship (The "Map" Builder)
class StationOnLineInline(admin.TabularInline):
    model = StationOnLine
    extra = 1
    # This ensures the list in the admin is sorted by the map order (1, 2, 3...)
    ordering = ('order',) 
    
    # We use autocomplete to make searching for stations fast
    autocomplete_fields = ['station', 'line']

# 3. Station Admin
@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ('name', 'distance_from_hub', 'display_lines')
    search_fields = ('name',) 
    
    # Shows which lines this station belongs to
    inlines = [StationOnLineInline]

    def display_lines(self, obj):
        # Helper to show comma-separated lines in the list view
        return ", ".join([sol.line.name for sol in obj.stationonline_set.all()])
    display_lines.short_description = 'Associated Lines'

# 4. Metro Line Admin (This is where you arrange your Map)
@admin.register(MetroLine)
class MetroLineAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'is_active', 'station_count')
    list_editable = ('is_active', 'color') # Allow editing color directly in list
    search_fields = ('name',) 
    
    # This inline allows you to Drag/Drop or number stations to build the line map
    inlines = [StationOnLineInline]

    def station_count(self, obj):
        return obj.stationonline_set.count()
    station_count.short_description = 'Total Stations'

# 5. Ticket Admin
@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'user', 'source', 'destination', 'price', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('ticket_id', 'user__username', 'source__name', 'destination__name')
    readonly_fields = ('ticket_id', 'created_at')

# 6. System Settings Admin
@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'is_metro_open')
    list_editable = ('is_metro_open',)  
    
    def has_add_permission(self, request):
        # Prevents creating more than one SystemSettings object
        return not SystemSettings.objects.exists()