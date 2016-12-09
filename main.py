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
from event_creator import *
from network_system import *

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
            flow_rate_dict[hosts[host].get_flow_id()].append((global_time, diff))
            flows[hosts[host].get_flow_id()].prev = hosts[host].get_bytes_received()

def store_link_rate(link_rate_dict, links, global_time):
    for l in link_rate_dict:
        prev = 0
        if len(link_rate_dict[l]) != 0:
            prev = links[l].prev

        diff = ((links[l].get_packet_size_sent() - prev) * 8.0 / 10**6) / float(GRAPH_EVENT_INTERVAL)
        link_rate_dict[l].append((global_time, diff))
        links[l].prev = links[l].get_packet_size_sent()


def store_packet_loss(packet_loss_dict, links, global_time):
    for link_id, l in links.iteritems():
        packet_loss_dict[link_id].append((global_time, l.get_drop_packets()))


if __name__ == '__main__':
    network = NetworkSystem()
    hosts, routers, links, flows = network.retrieve_system()
    network.update_routing_table()
    network.initialize_packets()

    print_dict(hosts, 'HOSTS')
    print_dict(routers, 'ROUTERS')
    print_dict(links, 'LINKS')
    print_dict(flows, 'FLOWS')

    # Update every packets next hop location
    network.init_packet_hop()
    # Populate all the link buffers with packets from hosts
    network.populate_link_buffers()

    # Create timeout events for all the packets in the buffer and creates
    # Create a packet received event for first packet in buffer (taking a packet
    # out of a buffer means that we can include a packet from the host queue or
    # maybe the router queue)
    network.create_packet_events()
    # Initialize the flow RTT
    network.initialize_flow_RTT()

    eq = network.get_system_queue()
    ec = network.get_event_creator()
    ep = network.get_event_processor()

    ec.create_dynamic_routing_event(ROUTING_INTERVAL)
    ec.create_graph_event(GRAPH_EVENT_INTERVAL)

    global_time = 0
    acknowledged_packets = {}
    pck_graph_dict = {}
    dropped_packets = []
    pck_drop_graph = []
    window_size_dict = {}
    packet_delay_dict = {}
    flow_rate_dict = {}
    packet_loss_dict = {}
    link_rate_dict = {}

    # Initialize graph dictionaries
    for _, h in hosts.iteritems():
        if h.get_flow_id() is not None:
            f_id = h.get_flow_id()
            window_size_dict[f_id] = []
            packet_delay_dict[f_id] = []
            flow_rate_dict[f_id] = []
            ec.create_update_window_event(h, PERIODIC_FAST_INTERVAL)
    
    for l in links:
        packet_loss_dict[l] = []
        link_rate_dict[l] = []


    done = 0
    # Continuously pull events from the priority queue
    while eq.qsize() != 0 and not done:
        print 'Host Window Queue size: ', eq.qsize()
        t, event_top = eq.get()
        assert t != None
        assert t >= global_time
        global_time = t
        event_type = event_top.get_type()


        pck_tot_buffers(pck_graph_dict, t, links)
        store_link_rate(link_rate_dict, links, global_time)

        # Host or Router receives a packet
        if event_type == PACKET_RECEIVED:
            ep.process_packet_received_event(event_top, global_time, links, routers, 
                hosts, dropped_packets, acknowledged_packets, window_size_dict, network)
        elif event_type == TIMEOUT_EVENT:
            ep.process_timeout_event(event_top, global_time, hosts, dropped_packets, 
                acknowledged_packets)
        elif event_type == DYNAMIC_ROUTING:
            for r in routers:
                routers[r].reset_weight_table()

            # Creates routing packet for each host and adds to queue
            for _, h in hosts.iteritems():
                l = h.get_link()
                dest = l.get_link_endpoint(h)
                routing_pkt = Packet(ROUTER_PACKET, l.get_weight(), h.get_ip(), None, l.get_link_endpoint(h).get_ip(), None)
                
                # Insert the routing packets into the buffer
                ep.insert_packet_into_buffer(l, h, dest, routing_pkt, dropped_packets, global_time)

            ec.create_dynamic_routing_event(global_time + ROUTING_INTERVAL)

        elif event_type == REMOVE_FROM_BUFFER:
            ep.process_remove_from_buffer_event(event_top, global_time)

        elif event_type == ROUTING_PACKET_RECEIVED:
            ep.process_routing_packet_received_event(event_top, hosts, links, dropped_packets, global_time, routers)
        elif event_type == GRAPH_EVENT:
            store_flow_rate(flow_rate_dict, hosts, global_time)
            store_packet_delay(packet_delay_dict, hosts, global_time)
            store_packet_loss(packet_loss_dict, links, global_time)
            ec.create_graph_event(global_time + GRAPH_EVENT_INTERVAL)

        elif event_type == UPDATE_WINDOW:
            curr_host = hosts[event_top.get_src()]
            if curr_host.get_is_fast():
                assert curr_host.is_fast
                # Update window size 
                # if curr_host in window_size_dict:
                w = curr_host.get_window_size()
                curr_host.set_window_size(min(2 * w, (1 - GAMMA) * w + GAMMA * (curr_host.get_base_RTT() / curr_host.get_last_RTT() * w + ALPHA)))
                window_size_dict[curr_host.get_flow_id()].append((global_time, curr_host.get_window_size()))
            elif curr_host.get_is_cubic():
                K = (curr_host.window_size_max * BETA / float(C)) ** (1.0/3.0)
                t = global_time - curr_host.last_congestion_time
                window_new = C * (t - K)**3 + curr_host.window_size_max
                if window_new < curr_host.get_window_size():
                    curr_host.last_congestion_time = global_time
                    curr_host.window_size_max = curr_host.get_window_size()
                curr_host.set_window_size(window_new)
            elif curr_host.get_is_reno():
                pass
            else:
                assert False

            ec.create_update_window_event(curr_host, global_time + PERIODIC_FAST_INTERVAL)
            network.populate_packets_into_buffer(curr_host, global_time, dropped_packets)

        else:
            print "event type", event_type
            assert False

        done = 1
        for h in hosts:
            if hosts[h].get_flow_id() != None:
                if not len(hosts[h].get_outstanding_pkts()) % 1000:
                    print "out pkts", len(hosts[h].get_outstanding_pkts()) / 1000
                if not hosts[h].flow_done():
                    
                    done = 0
                    break

    graph_link_rate(link_rate_dict)
    graph_pck_buf(pck_graph_dict)
    graph_packet_loss(packet_loss_dict)
    graph_flow_rate(flow_rate_dict)
    graph_window_size(window_size_dict)
    graph_packet_delay(packet_delay_dict)
