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
from packet import *

def get_base_RTT(hosts):
    base_RTT_table = {}
    for h1 in hosts.values():
        for h2 in hosts.values():
            if h1 != h2:
                tup = (h1,h2)
                if tup not in base_RTT_table:
                    time = 0
                    link_adj = h1.get_link()
                    time += link_adj.get_prop_time() + MESSAGE_SIZE/link_adj.get_trans_time()
                    dest = link_adj.get_link_endpoint(h1)
                    print h1.get_ip()
                    print h2.get_ip()
                    print "Dest: ", dest
                    while dest != h2: 
                        new_dest = dest.get_routing_table()[h2] 
                        link_adj = dest.get_link_for_dest(new_dest)
                        time += link_adj.get_prop_time() + MESSAGE_SIZE/link_adj.get_trans_time()
                        dest = new_dest
                    time *= 2
                    base_RTT_table[tup] = time 
    return base_RTT_table


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
        flow_id, src, dst, data_amt, flow_start, is_fast = line.strip().split('|')
        flows[flow_id] = Flow(flow_id, data_amt, src, dst, flow_start, is_fast)

    return hosts, routers, links, flows

def initialize_packets(flows, hosts):
    for key in flows:
        event_list = []
        count = 0
        curr_host = hosts[flows[key].get_src()]
        curr_host.set_tcp(flows[key].get_tcp())
        curr_host.set_flow_id(key)

        for packet in flows[key].gen_packets():
            count += 1
            packet.set_packet_id(count)
            curr_host.insert_packet(packet)

            if count == 5000:
                break

def initialize_flow_RTT(hosts):
    '''
    Sets each hosts base RTT to be infinity
    '''
    base_rtt_table = get_base_RTT(hosts)
    print base_rtt_table
    for host in hosts:
        hosts[host].set_base_RTT(float('inf'))

def store_packet_delay(packet_delay_dict, hosts, global_time):
    for host in hosts:
        if hosts[host].get_flow_id() is not None:
            packet_delay_dict[hosts[host].get_flow_id()].append((global_time, hosts[host].get_last_RTT()))

def store_flow_rate(flow_rate_dict, hosts, global_time):
    for host in hosts:
        if hosts[host].get_flow_id() is not None:
            prev = 0
            if len(flow_rate_dict[hosts[host].get_flow_id()]) != 0:
                prev = flows[hosts[host].get_flow_id()].prev

            diff = ((hosts[host].get_bytes_received() - prev) * 8.0 / 10**6) / float(GRAPH_EVENT_INTERVAL)
            # diff = ((hosts[host].get_bytes_received() - prev) / (10 ** 6 / 8.0)) / global_time
            print 'Diff: ', global_time, diff, hosts[host].get_bytes_received(), prev
            flow_rate_dict[hosts[host].get_flow_id()].append((global_time, diff))
            flows[hosts[host].get_flow_id()].prev = hosts[host].get_bytes_received()

    # print 'Diff '

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
    create_graph_event(GRAPH_EVENT_INTERVAL)

    global_time = 0
    acknowledged_packets = {}
    pck_graph = []
    dropped_packets = []
    pck_drop_graph = []
    window_size_dict = {}
    packet_delay_dict = {}
    flow_rate_dict = {}


    initialize_flow_RTT(hosts)
    for host in hosts:
        if hosts[host].get_flow_id() is not None:
            window_size_dict[hosts[host].get_flow_id()] = []
            packet_delay_dict[hosts[host].get_flow_id()] = []
            flow_rate_dict[hosts[host].get_flow_id()] = []
        if hosts[host].get_tcp():
            create_update_window_event(hosts[host], PERIODIC_FAST_INTERVAL)
    

    # Continuously pull events from the priority queue
    while eq.qsize() != 0:
        print 'Queue size: ', eq.qsize()
        print '-' * 80
        a= eq.get()
        print 'exp_packe This is a: ', a
        t, event_top = a
        assert t != None
        global_time = t


        pck_graph.append(pck_tot_buffers(t, links))
        pck_drop_graph.append(drop_packets(t, links))
        # print t, event_top
        store_packet_delay(packet_delay_dict, hosts, global_time)
        # store_flow_rate(flow_rate_dict, hosts, global_time)

        assert event_top.get_type() != LINK_TO_ENDPOINT

        # Host or Router receives a packet
        if event_top.get_type() == PACKET_RECEIVED:
            process_packet_received_event(event_top, global_time, links, routers, 
                hosts, dropped_packets, acknowledged_packets, window_size_dict)
        elif event_top.get_type() == TIMEOUT_EVENT:
            process_timeout_event(event_top, global_time, hosts, dropped_packets, 
                acknowledged_packets)
        elif event_top.get_type() == DYNAMIC_ROUTING:
            if eq.qsize() == 0:
                break
            elif eq.qsize() == 1:
                t, event_top = eq.get()
                if event_top.get_type() == UPDATE_WINDOW:
                    break
                else:
                    eq.put((t, event_top))
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
        elif event_top.get_type() == GRAPH_EVENT:
            # Hackish solution to stop the program
            if eq.qsize() < 5:
                break

            store_flow_rate(flow_rate_dict, hosts, global_time)
            create_graph_event(global_time + GRAPH_EVENT_INTERVAL)

        elif event_top.get_type() == UPDATE_WINDOW:
            # Hackish solution to stop the program
            if eq.qsize() < 5:
                break

            # if eq.qsize() == 0:
            #     break
            # elif eq.qsize() == 1:
            #     t, event_top = eq.get()
            #     if event_top.get_type() == DYNAMIC_ROUTING:
            #         break
            #     else:
            #         eq.put(t, event_top)
            curr_host = hosts[event_top.get_src()]
            assert curr_host.is_fast
            # Update window size 
            # if curr_host in window_size_dict:
            w = curr_host.get_window_size()
            curr_host.set_window_size(min(2 * w, (1 - GAMMA) * w + GAMMA * (curr_host.get_base_RTT() / curr_host.get_last_RTT() * w + ALPHA)))
            print "changing window size:", curr_host.get_window_size()
            window_size_dict[curr_host.get_flow_id()].append((global_time, curr_host.get_window_size()))

            create_update_window_event(curr_host, global_time + PERIODIC_FAST_INTERVAL)

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

    # print window_size_dict
    # print flow_rate_dict
    graph_flow_rate(flow_rate_dict)
    # graph_pck_buf(pck_graph)
    graph_window_size(window_size_dict)
    # graph_packet_delay(packet_delay_dict)

    # graph_pck_buf(pck_graph)
    # graph_window_size(window_size_dict)
    # points = format_drop_to_rate(pck_drop_graph)
    # graph(points)
    # print(pck_drop_graph)
    # graph_pck_drop_rate(pck_drop_graph)
    # graph_pck_buf(pck_graph)

