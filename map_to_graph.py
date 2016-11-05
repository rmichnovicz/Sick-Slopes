#import itertools

def map_to_graph(map_data):

    way_lists = list()
    way_sets = list()
    for entry in map_data:
        if (entry['type'] == 'way'
                and 'data' in entry.keys()
                and 'tag' in entry['data'].keys()
                and 'highway' in entry['data']['tag'].keys()
        ):
            way = entry['data']['nd']
            way_lists.append(way)
            way_sets.append(frozenset(way))

    '''for ndset1,ndset2 in itertools.combinations(way_sets, 2):
        intersect = ndset1 & ndset2
        if len(intersect) > 0:
            print(ndset1, ndset2)
            print(intersect)
            print()'''


    graph = dict()

    # node is the current node, link is the node to link to
    def graph_add(cur, link):
        if cur in graph.keys():
            graph[cur].add(link)
        else:
            graph[cur] = {link}

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

    # for node in graph.keys():
    #     print(node, graph[node])

    return graph