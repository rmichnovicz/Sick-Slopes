import subprocess
import math
import osmapi
import os.path
import pickle
from numpy import linspace
import acceleration

def get_elevations_by_coords(lats, lngs, country):
    queries = dict()
    for lat, lng in zip(lats, lngs):
        fname = ('grd' + ('n' if lat>0 else 's')
                 + str(abs(math.ceil(lat))).zfill(2)
                 + ('e' if lng>=0 else 'w') # lng = 0 block is all east I guess
                 + str(abs(math.floor(lng))).zfill(3)
                 )

        s = str(lng) + ' ' + str(lat) + '\n'
        if fname in queries.keys():
            queries[fname] += s
        else:
            queries[fname] = s

    elevations = []
    for fname in queries.keys():
        if country == 'United States': # TODO deal with AK
            database_path = 'elevationdata/' + fname + '_13/w001001.adf'
        if country == 'Mexico' or country == 'Canada' or country == None:
            # TODO deal with country == None which would be sorta wierd
            database_path = 'elevationdata/' + fname + '_1/w001001.adf'
        proc = subprocess.Popen(
            ['gdallocationinfo', database_path, '-valonly', '-geoloc'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            universal_newlines=True
        )
        output, err = proc.communicate(queries[fname])
        elevations += [float(s) for s in output.splitlines()]

    return elevations

def get_node_entries(target_nodes, map_data):
    # return (item for item in map_data
    #         if item["data"]["id"] == target_node).__next__()
    for item in map_data:
        if item["data"]["id"] in target_nodes:
            yield (item["data"]["id"], item)

def make_map(mapsize = (-84.4203, 33.7677, -84.3812, 33.7874),
    country = 'United States'):
                        # (west, south, east, north), string

    api_link = osmapi.OsmApi(#username='evanxq1@gmail.com',
                             #password='hrVQ*DO9aD9q'#,
                             #api="api06.dev.openstreetmap.org"
                             )

    querypath = 'queryresults/' + str(mapsize) + '.dat'
    try:
        if os.path.exists(querypath):
            print('opening query result...')
            with open(querypath, 'rb') as f:
                q = pickle.load(f)
                return q[0], q[1], q[2], q[3], q[4], q[5], q[6]
    except IOError as e:
            print("Couldn't read query data!", e.errorno, e.strerror)

    mapfilepath = 'maps/map'+str(mapsize)+'.dat'

    try:
        if os.path.exists(mapfilepath):
            print('loading local map...')
            with open(mapfilepath, 'rb') as f:
                map_data = pickle.load(f)
        else:
            print('requesting map...')
            map_data = api_link.Map(mapsize[0], mapsize[1],
                                    mapsize[2], mapsize[3])
            with open(mapfilepath, 'wb') as f:
                pickle.dump(map_data, f) # TODO delete this entire try block tbh

    except IOError as e:
        print("Couldn't write map data!", e.errorno, e.strerror)

    except: # osmapi.OsmApi.MaximumRetryLimitReachedError:  #TODO: handle errors
        print("Could not get map data!")
        return False, [], [], [], [], [], []



    #with open('log/map_data_example.txt','w') as f:
        #f.write(str(map_data))

    print('converting map to graph...')
    graph = map_to_graph(map_data)
    print('graph completed with %d nodes' % len(graph))
    #keys = list(graph.keys())
    # for k in keys[50:70]:
        #print(k, graph[k])


    print('finding node heights and building coordinate list...')
    node_heights, node_latlons = dict(), dict()
    stoplights = set()
    for node, node_info in get_node_entries(graph.keys(), map_data):
        node_latlons[node] = (float(node_info['data']['lat']),
                              float(node_info['data']['lon']))
        if ('tag' in node_info['data'] and 'highway' in node_info['data']['tag']
                and node_info['data']['tag']['highway'] == 'traffic_signals'
        ):
            stoplights.add(node)

    latlons_items = tuple(node_latlons.items())
    node_iter = (x[0] for x in latlons_items)
    lat_iter = (x[1][0] for x in latlons_items)
    lon_iter = (x[1][1] for x in latlons_items)
    elevations = get_elevations_by_coords(lat_iter, lon_iter, country)
    for node, elev in zip(node_iter, elevations):
        node_heights[node] = elev



    print('identifying edges...')
    datapts_per_degree = 10800
    unscanned = ((k,v) for k,vlist in graph.items() for v in vlist)
    edge_heights = dict()

    superquery_lats = []
    superquery_lons = []
    superquery_keys = []
    for src, dst in unscanned:
        llsrc, lldst = node_latlons[src], node_latlons[dst]
        measures_lat = int(abs(llsrc[0]-lldst[0]) * datapts_per_degree)
        measures_lon = int(abs(llsrc[1]-lldst[1]) * datapts_per_degree)
        n_steps = max(measures_lat, measures_lon, 2)
        #print(n_steps)

        lat_steps = linspace(llsrc[0], lldst[0], num=n_steps, endpoint=True)
        lon_steps = linspace(llsrc[1], lldst[1], num=n_steps, endpoint=True)
        superquery_lats += lat_steps.tolist()
        superquery_lons += lon_steps.tolist()
        superquery_keys += [(src,dst)] * n_steps

    print("Found %d. Scanning them..." % len(superquery_keys))
    elevations = get_elevations_by_coords(superquery_lats, superquery_lons, country)
    for i in range(len(elevations)):
        item = elevations[i]
        if str(superquery_keys[i]) in edge_heights.keys():
            edge_heights[str(superquery_keys[i])].append(item)
        else:
            edge_heights[str(superquery_keys[i])] = [item]
        # The str() is gross, but there's no way of using tuples as keys in JSON.
    print('identifying local and global maxima...')
    local_maxima = set()
    for node in graph.keys():
        if (node_heights[node]
            > max(node_heights[n] for n in graph[node])
        ):
            local_maxima.add(node)

    #maxima_by_elevation = sorted(list(local_maxima), key=lambda n: node_heights[n])
    print('Found', len(local_maxima), 'local maxima')

    try:
        print('writing query result...')
        with open(querypath, 'wb') as f:
            q = pickle.dump([True, list(stoplights), list(local_maxima), graph, \
                node_heights, node_latlons, edge_heights], f)
    except IOError as e:
            print("Couldn't read query data!", e.errorno, e.strerror)


    return True, list(stoplights), list(local_maxima), graph, \
        node_heights, node_latlons, edge_heights
    # Success, data
if __name__ == '__main__':
    find_hills()

def map_to_graph(map_data):

    way_lists = list()
    way_sets = list()
    for entry in map_data:
        if (entry['type'] == 'way'
                and 'data' in entry.keys()
                and 'tag' in entry['data'].keys()
                and 'highway' in entry['data']['tag'].keys()
                and entry['data']['tag']['highway'] != 'steps'
                and 'bridge' not in entry['data']['tag']
        ):
            way = entry['data']['nd']
            way_lists.append(way)
            way_sets.append(frozenset(way))
    graph = dict()

    # node is the current node, link is the node to link to
    def graph_add(cur, link):
        if cur in graph.keys():
            graph[cur].append(link)
        else:
            graph[cur] = [link]

    # update node index n1 in way1 with links from
    # n2 in way2
    def graph_update(way1, way2, n1, n2):
        if n2 > 0:
            graph_add(way1[n1], way2[n2-1])
        if n2 < len(way2)-1:
            graph_add(way1[n1], way2[n2+1])

    # w = way index
    for w in range(len(way_lists)):
        curWay = way_lists[w]
        # n = node index in way
        for n in range(len(curWay)):
            graph_update(curWay,curWay, n,n)

            for w2 in range(len(way_lists)):
                if w != w2 and curWay[n] in way_sets[w2]:
                    n2 = way_lists[w2].index(curWay[n])
                    graph_update(curWay,way_lists[w2], n,n2)
    return graph
