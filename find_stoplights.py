import xml.etree.cElementTree as ET
import overpass
import urllib.request
import requests

def find_stoplights(xml, nodes_to_test): #tuple of ints, iterable of ints
    return_set = set()
    tree = ET.fromstring(xml)
    for node in tree.iterfind("node"):
        if int(node.attrib["id"]) in nodes_to_test:
            for tag in (node.findall("tag[@v='traffic_signals']")):
                return_set.add(int(node.attrib["id"]))
    return return_set
def get_xml(map_bounds):
    url = "http://overpass-api.de/api/interpreter?data=" \
        + urllib.request.pathname2url("(node" + \
            str(map_bounds) + \
            ";<;);out meta;")
    f = open('map.osm', 'w')
    f.write(requests.get(url).text)
    f.close()
    return requests.get(url).text
#get_xml(0)\
# \map_query = "overpass.MapQuery(-84.4085,33.7824,-84.3973,33.7784)"
# map_query = "node(50.745,7.17,50.75,7.18);out;"
# api = overpass.API()
# response = api.Get(map_query)
# print(response)