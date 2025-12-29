import csv
from django.core.management.base import BaseCommand
from core.models import MetroLine, Station, StationOnLine

class Command(BaseCommand):
    help = 'Loads metro data from lines.csv and calculates simulated distances'

    def handle(self, *args, **kwargs):
        # 1. Clear existing data to prevent duplicates
        StationOnLine.objects.all().delete()
        Station.objects.all().delete()
        MetroLine.objects.all().delete()
        
        print("Cleared old data...")

        with open('lines.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                line_name = row['line_name']
                metro_line, created = MetroLine.objects.get_or_create(name=line_name)
                print(f"Processing {line_name}...")

                stations_list = row['stations_list'].split(',')
                
                for index, station_name in enumerate(stations_list):
                    station_name = station_name.strip()
                    

                    simulated_distance = (index + 1)
                 
                    station, created = Station.objects.get_or_create(
                        name=station_name,
                        defaults={'distance_from_hub': simulated_distance}
                    )
                    
                    StationOnLine.objects.create(
                        line=metro_line,
                        station=station,
                        order=index + 1
                    )

        self.stdout.write(self.style.SUCCESS('Successfully loaded Montreal Metro data with distances!'))