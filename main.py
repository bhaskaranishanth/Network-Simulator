from constants import *
from router import *
from link import *
from host import *
from flow import *
from utilities import *
from pprint import pprint
from djikstra import *
from event import *
from eventqueue import *
from event import *
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

            if count == 10:
                break




if __name__ == '__main__':
    hosts, routers, links, flows = process_input()

    print_dict(hosts, 'HOSTS')
    print_dict(routers, 'ROUTERS')
    print_dict(links, 'LINKS')
    print_dict(flows, 'FLOWS')

    # Create routing table
    d = Djikstra()
    d.update_routing_table(routers.values())
    print_dict(routers, 'ROUTERS')

    timeout_val = .01

    window_size = 10
    initialize_packets(flows, hosts)
    for host_id in hosts:
        link = hosts[host_id].get_link()
        if hosts[host_id].get_window_count() < window_size:
            # Load window number of packets from host queue to buffer
            while link.get_num_packets() < window_size:
                curr_packet = hosts[host_id].remove_packet()
                if curr_packet != None:
                    assert link.insert_into_buffer(curr_packet.get_capacity())
                    hosts[host_id].set_window_count(hosts[host_id].get_window_count()+1)
                    new_event = Event(LINK_TO_ENDPOINT, curr_packet.get_init_time(), curr_packet.get_src(), curr_packet.get_dest(), curr_packet)
                    eq.put((new_event.get_initial_time(), new_event))

                    timeout_event = Event(TIMEOUT_EVENT, timeout_val, curr_packet.get_src(), curr_packet.get_dest(), curr_packet)
                    eq.put((timeout_event.get_initial_time(), timeout_event))
                else:
                    break

        else:
            pass
            # TODO


######## Link might need both directions because one links buffer might be full 
#### while on the other direction, it can be full too
####### It may be possible for ack packets to come back out of order
####### Timeout event happens first, then ack packet is received.
###### Flow has its own start time
###### Do acknowledgement packets need to be in the buffer
###### Create event processing class to handle all different types of events
###### Event should only have the current src and dst, packet has total distance, LINK_TO_ENDPOINT is the only exception
###### Implement window counter for each host

    global_time = 0
    acknowledged_packets = {}
    pck_graph = []
#     buf_to_link_time = .05
    dropped_packets = []
#     timeout_val = 1

    # Continuously pull events from the priority queue
    while eq.qsize() != 0:
        print 'Queue size: ', eq.qsize()
        t, event_top = eq.get()
        pck_graph.append(pck_tot_buffers(t, links))
        assert t != None
        global_time = t
        print t, event_top

        # Send from Link Buffer -> Endpoint
        if event_top.get_type() == LINK_TO_ENDPOINT:
            curr_entity = routers if event_top.get_data().get_curr_loc() in routers else hosts
            curr_src = curr_entity[event_top.get_data().get_curr_loc()]
            curr_packet = event_top.get_data()

            # Compute curr link
            curr_link = None
            if isinstance(curr_src, Host):
                print 'Host specific processing...'
                curr_link = curr_entity[event_top.get_data().get_curr_loc()].get_link()
            else:
                # assert False
                print 'Router specific processing...'
                next_hop = curr_src.get_routing_table()[hosts[curr_packet.get_dest()]]
                curr_link = curr_src.get_link_for_dest(next_hop)

            if curr_link.get_free_time() <= t:
                # If link free, use link and send a received packet that
                # gets completed once it passes through the link
                dst_time = global_time + curr_packet.get_capacity() / curr_link.get_prop_time() + curr_link.get_trans_time()
                print "dest time:", dst_time
                curr_link.update_next_free_time(dst_time)

                # Compute src and dest locations for event
                event_src_loc = curr_packet.get_curr_loc()
                curr_packet.set_curr_loc(curr_link.get_link_endpoint(curr_src))
                event_dst_loc = curr_packet.get_curr_loc()
                # print 'Event ', event_src_loc, event_dst_loc
                new_event = Event(PACKET_RECEIVED, dst_time, event_src_loc, event_dst_loc, curr_packet)
                eq.put((new_event.get_initial_time(), new_event))

                # Remove packets from buffer and decrement count
                curr_link.remove_from_buffer(curr_packet.get_capacity())

            else:
                # Else, update event completion time
                event_top.initial_time = curr_link.get_free_time()
                eq.put((event_top.initial_time, event_top))

        # Host or Router receives a packet
        elif event_top.get_type() == PACKET_RECEIVED:
            # Router component
            if event_top.get_data().get_curr_loc() in routers:
                print 'Packet received in router....'     
                curr_router = routers[event_top.get_data().get_curr_loc()]
                curr_packet = event_top.get_data()

                next_hop = curr_router.get_routing_table()[hosts[curr_packet.get_dest()]]
                curr_link = curr_router.get_link_for_dest(next_hop)

                # print 'Packet info: '
                # print curr_packet
                
                # curr_packet.set_curr_loc(curr_link.get_link_endpoint(curr_router))

                # print 'Packet info: '
                # print curr_packet

                # Insert packet into buffer
                if curr_link.insert_into_buffer(curr_packet.get_capacity()):
                    new_event = Event(LINK_TO_ENDPOINT, global_time, curr_packet.get_curr_loc(), next_hop.get_ip(), curr_packet)
                    eq.put((new_event.get_initial_time(), new_event))
                else:
                    dropped_packets.append(curr_packet)

            # Host receives a packet
            elif event_top.get_data().get_curr_loc() in hosts:
                curr_host = hosts[event_top.get_data().get_curr_loc()]
                curr_packet = event_top.get_data()
                curr_link = hosts[event_top.get_data().get_curr_loc()].get_link()
                # Acknowledgment packet received
                if curr_packet.get_type() == ACK_PACKET:
                    print 'Acknowledged this shit'

                    # Insert acknowledgement into dictionary
                    if curr_packet.packet_id in acknowledged_packets:
                        acknowledged_packets[curr_packet.packet_id] += 1
                    else:
                        acknowledged_packets[curr_packet.packet_id] = 1
                        # Perform this ack only based on certain acks
                        curr_host.set_window_count(curr_host.get_window_count()-1)


                    # Convert packet from host queue into event and insert into buffer
                    if curr_host.get_window_count() < window_size:
                        # assert False
                        # assert curr_link.get_num_packets() - window_size < 0
                        while curr_link.get_num_packets() < window_size:
                            pkt = curr_host.remove_packet()
                            if pkt != None:
                                if curr_link.insert_into_buffer(pkt.get_capacity()):
                                    new_event = Event(LINK_TO_ENDPOINT, global_time, pkt.get_src(), pkt.get_dest(), pkt)
                                    eq.put((new_event.get_initial_time(), new_event))

                                    dst_time = global_time + timeout_val
                                    timeout_event = Event(TIMEOUT_EVENT, dst_time, pkt.get_src(), pkt.get_dest(), pkt)
                                    eq.put((timeout_event.get_initial_time(), timeout_event))

                                    # Increment window count
                                    curr_host.set_window_count(curr_host.get_window_count()+1)
                            else:
                                break

                else:
                    # Other packets
                    print 'Received host'
                    # assert curr_link.get_free_time() <= t

                    if curr_link.get_free_time() <= t:
                        print 'Running...'

                        # If link free, use link and send a received packet that
                        # gets completed once it passes through the link
                        # dst_time = global_time + link_transfer_time
                        # curr_link.update_next_free_time(dst_time)
                        dst_time = global_time

                        # Make sure the ack packet has the same id as the original packet
                        p = Packet(ACK_PACKET, 1, curr_packet.get_dest(), curr_packet.get_src(), curr_packet.get_dest(), global_time)
                        p.packet_id = curr_packet.packet_id
                        # p.set_curr_loc(p.get_src())

                        # print event_top
                        # print p.get_dest()
                        # print p.get_src()
                        # print p

                        # print 'Curr link ....'
                        # print curr_link

                        # Determine the event start and end location
                        event_src_loc = p.get_src()
                        event_dst_loc = curr_link.get_link_endpoint(curr_host)

                        # print event_src_loc
                        # print event_dst_loc

                        if curr_link.insert_into_buffer(p.get_capacity()):
                            new_event = Event(LINK_TO_ENDPOINT, dst_time, event_src_loc, event_dst_loc, p)
                            eq.put((new_event.get_initial_time(), new_event))

                        else:
                            dropped_packets.append(curr_packet)


                        # curr_packet.set_curr_loc(curr_link.get_link_endpoint(curr_host))
                        # new_event = Event(PACKET_RECEIVED, dst_time, event_top.get_src(), event_top.get_dest(), event_top.get_flow(), curr_packet)
                        # eq.put((new_event.get_initial_time(), new_event))
                    else:
                        print 'Waiting....'
                        # Else, update event completion time
                        event_top.initial_time = curr_link.get_free_time()
                        eq.put((event_top.initial_time, event_top))


        elif event_top.get_type() == TIMEOUT_EVENT:
            curr_packet = event_top.get_data()
            curr_host = hosts[event_top.get_src()]
            p_id = curr_packet.packet_id
            if p_id in acknowledged_packets:
                # Packet was acknowledged beforehand
                if acknowledged_packets[p_id] == 1:
                    del acknowledged_packets[p_id]
                else:
                    acknowledged_packets[p_id] -= 1
            else:
                print 'Creating timeout packet'
                # Create new packet and insert into host's queue
                p = Packet(MESSAGE_PACKET, 1, curr_packet.get_src(), curr_packet.get_dest(), curr_packet.get_src(), global_time)
                p.packet_id = curr_packet.packet_id
                # curr_host.insert_packet(p)
                dropped_packets.append(p)

                curr_link = hosts[curr_packet.get_src()].get_link()
                
                if curr_link.insert_into_buffer(p.get_capacity()):
                    new_event = Event(LINK_TO_ENDPOINT, global_time, p.get_src(), p.get_dest(), p)
                    eq.put((new_event.get_initial_time(), new_event))

                else:
                    dropped_packets.append(curr_packet)


                dst_time = global_time + timeout_val
                timeout_event = Event(TIMEOUT_EVENT, dst_time, p.get_src(), p.get_dest(), p)
                eq.put((timeout_event.get_initial_time(), timeout_event))


                # new_event = Event(LINK_TO_ENDPOINT, global_time, p.get_src(), p.get_dest(), None, p)
                # eq.put((new_event.get_initial_time(), new_event))

                # timeout_event = Event(TIMEOUT_EVENT, global_time + timeout_val, p.get_src(), p.get_dest(), None, p)
                # eq.put((timeout_event.get_initial_time(), timeout_event))

            print 'Timeout happened!!!!!'
            print 'Other'
        else:
            assert False

    print 'Completed everything '
    print len(dropped_packets)
    # print(pck_graph)
    graph(pck_graph)

