import random
import subprocess
from map_to_graph import map_to_graph
import math
import osmapi
import os.path
import pickle
from numpy import linspace

def get_elevations_by_coords(lats, lngs):
    queries = dict()
    for lat, lng in zip(lats, lngs):
        fname = ('grd' + ('n' if lat>0 else 's') 
                 + str(math.ceil(abs(lat))).zfill(2)
                 + ('e' if lng>0 else 'w')
                 + str(math.ceil(abs(lng))).zfill(3)
                 )

        s = str(lng) + ' ' + str(lat) + '\n'
        if fname in queries.keys():
            queries[fname] += s
        else:
            queries[fname] = s

    elevations = []
    for fname in queries.keys():
        database_path = fname + '_13/w001001.adf'

        proc = subprocess.Popen(
            ['gdallocationinfo', database_path, '-valonly', '-geoloc'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            universal_newlines=True
        )
        output, err = proc.communicate(queries[fname])
        elevations += output.splitlines()

    return elevations

def get_node_entry(target_node):
    return (item for item in map_data 
            if item["data"]["id"] == target_node).__next__()

def get_coords_by_nodes(nodes):
    lats, lons = list(), list()
    for node in nodes:
        node_info = get_node_entry(node)
        lats.append( float(node_info['data']['lat']) )
        lons.append( float(node_info['data']['lon']) )
    return (lats, lons)

def get_edge(node1, node2):
    pass




if __name__ == '__main__':
    api_link = osmapi.OsmApi()

    try:
        if os.path.exists('map.dat'):
            print('loading local map...')
            with open('map.dat', 'rb') as f:
                map_data = pickle.load(f)
        else:
            print('requesting map...')
            map_data = api_link.Map(-83.1,33.1, -83.05,33.15)
            with open('map.dat', 'wb') as f:
                pickle.dump(map_data, f)

    except: # osmapi.OsmApi.MaximumRetryLimitReachedError:  #TODO: handle errors
        print("Could not get map data!")

    print('converting map to graph...')
    graph = map_to_graph(map_data)
    print('graph completed with %d nodes' % (len(graph),))

    # print('finding node heights...')
    # node_heights = dict()
    # node_list = list(graph.keys())
    # lats, lons = get_coords_by_nodes(node_list)
    # elevations = get_elevations_by_nodes(lats, lons)
    # for i in range(len(node_list)):
    #     node_heights[node_list[i]] = elevations[i]

    print('building node coordinate list...')
    node_lats, node_lons = dict(), dict()
    nodes = list(graph.keys())
    lats, lons = get_coords_by_nodes(nodes)
    for i in range(len(nodes)):
        node_lats[nodes[i]] = lats[i]
        node_lons[nodes[i]] = lons[i]


    print('scanning edges...')
    datapts_per_degree = 10800
    unscanned = [(k,v) for k,vlist in graph.items() for v in vlist]
    edges = dict()

    superquery_lats = []
    superquery_lons = []
    superquery_keys = []
    for src, dst in unscanned:
        measures_lat = int(abs(node_lats[src]-node_lats[dst]) * datapts_per_degree)
        measures_lon = int(abs(node_lons[src]-node_lons[dst]) * datapts_per_degree)
        n_steps = max(measures_lat, measures_lon)
        #print(n_steps)

        lat_steps = linspace(node_lats[src], node_lats[dst], 
                             num=n_steps, endpoint=False)
        lon_steps = linspace(node_lons[src], node_lons[dst], 
                             num=n_steps, endpoint=False)

        superquery_lats += lat_steps.tolist()
        superquery_lons += lon_steps.tolist()
        superquery_keys += [(src,dst)] * n_steps

    #print(len(superquery_keys), len(superquery_lats), len(superquery_lons))
    elevations = get_elevations_by_coords(superquery_lats, superquery_lons)
    for i in range(len(elevations)):
        if superquery_keys[i] in edges.keys():
            edges[superquery_keys[i]].append(elevations[i])
        else:
            edges[superquery_keys[i]] = [elevations[i]]

    for c in random.sample(list(edges.keys()), 20):
        print(c, ['%.2f' % float(x) for x in edges[c]])



    # print('identifying local maxima...')
    # local_maxima = set()
    # for node in graph.keys():
    #     if node_heights[node] > max(node_heights[n] for n in graph[node]):
    #         local_maxima.add(node)

    # print(len(local_maxima))



    '''# follow a random path
    test_path = list()
    curnode = random.choice(tuple(graph.keys()))
    test_path.append(curnode)
    for i in range(49):
        options = graph[curnode] - set(test_path);
        if len(options) == 0:
            print('no links :(')
            break
        curnode = random.choice(tuple(options))
        test_path.append(curnode)'''

    '''def latlong_dist(lat1_raw, lon1_raw, lat2_raw, lon2_raw):
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
        return distance'''

    '''with open('pins.txt', 'w') as trace_file:
        for node in test_path:
            node_info = get_node_entry(node)
            lat = node_info['data']['lat']
            lon = node_info['data']['lon']
            write_string = str(lat) + ', ' + str(lon) + '\n'
            trace_file.write(write_string)'''

    '''#edge_len_max = 0
    for entry in map_data:
        if (entry['type'] == 'node'
                and 'data' in entry.keys()
                and 'id' in entry['data'].keys()
                and entry['data']['id'] in graph.keys()
        ):
            for neighbor in graph[entry['data']['id']]:
                neighbor_entry = get_node_entry(neighbor)
                
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
