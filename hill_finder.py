import subprocess
from map_to_graph import map_to_graph
import math
import osmapi
import os.path
import pickle
from numpy import linspace
import acceleration


# Globals
# Lord forgive me, for I have sinned.
# But really, this is function is supposed to be in an isolated process or thread.
# Is it really worth passing around all of these?
use_stoplights = True
node_heights, node_latlons, graph, edge_heights = dict(), dict(), dict(), dict()
stoplights = set()
map_data = []

def ride_down_node(src, dest, vel, max_vel=0):
    global edge_sim_count
    edge_sim_count += 1
    if vel > max_vel: max_vel = vel
    dist_internode = latlong_dist(node_latlons[src][0], node_latlons[src][1],
                                  node_latlons[dest][0], node_latlons[dest][1])
    dist = dist_internode / len(edge_heights[(src, dest)])
    edge = edge_heights[(src,dest)]
    for i in range(1, len(edge)):
        dh = edge[i] - edge[i-1]
        vel = acceleration.new_velocity(vel, dh, dist)
        if vel > max_vel: max_vel = vel
        if vel == 0: break
    return vel, max_vel

def generate_find_all_paths(
		use_stoplights = True,
        #sort_paths = False,
        cap_paths = False,
        paths_cap = 100,
		use_hill_to_slow_down = False,
		slow_down_to = 3.5
	): # All velocities are in m/s
    def find_all_paths(start, vel, path, max_vel=0):
        path.append(start)
        # print("Path is now ", path)

        if (use_hill_to_slow_down and len(graph[start] - set(path)) == 0 and
            vel > slow_down_to
        ):
            return None

        if (vel == 0
            or (use_stoplights and start in stoplights and len(path) > 1)
            or len(graph[start] - set(path)) == 0
        ):
            # print("Returning single path ", path)
            # replacedinput
            return [path], [max_vel]

        paths = []
        max_vels = []
        neighbors = list(graph[start])
        # print("Trying to sort", len(neighbors))
        # TODO: I'd like to sort everything, but sorting 2/3 element lists seems to be taking forever
        if(len(neighbors) > 3):
            neighbors = sorted(list(graph[start]), key=lambda neighbor: node_heights[neighbor])

        for neighbor in neighbors:
            # print("Exploring neighbor of", start, ": ", neighbor, "from", graph[start])
            # replacedinput
            if neighbor not in path:
                vel, max_vel = ride_down_node(start, neighbor, vel, max_vel)
                new_paths, new_maxes = find_all_paths(neighbor, vel, path[:], max_vel)
                #for p in new_paths: paths.append(p)
                paths += new_paths
                max_vels += new_maxes
        # print("returning many paths", paths)
        # replacedinput
        return paths, max_vels
    return find_all_paths


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
    global map_data
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

def find_hills(mapsize = (-84.4203, 33.7677, -84.3812, 33.7874)):
                        # (left, down, right, up)

    global map_data, node_heights, node_latlons, graph, edge_heights, \
        use_stoplights, stoplights
    api_link = osmapi.OsmApi(#username='evanxq1@gmail.com',
                             #password='hrVQ*DO9aD9q'#,
                             #api="api06.dev.openstreetmap.org"
                             )

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
                pickle.dump(map_data, f)

    except IOError as e:
        print("Couldn't write map data!", e.errorno, e.strerror)

    except: # osmapi.OsmApi.MaximumRetryLimitReachedError:  #TODO: handle errors
        print("Could not get map data!")


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
    for node, node_info in get_node_entries(graph.keys()):
        node_latlons[node] = (float(node_info['data']['lat']),
                              float(node_info['data']['lon']))
        if ('tag' in node_info['data'] and 'highway' in node_info['data']['tag']
                and node_info['data']['tag']['highway'] == 'traffic_signals'
        ):
            stoplights.add(node)

    print(len(stoplights), 'stoplights')

    latlons_items = tuple(node_latlons.items())
    node_iter = (x[0] for x in latlons_items)
    lat_iter = (x[1][0] for x in latlons_items)
    lon_iter = (x[1][1] for x in latlons_items)
    elevations = get_elevations_by_coords(lat_iter, lon_iter)
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
        item = elevations[i]
        if superquery_keys[i] in edge_heights.keys():
            edge_heights[superquery_keys[i]].append(item)
        else:
            edge_heights[superquery_keys[i]] = [item]

    # for c in random.sample(list(edge_heights.keys()), 20):
    #     print(c, ['%.2f' % float(x) for x in edge_heights[c]])

    print('identifying local and global maxima...')
    local_maxima = set()
    for node in graph.keys():
        #print("trying node", node)
        if (node_heights[node]
            > max(node_heights[n] for n in graph[node])
        ):
            local_maxima.add(node)

    #maxima_by_elevation = sorted(list(local_maxima), key=lambda n: node_heights[n])
    print('Found', len(local_maxima), 'local maxima')

    global edge_sim_count
    edge_sim_count = 0
    #return final vel and max vel



    def find_all_paths(start, vel, path, max_vel=0):
        path.append(start)
        # print("Path is now ", path)
        # replacedinput
        # print(path)

        if (vel == 0
            or (use_stoplights and start in stoplights and len(path) > 1)
            or len(graph[start] - set(path)) == 0
        ):
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
                #for p in new_paths: paths.append(p)
                paths += new_paths
                max_vels += new_maxes
        # print("returning many paths", paths)
        # replacedinput
        return paths, max_vels


    print('descending...')
    paths = []
    max_vels = []
    # print(maxima_by_elevation)
    origins = (local_maxima | stoplights) if use_stoplights else local_maxima
    #origins = stoplights
    find_the_paths = generate_find_all_paths()
    originz = sorted(local_maxima)
    for origin in range(len(originz)):
        print("plugging in", origin)
        new_paths, new_maxes = find_the_paths(originz[origin], 1.0, [])
        # print ("Adding ", new_paths)
        # replacedinput
        paths += new_paths
        max_vels += new_maxes

    vels_and_paths = list(zip(max_vels, paths))
    #print(vels_and_paths[0])
    #vels_and_paths = sorted(vels_and_paths, key=lambda vp: len(vp[1]))
    vels_and_paths = sorted(vels_and_paths)
    vels_and_paths = vels_and_paths[::-1]

    print('Simulated', edge_sim_count, 'edges')

    # for v, p in vels_and_paths[:5]:
    #     print('max vel', v, 'path', p)

    bestvel, bestpath = vels_and_paths[0]
    #print("Best velocity:", bestvel)#, "\nFrom ", vels_and_paths[0])
    # Testing if path is in graph
    #first_path = vels_and_paths[0][1]
    # for i in range(len(p) - 1):
    #     if first_path[i + 1] in graph[first_path[i]]:
    #         print(first_path[i + 1], " is in ", graph[first_path[i]])
    #     else:
    #         print("Oh no! ", first_path[i + 1], " is not in ", graph[first_path[i]])
    #         break
    # end test

    for i, vp in enumerate(vels_and_paths[:200]):
        print('%2d. %d -> %f (%d)' % (i, vp[1][0], vp[0], len(vp[1])))

    import mapview_creator
    coord_path = [node_latlons[n] for n in bestpath]
    mapview_creator.create_map_html(coord_path)

    vel = 1.0
    max_vel = 0
    print('Speed at 0 is', vel)
    print('origin is', bestpath[0])
    for i in range(1, len(bestpath)):
        src, dst = bestpath[i-1], bestpath[i]
        vel, max_vel = ride_down_node(src, dst, vel, max_vel)
        print('Speed from', src, 'to', dst, '-', node_heights[src],
                'to', node_heights[dst], 'is', vel)
    print('Max velocity is', max_vel)

if __name__ == '__main__':
    find_hills()


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
