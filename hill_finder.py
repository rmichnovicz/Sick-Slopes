import sys
import random
from subprocess import check_output
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

# follow a random path
test_path = list()
curnode = random.choice(tuple(graph.keys()))
test_path.append(curnode)
for i in range(49):
    options = graph[curnode] - set(test_path);
    if len(options) == 0:
        print('no links :(')
        break
    curnode = random.choice(tuple(options))
    test_path.append(curnode)


def get_node_entry_by_id(target_node):
    return (item for item in map_data 
            if item["data"]["id"] == target_node).__next__()

def latlong_dist(lat1_raw, lon1_raw, lat2_raw, lon2_raw):
    lat1 = radians(float(lat1_raw))
    lon1 = radians(float(lon1_raw))
    lat2 = radians(float(lat2_raw))
    lon2 = radians(float(lon2_raw))
    # approximate radius of earth in m
    R = 6373000.0
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance

with open('pins.txt', 'w') as trace_file:
    for node in test_path:
        node_info = get_node_entry_by_id(node)
        lat = node_info['data']['lat']
        lon = node_info['data']['lon']
        write_string = str(lat) + ', ' + str(lon) + '\n'
        trace_file.write(write_string)




'''#edge_len_max = 0
for entry in map_data:
    if (entry['type'] == 'node'
            and 'data' in entry.keys()
            and 'id' in entry['data'].keys()
            and entry['data']['id'] in graph.keys()
    ):
        for neighbor in graph[entry['data']['id']]:
            neighbor_entry = get_node_entry_by_id(neighbor)
            
            # distance = latlong_dist(
            #         entry['data']['lat'],
            #         entry['data']['lon'],
            #         neighbor_entry['data']['lat'],
            #         neighbor_entry['data']['lon']
            # )
            # print('Result:', distance)
            # edge_len_max = max(edge_len_max, distance)

#print('\n', 'Maximum:', edge_len_max)
'''
