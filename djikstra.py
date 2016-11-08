class Djikstra():
    'Class for initializing '
    def __init__(self):
        pass

    def gen_routing_table(self, source_router, routers):
        table = {}
        previous = {}
        dist = {}
        vertex_set = []
        for router in routers:
            previous[router] = None
            dist[router] = INF
            vertex_set.append(router)
            for host in router.get_hosts():
                previous[host] = None
                dist[host] = INF
                vertex_set.append(host)

        vertex_set_copy = vertex_set[:]
        dist[source_router] = 0
        while vertex_set:
            index_of_min = index_of_min(vertex_set, dist)
            min_node = vertex_set.pop(index_of_min)
            for link in min_node.get_links():
                endpoints = link.get_endpoints()
                dest = endpoints[0] if endpoints[1] == min_node else endpoints[1]
                alt = dist[min_node] + link.get_weight()
                if alt < dist[dest]:
                    dist[dest] = alt 
                    prev[dest] = min_node
        for node in vertex_set_copy:
            table[node] = get_next(source_router, prev, node)
        return table 

    def index_of_min(self, vertex_set, dist):
        best_index = 0
        for i in range(len(vertex_set)):
            if dist[vertex_set[i]] < dist[vertex_set[best_index]]:
                best_index = i
        return best_index

    def get_next(self, source_router, prev, node):
        while prev[node] != source_router:
            node = prev[node]
        return node
