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
            # diff = ((hosts[host].get_bytes_received() - prev) / (10 ** 6 / 8.0)) / global_time
            print 'Diff: ', global_time, diff, hosts[host].get_bytes_received(), prev
            flow_rate_dict[hosts[host].get_flow_id()].append((global_time, diff))
            flows[hosts[host].get_flow_id()].prev = hosts[host].get_bytes_received()

    # print 'Diff '

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
    pck_graph = []
    dropped_packets = []
    pck_drop_graph = []
    window_size_dict = {}
    packet_delay_dict = {}
    flow_rate_dict = {}

    # Initialize graph dictionaries
    for _, h in hosts.iteritems():
        if h.get_flow_id() is not None:
            f_id = h.get_flow_id()
            window_size_dict[f_id] = []
            packet_delay_dict[f_id] = []
            flow_rate_dict[f_id] = []
        if h.get_tcp():
            ec.create_update_window_event(h, PERIODIC_FAST_INTERVAL)
    
    done = 0
    # Continuously pull events from the priority queue
    while eq.qsize() != 0 and not done:
        print 'Queue size: ', eq.qsize()
        print '-' * 80
        t, event_top = eq.get()
        print 'Event details', event_top
        assert t != None
        assert t >= global_time
        global_time = t
        event_type = event_top.get_type()


        # for h in hosts:
        #     print "Host Window count:", hosts[h].get_window_count()
        #     print "Host Window size:", hosts[h].get_window_size()

        # print "global time:", global_time
        # for l in links:
        #     print "Link ID:", l
        #     links[l].print_link_buffer()
        #     print "Host Window Link id:", l
        #     print "Host Window Link size:", len(links[l].packet_queue)
        # print 'Link 1 size: ', len(links['L1'].packet_queue)
        # print 'Link 1 capacity size: ', links['L1'].capacity
        # print 'Link 1 size: ', links['L1']
        # print 'Link 1 buf: ', links['L1'].buf

        pck_graph.append(pck_tot_buffers(t, links))
        pck_drop_graph.append(drop_packets(t, links))
        # print t, event_top
        store_packet_delay(packet_delay_dict, hosts, global_time)
        store_flow_rate(flow_rate_dict, hosts, global_time)

        # if event_type != DYNAMIC_ROUTING and event_type != GRAPH_EVENT and event_type != UPDATE_WINDOW:
        #     pkt = event_top.get_data()
        #     if pkt.get_packet_id() == 14:
        #         print "global time", global_time
        #         print "L0 buffer", links['L0'].print_link_buffer()
        #         while eq.qsize() != 0:
        #             t, event_top = eq.get()
        #             print 'Event details at packet 14', event_top
        #         exit(1)


        # Host or Router receives a packet
        if event_type == PACKET_RECEIVED:
            ep.process_packet_received_event(event_top, global_time, links, routers, 
                hosts, dropped_packets, acknowledged_packets, window_size_dict)
        elif event_type == TIMEOUT_EVENT:
            ep.process_timeout_event(event_top, global_time, hosts, dropped_packets, 
                acknowledged_packets)
        elif event_type == DYNAMIC_ROUTING:
            # if eq.qsize() == 0 or eq.qsize() == 1:
            #     break
            # elif eq.qsize() == 1:
            #     t, event_top = eq.get()
            #     if event_type == UPDATE_WINDOW:
            #         break
            #     else:
            #         eq.put((t, event_top))
            # create_dynamic_routing_event(event_top.get_initial_time() + ROUTING_INTERVAL)
            for r in routers:
                routers[r].reset_weight_table()

            # Creates routing packet for each host and adds to queue
            for _, h in hosts.iteritems():
                l = h.get_link()
                dest = l.get_link_endpoint(h)
                routing_pkt = Packet(ROUTER_PACKET, l.get_weight(), h.get_ip(), None, l.get_link_endpoint(h).get_ip(), None)
                if len(l.packet_queue) == 0:
                    if l.get_direction() == (h.get_ip(), dest.get_ip()):
                        # Insert packet into the next link's buffer
                        if ep.insert_routing_packet_into_buffer(routing_pkt, l, dropped_packets, global_time, dest):
                            ec.create_remove_from_buffer_event(global_time, routing_pkt, h.get_ip(), dest.get_ip())
                    elif l.get_direction() == (dest.get_ip(), h.get_ip()):
                        if ep.insert_routing_packet_into_buffer(routing_pkt, l, dropped_packets, global_time, dest):
                            next_time = max(l.get_last_pkt_dest_time(), global_time)
                            ec.create_remove_from_buffer_event(next_time, routing_pkt, dest.get_ip(), h.get_ip())
                    else:
                        print "link: ", l
                        print "Direction: ", l.get_direction()
                        print "Curr: ", (h.get_ip(), dest.get_ip())
                        assert False
                else:
                    ep.insert_routing_packet_into_buffer(routing_pkt, l, dropped_packets, global_time, dest)
                # ep.insert_routing_packet_into_buffer(routing_pkt, link, dropped_packets, global_time, dest)
                # create_routing_packet_received_event(global_time, routing_pkt, link, host_id, dest):

            ec.create_dynamic_routing_event(global_time + ROUTING_INTERVAL)

        elif event_type == REMOVE_FROM_BUFFER:
            ep.process_remove_from_buffer_event(event_top, global_time)

        elif event_type == ROUTING_PACKET_RECEIVED:
            ep.process_routing_packet_received_event(event_top, hosts, links, dropped_packets, global_time, routers)
        elif event_type == GRAPH_EVENT:
            # Hackish solution to stop the program
            # if eq.qsize() < 2:
            #     break

            store_flow_rate(flow_rate_dict, hosts, global_time)
            store_packet_delay(packet_delay_dict, hosts, global_time)
            ec.create_graph_event(global_time + GRAPH_EVENT_INTERVAL)

        elif event_type == UPDATE_WINDOW:
            # Hackish solution to stop the program
            # if eq.qsize() < 5:
            #     break

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

            ec.create_update_window_event(curr_host, global_time + PERIODIC_FAST_INTERVAL)

            # while curr_host.get_window_count() < curr_host.get_window_size():
            #     pkt = curr_host.remove_packet()
            #     next_link = curr_host.get_link()
            #     next_dest = next_link.get_link_endpoint(curr_host)
            #     if pkt != None:
            #         assert pkt.get_curr_loc() != None
            #         ec.create_timeout_event(TIMEOUT_VAL + pkt.get_init_time(),
            #             pkt, pkt.get_init_time())
            #         if len(next_link.packet_queue) == 0:
            #             if next_link.get_direction() == (curr_host.get_ip(), next_dest.get_ip()):
            #                 # Insert packet into the next link's buffer
            #                 if ep.insert_packet_into_buffer(pkt, next_link, dropped_packets, global_time, next_dest):
            #                     ec.create_remove_from_buffer_event(global_time, pkt, curr_host.get_ip(), next_dest.get_ip())
            #                     curr_host.set_window_count(curr_host.get_window_count()+1)
            #                 # else:
            #                 #     assert False
            #             elif next_link.get_direction() == (next_dest.get_ip(), curr_host.get_ip()):
            #                 if ep.insert_packet_into_buffer(pkt, next_link, dropped_packets, global_time, next_dest):
            #                     next_time = max(next_link.get_last_pkt_dest_time(), global_time)
            #                     ec.create_remove_from_buffer_event(next_time, pkt, next_dest.get_ip(), curr_host.get_ip())
            #                     curr_host.set_window_count(curr_host.get_window_count()+1)
            #                 # else:
            #                 #     assert False
            #             else:
            #                 assert False
            #         else:
            #             if ep.insert_packet_into_buffer(pkt, next_link, dropped_packets, global_time, next_dest):
            #                 curr_host.set_window_count(curr_host.get_window_count()+1)
            #             # else:
            #             #     # TODO
            #             #     assert False


            #         # if next_link.insert_into_buffer(pkt):
            #         #     curr_host.set_window_count(curr_host.get_window_count()+1)
            #         #     if len(next_link.packet_queue) == 1:
            #         #         next_link.remove_from_buffer(pkt, pkt.get_capacity())

            #         #         self.ec.create_packet_received_event(global_time, pkt, next_link, curr_host.get_ip(), next_dest.get_ip())

            #         #     dst_time = global_time + TIMEOUT_VAL
            #         #     self.ec.create_timeout_event(dst_time, pkt, global_time)
            #         # else:
            #         #     # Put the packet back into the host queue
            #         #     curr_host.insert_packet(pkt)
            #         #     break
            #     else:
            #         break

        else:
            print "event type", event_type
            assert False

        done = 1
        for h in hosts:
            # print "out pkts", hosts[h].get_outstanding_pkts()
            if not hosts[h].flow_done():
                done = 0
                break


    # for l in links:
    #     assert len(links[l].packet_queue) == 0

    # print_dict(hosts, 'HOSTS')
    # print_dict(routers, 'ROUTERS')
    # print_dict(links, 'LINKS')
    # print_dict(flows, 'FLOWS')
    # print 'Completed everything '
    # # print len(dropped_packets)
    # # # print(pck_graph)

    # # print window_size_dict
    # # print flow_rate_dict
    graph_flow_rate(flow_rate_dict)
    graph_pck_buf(pck_graph)
    graph_window_size(window_size_dict)
    graph_packet_delay(packet_delay_dict)

    # # graph_pck_buf(pck_graph)
    # # graph_window_size(window_size_dict)
    # # points = format_drop_to_rate(pck_drop_graph)
    # # graph(points)
    # # print(pck_drop_graph)
    # # graph_pck_drop_rate(pck_drop_graph)
    # # graph_pck_buf(pck_graph)

