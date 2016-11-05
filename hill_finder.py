from subprocess import check_output
import sys
import math
from map_to_graph import map_to_graph

api_link = osmapi.OsmApi()

print('starting request')
try:
    map_data = api_link.Map(-83.1,33.1, -83.05,33.15)
except: # osmapi.OsmApi.MaximumRetryLimitReachedError:  #TODO: handle errors
    print("Could not get map data!")

graph = map_to_graph(map_data)

lat, lng = 33.373447, -84.7394

database_path = 'grdn' + str(math.ceil(abs(lat))) + 'w' \
         + str(math.ceil(abs(lng))).zfill(3) + '_13/w001001.adf'

#print(database_path)

elevation = float(check_output(
    ['gdallocationinfo',database_path,
     '-valonly','-geoloc',str(lng),str(lat)
     ])
)

print(elevation)
