import matplotlib.pyplot as plt
import numpy as np
import math
import csv
import requests
import math
import os
import urllib
import wget
import zipfile
from collections import defaultdict
import subprocess
import pylab as pl
from matplotlib import collections  as mc
from heapq import heappush, heappop
import overpy

class Node:
    def __init__(self, node_id, lat, lng, is_stoplight, adj,
                 init_energy, init_speed):
        self.node_id = node_id
        self.lat = lat
        self.lng = lng
        self.is_stoplight = is_stoplight
        self.adj = adj
        self.edge_coords = None
        self.edge_elevations = []
        self.edge_work = []
        self.energy = init_energy
        self.speed = init_speed
        self.prev_node = None
        self.next_nodes = set()
        self.path_start = self
    def __lt__(self, other):
        return False
    def __gt__(self, other):
        return False
    def create_adj_node_ptrs(self, nodes):
        self.adj_node_ptrs = list(nodes[adj_node_id] for adj_node_id in self.adj)



g = -9.81 #accelertion due to gravity, m/s
drag_c = .6 #drag coefficient of human body
cross_a = .68 #Cross-sectional area of human body
mass = 80 #kg
frict_c = .03 #Coefficient of friction
api = overpy.Overpass()
datapts_per_degree = 10800
us_urls = ("elevationproductslinks/13secondplots.csv")
ak_urls = ("elevationproductslinks/2secondplotsAK.csv")
mx_ca_urls = ("elevationproductslinks/1secondplots.csv")
def acceleration_due_to_wind(v):
    return -v**2 * (1.225 * drag_c * cross_a) / (2 * mass)


def acceleration_due_to_slope_no_friction(theta):
    return g * math.sin(theta)


def load_csv(file):
    with open(file) as csvfile:
        reader = csv.reader(csvfile, delimiter=',') # , quotechar=''
        headers = next(reader, None)
        URLs = {}
        for r in reader:
            if len(r) > 1:
                bb = r[3]
                label_pairs = bb[2:len(bb)-3].split(",")
                min_y = int(round(float(label_pairs[0].split(':')[1])))
                min_x = int(round(float(label_pairs[1].split(':')[1])))
                url = r[7]
                URLs[(min_y, min_x)] = url
        return URLs


def download_coords(data, country='United States'):
    # TODO check if request is gucci
    # TODO Remove the following block of code in production
    if country == 'United States':
        path_suffix = '_13'
        useful_urls = us_urls
    elif country == 'Alaska':
        useful_urls = ak_urls
    else:
        path_suffix = '_1'
        useful_urls = mx_ca_urls
    urls = load_csv(useful_urls)
    for lat in range(
            math.ceil(float(data['south'])), math.ceil(float(data['north'])) + 1
            # Eg N 87.7 to N 86.
        ):
        for lng in range(
                math.floor(float(data['west'])), math.floor(float(data['east'])) + 1
                ):
            fname = ('grd' + ('n' if lat>0 else 's')
                + str(abs(math.ceil(lat))).zfill(2)
                + ('e' if lng>=0 else 'w')
                + str(abs(math.floor(lng))).zfill(3))
            database_path = ('elevationdata/'
                + fname
                + path_suffix + '/w001001.adf'
                )
            if not os.path.exists(database_path):
                try:
                    url = urls[(lat, lng)]
                    print("downloading " + url + "\n")
                    wget.download(url)
                    print("Done downloading.\n")
                    file_name = url.split('/')[-1]
                    archive = zipfile.ZipFile(file_name)
                    for file in archive.namelist():
                        if file.startswith("grd" + fname[3:] + path_suffix + "/"):
                            archive.extract(file, "elevationdata")
                    os.remove(file_name)
                    print("Extracted")
                except (urllib.error.HTTPError):
                    print("Could not download data for", (lat, lng))
                except KeyError:
                    print("Thing not found in urls: " (lat, lng))


def build_overpass_query(data):
    boundingbox = str((data['south'], data['west'], data['north'], data['east']))
    query = "[out:json];("
    for highway_type in data['allowed_highway_types']:
        query += "way[highway=" + highway_type + "]" + boundingbox + "; "
    query += ");(._;>;); out body;"
    return query


def build_overpass_query_2(data):
    boundingbox = str((data['south'], data['west'], data['north'], data['east']))
    query = "[out:json];way" + boundingbox + "[highway]"
    for highway_type in data['disallowed_highway_types']:
        query += "[highway!=" + highway_type + "]"
    query += ";(._;>;); out body;"
    return query


def overpass_to_graph(query_res, data):
    # TODO support bridges/tunnels
    graph = defaultdict(set)
    id_to_nodes = dict()
    for way in query_res.ways:
        if (
            data['allow_bridges'] or ('bridge' not in way.tags) and
                                     ('tunnel' not in way.tags)
        ):
            road_nodes = way.nodes
            for i in range(len(road_nodes) - 1):
                graph[road_nodes[i].id].add(road_nodes[i+1].id)
                graph[road_nodes[i+1].id].add(road_nodes[i].id)
            for node in road_nodes:
                id_to_nodes[node.id] = node
    return graph, id_to_nodes

def create_node_list_with_elevations(adj_list, id_to_nodes, data):
    nodes = dict()
    node_heights, node_latlons = dict(), dict()
    stoplights = set()
    init_energy = .5 *data['mass'] * data['init_speed'] ** 2
    init_speed = data['init_speed']
    for node_id in adj_list.keys():
        node = id_to_nodes[node_id]
        nodes[node_id] = Node(
            node_id,
            lat=float(node.lat), 
            lng=float(node.lon),
            is_stoplight = 
                ('highway' in node.tags
                    and node.tags['highway'] == 'traffic_signals'
                ),
            adj = list(adj_list[node_id]),
            init_speed = init_speed,
            init_energy = init_energy
        )
    return nodes


def add_edges_return_queries(nodes):
    large_query = set()
    for node_id, node in nodes.items():
        edge_coords = []
        for adj_node in node.adj_node_ptrs:
            # Degrees aren't squares, so this isn't super valid, but it's not important.
            dist_in_degs = np.sqrt((node.lat - adj_node.lat)**2 + (node.lng - adj_node.lng)**2)
            n_steps = max(int(dist_in_degs * datapts_per_degree), 2)
            lat_steps = np.linspace(node.lat, adj_node.lat, num=n_steps, endpoint=True)
            lng_steps = np.linspace(node.lng, adj_node.lng, num=n_steps, endpoint=True)
            coords = list(zip(lat_steps, lng_steps))
            edge_coords.append(coords)
            large_query.update(coords)
        node.edge_coords = edge_coords
    return large_query


# Make sure each node's edges start with the same coordinates
def test_edge_coords_start(nodes):
    for node_id, node in nodes.items():
        first = (node.lat, node.lng)
        for edge in node.edge_coords:
            assert edge[0] == first

# Make sure each node's edges end with the same coordinates 
# as its adjacent node's start with
def test_edge_coords_end(nodes):
    for node_id, node in nodes.items():
        assert len(node.edge_coords) == len(node.adj) == len(node.adj_node_ptrs)
        for i in range(len(node.adj_node_ptrs)):
            assert (node.adj_node_ptrs[i].lat, node.adj_node_ptrs[i].lng) == node.edge_coords[i][-1]


# Possible optimization here: instead of +=ing a bunch of strings, we could use a stringbuilder type object
# def build_query_text(large_query, country="United States"):
#     queries = defaultdict(str)
#     latlng_order = defaultdict(list)
#     for lat_lng in large_query:
#         lat, lng = lat_lng
#         fname = ('grd' + ('n' if lat>0 else 's')
#                  + str(abs(math.ceil(lat))).zfill(2)
#                  + ('e' if lng>=0 else 'w') # lng = 0 block is all east I guess
#                  + str(abs(math.floor(lng))).zfill(3)
#                  )

#         s = str(lng) + ' ' + str(lat) + '\n'
#         queries[fname] += s
#         latlng_order[fname].append(lat_lng)
#     return queries, latlng_order

# "optimized"
def build_query_text(large_query, country="United States"):
    queries_fast = defaultdict(list)
    latlng_order_fast = defaultdict(list)
    for lat_lng in large_query:
        lat, lng = lat_lng
        key = (math.ceil(lat), math.floor(lng))
        s = str(lng) + ' ' + str(lat) + '\n'
        queries_fast[key].append(s)
        latlng_order_fast[key].append(lat_lng)
    queries = dict()
    latlng_order = dict()
    for key, value in queries_fast.items():
        lat, lng = key
        fname = ('grd' + ('n' if lat>0 else 's')
                 + str(abs(lat)).zfill(2)
                 + ('e' if lng>=0 else 'w') # lng = 0 block is all east I guess
                 + str(abs(lng)).zfill(3)
                 )
        queries[fname] = "".join(value)
        latlng_order[fname] = latlng_order_fast[key]
    return queries, latlng_order

def query_elevations(queries, latlng_order, country="United States"):
    points = []
    elevations = []
    for fname in queries.keys():
        if country == 'United States': # TODO deal with AK
            database_path = 'elevationdata/' + fname + '_13/w001001.adf'
        if country == 'Mexico' or country == 'Canada' or country == None:
            # TODO deal with country == None which would be sorta weird
            database_path = 'elevationdata/' + fname + '_1/w001001.adf'
        proc = subprocess.Popen(
            ['gdallocationinfo', database_path, '-valonly', '-geoloc'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            universal_newlines=True
        )
        output, err = proc.communicate(queries[fname])
        elevations += [float(s) for s in output.splitlines()]
        points += latlng_order[fname]
    if len(points) != len(elevations):
        raise Exception("Error querying points: " + str(len(points)) + " points, " + str(len(elevations)) + " elevations")
    ret = dict()
    for i in range(len(points)):
        ret[points[i]] = elevations[i]
    return ret

def set_node_elevations(nodes, elevations):
    for node_id, node in nodes.items():
        for edge in node.edge_coords:
            elevation_list = []
            for coord_pair in edge:
                elevation_list.append(elevations[coord_pair])
            node.edge_elevations.append(elevation_list)
        node.elevation = node.edge_elevations[0][0]

def generate_new_velocity_fn(data):
    c1 = (1.225 * data['drag_c'] * data['cross_a']) / (2 * data['mass'])
    c2 = g * data['frict_c']
    def new_velocity(v0, dh, dist, integrations=1): # for small changes in V; dist is horizontal dist
        if v0 == 0:
            return 0

        theta = math.atan2(dh, dist)
        # Original implementation
    #     a = ((g * math.sin(theta))
    #          - (1.225 * drag_c * cross_a * v0 ** 2) / (2 * mass)
    #          + (g * frict_c * math.cos(theta))
    #         )
        # Prematurely optimized (tm) implementation
        v = v0
        dist_per_i = dist/integrations
        dh_per_i = dh/integrations
        for i in range(integrations):
            a = ((g * math.sin(theta))
                 - v ** 2 * c1
                 + math.cos(theta) * c2
                )
                # Total Acceleration = grav, air resistance, rolling friction resistance
                # Assumes final velocity causes about the amount of air resistance as
                #   inital velocity
            vel_sqr = 2 * a * math.sqrt(dist_per_i**2 + dh_per_i**2) + v ** 2
            if vel_sqr > 0:
                v = math.sqrt(vel_sqr)
            else:
                return 0
        return v
    return new_velocity

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

def generate_calculate_work(approx_frict_c, mass):
    def calculate_work(dist, dh, approx_frict_c, mass): # Work done by gravity
        theta = math.atan2(dh, dist)
        a = ((g * math.sin(theta))
         + math.cos(theta) * g * approx_frict_c
        )
        real_dist = math.sqrt(dist**2 + dh**2)
        return real_dist * a * mass
    return calculate_work

def find_work_all_edges(sorted_nodes, data):
    calculate_work = generate_calculate_work(data['approx_frict_c'], data['mass'])
    approx_frict_c = data['approx_frict_c']
    mass = data['mass']
    for node in sorted_nodes:
        node.edge_work = []
        for i in range(len(node.adj)):
            edge_coords = node.edge_coords[i]
            edge_elevations = node.edge_elevations[i]
            work = 0
            horiz_dist = latlong_dist(edge_coords[0][0], edge_coords[0][1], 
                                      edge_coords[1][0], edge_coords[1][1])
            for j in range(len(edge_coords) - 1): 
                dh = edge_elevations[j+1] - edge_elevations[j]
                # horiz dist is actually same for each part of an edge
                #  horiz_dist = latlong_dist(edge_coords[j][0], edge_coords[j][1], edge_coords[j+1][0], edge_coords[j+1][1])
                work += calculate_work(horiz_dist, dh, approx_frict_c, mass)
            node.edge_work.append(work)


def graph_paths(sorted_nodes):
    lines = []
    colors = []
    max_lat = -90
    min_lat = 90
    max_lng = -180
    min_lng = 180
    done = set()
    for node in sorted_nodes:
        max_lat = max(node.lat, max_lat)
        min_lat = min(node.lat, min_lat)
        max_lng = max(node.lng, max_lng)
        min_lng = min(node.lng, min_lng)
        for adj in node.next_nodes:
            if ((adj.lng,adj.lat), (node.lng, node.lat)) not in done:
                lines.append([(node.lng, node.lat),(adj.lng,adj.lat)])
                done.add(((node.lng, node.lat),(adj.lng,adj.lat)))
    colors = []
    for line in lines:
        beginning, end = line
        x1, y1 = beginning
        x2, y2 = end
        angle = math.atan2(x2-x1, y2-y1)
        colors.append((math.cos(angle) * .5 + .5,  math.sin(angle) * .5 + .5, 0, 1))
    lc = mc.LineCollection(lines, colors=colors, linewidths=1)
    fig, ax = pl.subplots(figsize=(16,10))
    ax.add_collection(lc)
    # ax.autoscale()
    # ax.margins(0.001)
    ax.set_xlim(min_lng, max_lng)
    ax.set_ylim(min_lat, max_lat)
    plt.show()

def generate_compass():
    lines = []
    for x in [-1, -.5, 0, .5, 1]:
        for y in [-1, -.5, 0, .5, 1]:
            if (x, y) != (0,0):
                lines.append([(0,0), ((x,y))])
    colors = []
    for line in lines:
        beginning, end = line
        x1, y1 = beginning
        x2, y2 = end
        angle = math.atan2(x2-x1, y2-y1)
        colors.append((math.cos(angle) * .5 + .5,  math.sin(angle) * .5 + .5, 0, 1))
    lc = mc.LineCollection(lines, colors=colors, linewidths=1)
    fig, ax = pl.subplots()
    ax.add_collection(lc)
    ax.autoscale()
    # ax.margins(0.001)
    plt.show()


def algo_1(sorted_nodes):
    edges_explored = 0
    for top_node in sorted_nodes:
        if top_node.prev_node != None: # Already part of a path
            continue
        need_to_explore = set([top_node])
        heap = [(-top_node.elevation, top_node)]
        while need_to_explore:
            _, node = heappop(heap)
            if node not in need_to_explore:
                continue
            need_to_explore.remove(node)
            node_energy = node.energy
            for i in range(len(node.adj)):
                adj = node.adj_node_ptrs[i]
                edge_work = node.edge_work[i]
                if edge_work + node_energy > adj.energy:
                    adj.energy = edge_work + node_energy
                    if adj.prev_node is not None:
                        prev = adj.prev_node
                        next_nodes = prev.next_nodes
                        next_nodes.remove(adj)
                    adj.prev_node = node
                    node.next_nodes.add(adj)
                    adj.path_start = top_node
                    need_to_explore.add(adj)
                    heappush(heap, (-adj.elevation, adj))
                edges_explored += 1
    return edges_explored

# Same thing, but use a normal queue instead of a priority queue
def algo_2(sorted_nodes):
    edges_explored = 0
    for top_node in sorted_nodes:
        if top_node.prev_node != None: # Already part of a path
            continue
        need_to_explore = set([top_node])
        q = deque()
        q.append(top_node)
        while need_to_explore:
            node = q.popleft()
            if node not in need_to_explore:
                continue
            need_to_explore.remove(node)
            node_energy = node.energy
            for i in range(len(node.adj)):
                adj = node.adj_node_ptrs[i]
                edge_work = node.edge_work[i]
                # For air resistance version, check first if 
                #      (node.speed > adj.speed or node.elevation > adj.elevaton)
                # then ride down nodes
                if edge_work + node_energy > adj.energy:
                    adj.energy = edge_work + node_energy
                    if adj.prev_node is not None:
                        prev = adj.prev_node
                        next_nodes = prev.next_nodes
                        next_nodes.remove(adj)
                    adj.prev_node = node
                    node.next_nodes.add(adj)
                    adj.path_start = top_node
                    need_to_explore.add(adj)
                    q.append(adj)
                edges_explored += 1
    return edges_explored


def test_nodes(sorted_nodes):
    for node in sorted_nodes:
        for adj in node.adj_node_ptrs:
            if adj in node.next_nodes:
                assert adj.prev_node == node
            else:
                assert adj.prev_node != node


def ride_down_node(v0, elevations, locs, new_velocity_fn, integrations=1):
    dist = latlong_dist(locs[0][0], locs[0][1], locs[1][0], locs[1][1])
    v = v0          
    for i in range(len(elevations) - 1):
        v = new_velocity_fn(v, elevations[i+1] - elevations[i], dist, integrations)
        if v == 0:
            break
    return v

def test_node_starts(sorted_nodes):
    for node in sorted_nodes:
        if node.path_start == node:
            assert not node.prev_node


def simulate_paths(sorted_nodes, data, new_velocity_fn):
    integrations = data['integrations']
    for node in sorted_nodes:
        if node.path_start == node:
            stack = [node]
            for i, adj in enumerate(node.next_nodes):
                new_speed = ride_down_node(node.speed, 
                                           node.edge_elevations[i], 
                                           node.edge_coords[i],
                                           new_velocity_fn,
                                           integrations)
                if new_speed > adj.speed:
                    adj.speed = new_speed
                else:
                    adj.prev = None
                    adj.path_start = adj


# Use a queue to decide which nodes to ride down
from collections import deque
def algo_2_with_air(sorted_nodes, data, new_velocity_fn):
    integrations = data['integrations']
    edges_ridden = 0
    edges_updated = 0
    need_to_explore = set(sorted_nodes)
    q = deque(sorted_nodes)
    while need_to_explore:
        node = q.popleft()
        if node not in need_to_explore:
            continue
        need_to_explore.remove(node)
        node_energy = node.energy
        for i in range(len(node.adj)):
            adj = node.adj_node_ptrs[i]
            if node.speed > adj.speed or node.elevation > adj.elevation:
                new_speed = ride_down_node(node.speed, 
                                           node.edge_elevations[i], 
                                           node.edge_coords[i],
                                           new_velocity_fn,
                                           integrations)
                edges_ridden += 1
                if new_speed > adj.speed:
                    adj.speed = new_speed
                    if adj.prev_node is not None:
                        adj.prev_node.next_nodes.remove(adj)
                    adj.prev_node = node
                    node.next_nodes.add(adj)
                    adj.path_start = node.path_start
#                     TODO Add Back
                    need_to_explore.add(adj)
                    q.append(adj)
                    edges_updated += 1
    return edges_updated, edges_ridden

def generate_perfect_graph(data):
    download_coords(data)
    # Change API URL this way
    # api.url = "http://overpass-api.de/api/interpreter"
    query_res = api.query(build_overpass_query_2(data))
    adj_list, id_to_nodes = overpass_to_graph(query_res, data)
    nodes = create_node_list_with_elevations(adj_list, id_to_nodes, data)
    for node_id, node in nodes.items():
        node.create_adj_node_ptrs(nodes)
    large_query = add_edges_return_queries(nodes)
    # test_edge_coords_start(nodes)
    # test_edge_coords_end(nodes)
    queries, latlng_order = build_query_text(large_query, country="United States")
    elevations = query_elevations(queries, latlng_order, country="United States")
    set_node_elevations(nodes, elevations)
    sorted_nodes = sorted(nodes.values(), key=lambda n: -n.elevation)
    new_velocity_fn = generate_new_velocity_fn(data)
    find_work_all_edges(sorted_nodes, data)
    # generate_compass()
    algo_2(sorted_nodes)
    # graph_paths(sorted_nodes)
    simulate_paths(sorted_nodes, data, new_velocity_fn)
    # test_node_starts(sorted_nodes)
    algo_2_with_air(sorted_nodes, data, new_velocity_fn)
    return sorted_nodes

def generate_perfect_graph_timed(data):
    from time import time
    orig = time()
    print('hi')
    download_coords(data)
    t1 = time()
    print('download_coords', t1-orig)
    # Change API URL this way
    # api.url = "http://overpass-api.de/api/interpreter"
    query_res = api.query(build_overpass_query_2(data))
    t2 = time()
    print('query_res', t2-t1)
    adj_list, id_to_nodes = overpass_to_graph(query_res, data)
    t3 = time()
    print('overpass_to_graph', t3-t2)
    nodes = create_node_list_with_elevations(adj_list, id_to_nodes, data)
    t4 = time()
    print('create_node_list_with_elevations', t4-t3)
    for node_id, node in nodes.items():
        node.create_adj_node_ptrs(nodes)
    t5 = time()
    print('create_adj_node_ptrs', t5-t4)
    large_query = add_edges_return_queries(nodes)
    t6 = time()
    print('add_edges_return_queries', t6-t5)
    # test_edge_coords_start(nodes)
    # test_edge_coords_end(nodes)
    queries, latlng_order = build_query_text(large_query, country="United States")
    t7 = time()
    print('build_query_text', t7-t6)
    elevations = query_elevations(queries, latlng_order, country="United States")
    t8 = time()
    print('query_elevations', t8-t7)
    set_node_elevations(nodes, elevations)
    t9 = time()
    print('set_node_elevations', t9-t8)
    sorted_nodes = sorted(nodes.values(), key=lambda n: -n.elevation)
    t10 = time()
    print('sorted_nodes', t10-t9)
    new_velocity_fn = generate_new_velocity_fn(data)
    t11 = time()
    print('generate_new_velocity_fn', t11-t10)
    find_work_all_edges(sorted_nodes, data)
    t12 = time()
    print('find_work_all_edges', t12-t11)
    # generate_compass()
    algo_2(sorted_nodes)
    t13 = time()
    print('algo_2', t13-t12)
    # graph_paths(sorted_nodes)
    simulate_paths(sorted_nodes, data, new_velocity_fn)
    t14 = time()
    print('simulate_paths', t14-t13)
    # test_node_starts(sorted_nodes)
    algo_2_with_air(sorted_nodes, data, new_velocity_fn)
    t15 = time()
    print('algo_2_with_air', t15-t14)
    print('total', t15-orig)
    generate_compass()
    graph_paths(sorted_nodes)
    return sorted_nodes


if __name__ == "__main__":
    # data = {
    #     'north': 33.7874, 
    #     'west':  -84.4203, 
    #     'south': 33.7677,
    #     'east':  -84.3812, 
    # }
    # ABQ
    data = {
        'north': 35.206225, 
        'west':  -106.650861, 
        'south': 35.059084,
        'east':   -106.480712, 
    }
    data['allowed_highway_types'] = {'primary','primary_link', 'secondary','secondary_link',
                             'tertiary', 'tertiary_link', 'unclassified', 'residential',
                            'living_street', 'cycleway'}
    data['disallowed_highway_types'] = [
        'motorway',
        'motorway_link',
        'trunk', 
        'trunk_link',
        'service',
        'pedestrian',
        'track',
        'bus_guideway',
        'escape',
        'raceway',
        'road', #unkown
        'footway',
        'bridleway',
        'steps',
        'path', # nonspecific, often trails
        'construction',
        'disused'
    ]
    data['mass'] = 80 #kg
    data['init_speed'] = 1.0
    data['respect_stoplights'] = True
    data['allow_bridges'] = False

    data['drag_c'] = .6 #drag coefficient of human body
    data['cross_a'] = .68 #Cross-sectional area of human body
    data['mass'] = 80 #kg
    data['frict_c'] = .03 #Coefficient of friction
    data['approx_frict_c'] = .03
    data['integrations'] = 1
    # test_nodes(sorted_nodes)
    # import cProfile
    generate_perfect_graph_timed(data)
    # cProfile.run('generate_perfect_graph(data)')