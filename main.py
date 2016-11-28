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
from event_processor import *
from graph import *
import matplotlib.pyplot as plt 

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
        assert src in hosts or src in routers, 'Endpoint is invalid'
        assert dst in hosts or dst in routers, 'Endpoint is invalid'

        # Create two way links
        src_node = hosts[src] if src in hosts else routers[src]
        dst_node = hosts[dst] if dst in hosts else routers[dst]
        l = Link(link_id, buf, prop_time, trans_time, congestion, direction)
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

def initialize_packets(flows, hosts):
    for key in flows:
        event_list = []
        count = 0
        for packet in flows[key].gen_packets():
            count += 1
            hosts[flows[key].get_src()].insert_packet(packet)

            # if count == 1000:
            #     break


if __name__ == '__main__':
    # Process input
    hosts, routers, links, flows = process_input()

    # print_dict(hosts, 'HOSTS')
    # print_dict(routers, 'ROUTERS')
    # print_dict(links, 'LINKS')
    # print_dict(flows, 'FLOWS')

    # Create routing table
    d = Djikstra()
    d.update_routing_table(routers.values())

    initialize_packets(flows, hosts)

    # Update every packets next hop location
    for host_id in hosts:
        link = hosts[host_id].get_link()
        q_len = hosts[host_id].q.qsize()
        for x in range(q_len):
            x = hosts[host_id].q.get()
            x.set_curr_loc(link.get_link_endpoint(hosts[host_id]).get_ip())
            hosts[host_id].q.put(x)
        assert hosts[host_id].q.qsize() == q_len



    # Fills up all the link's buffers connected to the host 
    for host_id in hosts:
        link = hosts[host_id].get_link()
        # Load window number of packets from host queue to buffer
        while hosts[host_id].get_window_count() < hosts[host_id].get_window_size():
            curr_packet = hosts[host_id].remove_packet()
            if curr_packet != None:
                if link.insert_into_buffer(curr_packet, curr_packet.get_capacity()):
                    hosts[host_id].set_window_count(hosts[host_id].get_window_count()+1)
                    curr_src = hosts[curr_packet.get_src()]
                    next_dest = link.get_link_endpoint(curr_src)
                    # curr_packet.set_curr_loc(next_dest.get_ip())

                    if len(link.packet_queue) == 1:
                        create_packet_received_event(curr_packet.get_init_time(), curr_packet, link, curr_src.get_ip(), next_dest.get_ip())
                    create_timeout_event(TIMEOUT_VAL + curr_packet.get_init_time(), curr_packet, curr_packet.get_init_time())
                else:
                    # Put packet back into the host since buffer is full
                    hosts[host_id].insert_packet(curr_packet)
                    break
            else:
                break

    create_dynamic_routing_event(ROUTING_INTERVAL)



    global_time = 0
    acknowledged_packets = {}
    pck_graph = []
    dropped_packets = []
    pck_drop_graph = []
    window_size_list = []

    counter = 0

    # Continuously pull events from the priority queue
    while eq.qsize() != 0:
        print 'Queue size: ', eq.qsize()
        print '-' * 80
        t, event_top = eq.get()
        pck_graph.append(pck_tot_buffers(t, links))
        pck_drop_graph.append(drop_packets(t, links))
        assert t != None
        global_time = t
        # print t, event_top

        assert event_top.get_type() != LINK_TO_ENDPOINT

        # Host or Router receives a packet
        if event_top.get_type() == PACKET_RECEIVED:
            process_packet_received_event(event_top, global_time, links, routers, 
                hosts, dropped_packets, acknowledged_packets, window_size_list)
        elif event_top.get_type() == TIMEOUT_EVENT:
            process_timeout_event(event_top, global_time, hosts, dropped_packets, 
                acknowledged_packets)
        elif event_top.get_type() == DYNAMIC_ROUTING:
            if eq.qsize() == 0:
                break
            # create_dynamic_routing_event(event_top.get_initial_time() + ROUTING_INTERVAL)
            for r in routers:
                routers[r].reset_weight_table()

            # Creates routing packet for each host and adds to queue
            for host_id in hosts:
                link = hosts[host_id].get_link()
                routing_pkt = Packet(ROUTER_PACKET, link.get_weight(), host_id, None, link.get_link_endpoint(hosts[host_id]).get_ip(), None)
                dest = link.get_link_endpoint(hosts[host_id])

                insert_routing_packet_into_buffer(routing_pkt, link, dropped_packets, global_time, dest)
                # create_routing_packet_received_event(global_time, routing_pkt, link, host_id, dest):

            create_dynamic_routing_event(global_time + ROUTING_INTERVAL)

        elif event_top.get_type() == ROUTING_PACKET_RECEIVED:
            process_routing_packet_received_event(event_top, hosts, links, dropped_packets, global_time, routers)

        else:
            assert False


    for l in links:
        assert len(links[l].packet_queue) == 0

    print_dict(hosts, 'HOSTS')
    print_dict(routers, 'ROUTERS')
    print_dict(links, 'LINKS')
    print_dict(flows, 'FLOWS')
    print 'Completed everything '
    # print len(dropped_packets)
    # # print(pck_graph)
    print window_size_list
    graph_pck_buf(pck_graph)
    graph_window_size(window_size_list)
    # points = format_drop_to_rate(pck_drop_graph)
    # graph(points)
    # graph_pck_drop_rate(pck_drop_graph)
    # graph_pck_buf(pck_graph)

