from subprocess import check_output
import sys
from map_to_graph import map_to_graph
from math import sin, cos, sqrt, atan2, radians
import osmapi

def get_elevation(lat, lng):
    database_path = 'grdn' + str(math.ceil(abs(lat))) + 'w' \
         + str(math.ceil(abs(lng))).zfill(3) + '_13/w001001.adf'
    #print(database_path)
    elevation = float(check_output(
        ['gdallocationinfo',database_path,
         '-valonly','-geoloc',str(lng),str(lat)
         ])
    )
    return elevation


api_link = osmapi.OsmApi()

print('starting request')
try:
    map_data = api_link.Map(-83.1,33.1, -83.05,33.15)
except: # osmapi.OsmApi.MaximumRetryLimitReachedError:  #TODO: handle errors
    print("Could not get map data!")

graph = map_to_graph(map_data)

edge_len_max = 0
for entry in map_data:
    if (entry['type'] == 'node'
            and 'data' in entry.keys()
            and 'id' in entry['data'].keys()
            and entry['data']['id'] in graph.keys()
    ):
        for neighbor in graph[entry['data']['id']]:
            neighbor_entry = (item for item in map_data 
                              if item["data"]["id"] == neighbor).__next__()
            
            # approximate radius of earth in m
            R = 6373000.0

            lat1 = radians(float(entry['data']['lat']))
            lon1 = radians(float(entry['data']['lon']))
            lat2 = radians(float(neighbor_entry['data']['lat']))
            lon2 = radians(float(neighbor_entry['data']['lon']))

            #print(lat1, lon1, lat2, lon2)

            dlon = lon2 - lon1
            dlat = lat2 - lat1

            a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))

            distance = R * c
            print("Result:", distance)

            edge_len_max = max(edge_len_max, distance)

print('\n', 'Maximum:', edge_len_max)

