from constants import *
from router import *
from link import *
from host import *
from flow import *
from utilities import *
from pprint import pprint
from djikstra import *

from eventqueue import *
from event import *

def process_input():
    host_f = open(HOST_FILE, 'r')
    host_f.readline()
    hosts = {}
    for line in host_f:
        hosts[line.strip()] = Host(line.strip())

    router_f = open(ROUTER_FILE, 'r')
    router_f.readline()
    routers = {}
    for line in router_f:
        routers[line.strip()] = Router(line.strip())

    link_f = open(LINK_FILE, 'r')
    link_f.readline()
    links = {}
    for line in link_f:
        attrs = line.strip().split('|')
        link_id, src, dst, trans_time, prop_time, buf = attrs
        congestion = None
        direction = None
        length = None
        assert src in hosts or src in routers, 'Endpoint is invalid'
        assert dst in hosts or dst in routers, 'Endpoint is invalid'

        # Create two way links
        src_node = hosts[src] if src in hosts else routers[src]
        dst_node = hosts[dst] if dst in hosts else routers[dst]
        l = Link(link_id, length, buf, prop_time, trans_time, congestion, direction)
        l.connect(src_node, dst_node)
        links[link_id] = l

        # Set up links for routers and hosts
        if src in routers:
            routers[src].add_link(l)
        else:
            hosts[src].attach_link(l)
        if dst in routers:
            routers[dst].add_link(l)
        else:
            hosts[dst].attach_link(l)

    flow_f = open(FLOW_FILE, 'r')
    flow_f.readline()
    flows = {}
    for line in flow_f:
        flow_id, src, dst, data_amt, flow_start = line.strip().split('|')
        flows[flow_id] = Flow(flow_id, data_amt, src, dst, flow_start)

    return hosts, routers, links, flows

def create_events(flows):
    """ Returns map of flow_id and events. """
    event_data = {}
    for key in flows.keys():
        event_list = []
        for packet in flows[key].gen_packets()[0]:
            newEvent = Event(ENQUEUE_EVENT, 0, flows[key].get_src(), flows[key].get_dest(), flows[key], packet)
            event_list.append(newEvent)
        event_data[key] = event_list
    return event_data


if __name__ == '__main__':
    hosts, routers, links, flows = process_input()

    print_dict(hosts, 'HOSTS')
    print_dict(routers, 'ROUTERS')
    print_dict(links, 'LINKS')
    print_dict(flows, 'FLOWS')

    # Create events from the flows
    flow_events_map = create_events(flows)

    d = Djikstra()
    d.update_routing_table(routers.values())
    print_dict(routers, 'ROUTERS')
    # pprint(d.gen_routing_table(routers['R1'], routers.values()))
    # d.gen_routing_table(routers['R1'], routers.values())
    # print routers
    # def gen_routing_table(self, source_router, routers):

