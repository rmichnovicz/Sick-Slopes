import subprocess
from map_to_graph import map_to_graph
import math
import osmapi
import os.path
import pickle
from numpy import linspace
import acceleration

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
        elevations += [float(s) for s in output.splitlines()]

    return elevations

def get_node_entries(target_nodes):
    # return (item for item in map_data
    #         if item["data"]["id"] == target_node).__next__()
    for item in map_data:
        if item["data"]["id"] in target_nodes:
            yield (item["data"]["id"], item)
    

def latlong_dist(lat1_raw, lon1_raw, lat2_raw, lon2_raw):
    lat1 = math.radians(float(lat1_raw))
    lon1 = math.radians(float(lon1_raw))
    lat2 = math.radians(float(lat2_raw))
    lon2 = math.radians(float(lon2_raw))
    # approximate radius of earth in m
    R = 6373000.0
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = (math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2)
         * math.sin(dlon / 2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance




if __name__ == '__main__':
    api_link = osmapi.OsmApi(#username='evanxq1@gmail.com',
                             #password='hrVQ*DO9aD9q'#,
                             #api="api06.dev.openstreetmap.org"
                             )

    mapsize = (-84.4203,33.7677, -84.3812,33.7874)
    mapfilepath = 'map'+str(mapsize)+'.dat'

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
                pickle.dump(map_data, f)

    except: # osmapi.OsmApi.MaximumRetryLimitReachedError:  #TODO: handle errors
        print("Could not get map data!")

    #print(map_data)
    print('converting map to graph...')
    graph = map_to_graph(map_data)
    print('graph completed with %d nodes' % (len(graph),))
    keys = list(graph.keys())
    # for k in keys[50:70]:
        #print(k, graph[k])


    print('finding node heights and building coordinate list...')
    node_heights, node_latlons = dict(), dict()
    for node, node_info in get_node_entries(graph.keys()):
        node_latlons[node] = (float(node_info['data']['lat']), 
                              float(node_info['data']['lon']))

    latlons_items = tuple(node_latlons.items())
    node_iter = (x[0] for x in latlons_items)
    lat_iter = (x[1][0] for x in latlons_items)
    lon_iter = (x[1][1] for x in latlons_items)
    elevations = get_elevations_by_coords(lat_iter, lon_iter)
    for node, elev in zip(node_iter, elevations):
        node_heights[node] = elev
        


    print('identifying edges...')
    datapts_per_degree = 10800
    unscanned = [(k,v) for k,vlist in graph.items() for v in vlist]
    edge_heights = dict()

    superquery_lats = []
    superquery_lons = []
    superquery_keys = []
    for src, dst in unscanned:
        # print((node_lats[src], node_lons[src],
        #                    node_lats[dst], node_lons[dst]), latlong_dist(node_lats[src], node_lons[src],
        #                    node_lats[dst], node_lons[dst]))
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
    elevations = get_elevations_by_coords(superquery_lats, superquery_lons)
    for i in range(len(elevations)):
        item = float(elevations[i])
        if superquery_keys[i] in edge_heights.keys():
            edge_heights[superquery_keys[i]].append(item)
        else:
            edge_heights[superquery_keys[i]] = [item]

    # for c in random.sample(list(edge_heights.keys()), 20):
    #     print(c, ['%.2f' % float(x) for x in edge_heights[c]])

    print('identifying local and global maxima...')
    local_maxima = set()
    for node in graph.keys():
        if (node_heights[node]
          > max(node_heights[n] for n in graph[node])
        ):
            local_maxima.add(node)

    maxima_by_elevation = sorted(list(local_maxima),
                                 key=lambda n: node_heights[n])
    print('Found', len(maxima_by_elevation), 'local maxima')

    global edge_sim_count
    edge_sim_count = 0
    #return final vel and max vel
    def ride_down_node(src, dest, vel, max_vel=0):
        global edge_sim_count
        edge_sim_count += 1
        dist_internode = latlong_dist(node_latlons[src][0], node_latlons[src][1],
                                      node_latlons[dest][0], node_latlons[dest][1])
        dist = dist_internode / len(edge_heights[(src, dest)])
        edge = edge_heights[(src,dest)]
        for i in range(1, len(edge)):
            dh = edge[i] - edge[i-1]
            vel = acceleration.new_velocity(vel, dh, dist)
            if vel == 0: break
            if vel > max_vel: max_vel = vel
        return vel, max_vel


    def find_all_paths(start, vel, path, max_vel=0):
        path.append(start)
        # print("Path is now ", path)
        # replacedinput
        # print(path)

        if vel == 0:
            # print("Returning single path ", path)
            # replacedinput
            return [path], [max_vel]

        paths = []
        max_vels = []
        for neighbor in graph[start]:
            # print("Exploring neighbor of", start, ": ", neighbor, "from", graph[start])
            # replacedinput
            if neighbor not in path:
                vel, max_vel = ride_down_node(start, neighbor, vel, max_vel)
                new_paths, new_maxes = find_all_paths(neighbor, vel, path[:], max_vel)
                for p in new_paths: paths.append(p)
                max_vels += new_maxes
        # print("returning many paths", paths)
        # replacedinput
        return paths, max_vels


    print('descending...')
    paths = []
    max_vels = []
    # print(maxima_by_elevation)
    for origin in maxima_by_elevation:
        # print("plugging in", origin)
        new_paths, new_maxes = find_all_paths(origin, 1.0, [])
        # print ("Adding ", new_paths)
        # replacedinput
        paths += new_paths
        max_vels += new_maxes

    vels_and_paths = list(zip(max_vels, paths))
    #print(vels_and_paths[0])
    vels_and_paths = sorted(vels_and_paths, reverse=True)

    print('Scanned', edge_sim_count, 'edges')

    # for v, p in vels_and_paths[:5]:
    #     print('max vel', v, 'path', p)

    bestvel, bestpath = vels_and_paths[0]
    print("Best velocity:", bestvel)#, "\nFrom ", vels_and_paths[0])
    # Testing if path is in graph
    #first_path = vels_and_paths[0][1]
    # for i in range(len(p) - 1):
    #     if first_path[i + 1] in graph[first_path[i]]:
    #         print(first_path[i + 1], " is in ", graph[first_path[i]])
    #     else:
    #         print("Oh no! ", first_path[i + 1], " is not in ", graph[first_path[i]])
    #         break
    # end test

    for node in bestpath:
        print('node', node, 'height', node_heights[node])

    import mapview_creator
    coord_path = [node_latlons[n] for n in bestpath]
    mapview_creator.create_map_html(coord_path)



    # with open('path.txt', 'w') as trace_file:
    #     for node in p:
    #         lat = node_lats[node]
    #         lon = node_lons[node]
    #         write_string = str(lat) + ', ' + str(lon) + '\n'
    #         trace_file.write(write_string)


    '''max_vel = 0
    best_stack = list()
    for i in range(100):
        vel = 10.0
        stack = list()
        targeted = set()
        targeted.add(node)
        node = maxima_by_elevation.pop()
        hprev = node_heights[node]
        options = tuple(graph[node] - targeted)
        while len(options) > 0 or len(stack) > 0:
            print('\nat node', node)
            print('stack size', len(stack))

            options = tuple(graph[node] - targeted)
            print(len(options), 'options')

            if len(options) == 0:
                print('out of options')
                if len(stack) > 0:
                    node, vel = stack.pop()
                continue

            stack.append((node, vel))
            target_node = options[-1]
            targeted.add(target_node)
            dist_node = latlong_dist(node_lats[node], node_lons[node],
                            node_lats[target_node], node_lons[target_node])
            dist = dist_node / len(edge_heights[(node, target_node)])
            print('dist is', dist)

            if (node, target_node) in edge_heights.keys():
                for height in edge_heights[(node, target_node)]:
                    print(hprev, height)
                    dh = hprev - height
                    vel = acceleration.new_velocity(vel, dh, dist)
                    print('vel =', vel)
                    hprev = height
                    if vel == 0:
                        node, vel = stack.pop()
                        print('stack size is now', len(stack))
                        break
                    if vel > max_vel:
                        max_vel = vel
                        best_stack = stack[:]

    print("best result:")
    for node, vel in best_stack:
        print(node_lats[node], node_lons[node])'''


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
