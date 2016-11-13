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

def initialize_packets(flows, hosts):
    for key in flows:
        event_list = []
        count = 0
        for packet in flows[key].gen_packets()[0]:
            count += 1
            hosts[flows[key].get_src()].insert_packet(packet)

            if count == 2:
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

    MAX_BUFFER_SIZE = 64

    timeout_val = 5

    window_size = 1
    initialize_packets(flows, hosts)
    for host_id in hosts:
        link = hosts[host_id].get_link()
        if int(link.buf) > window_size:
            # Load window number of packets from host queue to buffer
            while link.get_num_packets() < window_size:
                curr_packet = hosts[host_id].remove_packet()
                if curr_packet != None:
                    link.inc_packet()
                    link.inc_actual_packet()

                    new_event = Event(LINK_TO_ENDPOINT, 0, curr_packet.get_src(), curr_packet.get_dest(), None, curr_packet)
                    eq.put((new_event.get_initial_time(), new_event))

                    timeout_event = Event(TIMEOUT_EVENT, timeout_val, curr_packet.get_src(), curr_packet.get_dest(), None, curr_packet)
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
###### Rename get_curr_loc() to be the get_dest_loc() since it is the endpoint, wait i'm confused on this part too
###### Create event processing class to handle all different types of events
###### Event should only have the current src and dst, packet has total distance, LINK_TO_ENDPOINT is the only exception


    global_time = 0
    acknowledged_packets = {}
    pck_graph = []
#     buf_to_link_time = .05
#     dropped_packets = []
#     timeout_val = 1

    # Continuously pull events from the priority queue
    link_transfer_time = 1
    while eq.qsize() != 0:
        print 'Queue size: ', eq.qsize()
        t, event_top = eq.get()
        pck_graph.append(pck_tot_buffers(t, links))
        assert t != None
        global_time = t
        print t, event_top

        if event_top.get_type() == LINK_TO_ENDPOINT:
            if event_top.get_data().get_curr_loc() in routers:
                print 'Router specific processing....'
                curr_host = routers[event_top.get_data().get_curr_loc()]
                curr_packet = event_top.get_data()
                curr_link = routers[event_top.get_data().get_curr_loc()].get_link()
                # if curr_link.get_free_time() <= t:
                #     # If link free, use link and send a received packet that
                #     # gets completed once it passes through the link
                #     dst_time = global_time + link_transfer_time
                #     curr_link.update_next_free_time(dst_time)
                #     curr_packet.set_curr_loc(curr_link.get_link_endpoint(curr_host))
                #     new_event = Event(PACKET_RECIEVED, dst_time, event_top.get_src(), event_top.get_dest(), event_top.get_flow(), curr_packet)
                #     eq.put((new_event.get_initial_time(), new_event))

                #     # Decrease actual packets
                #     link.dec_actual_packet()
                # else:
                #     # Else, update event completion time
                #     event_top.initial_time = curr_link.get_free_time()
                #     eq.put((event_top.initial_time, event_top))



                # curr_packet = event_top.get_data()
                # curr_router = routers[curr_packet.get_curr_loc()]
                # next_hop = curr_router.get_routing_table()[curr_packet.get_dest()]
                # curr_link = curr_router.get_link_for_dest(next_hop)

                # if curr_link.insert_into_buffer(curr_packet.get_capacity()):
                #     # Fix time shit now length of buffer

                #     dst_time = global_time + buf_to_link_time * curr_link.get_capacity()
                #     newEvent = Event(BUFFER_TO_LINK, dst_time, event_top.get_src(), event_top.get_dest(), event_top.get_flow(), curr_packet)
                #     eq.put((dst_time, newEvent))
                # else:
                #     dropped_packets.append(curr_packet)

                # dst_time = global_time + timeout_val
                # timeout_event = Event(TIMEOUT_EVENT, dst_time, event_top.get_src(), event_top.get_dest(), event_top.get_flow(), curr_packet)
                # eq.put((dst_time, newEvent))
                print 'hello'

            elif event_top.get_data().get_curr_loc() in hosts:
                curr_host = hosts[event_top.get_data().get_curr_loc()]
                curr_packet = event_top.get_data()
                curr_link = hosts[event_top.get_data().get_curr_loc()].get_link()
                if curr_link.get_free_time() <= t:
                    # If link free, use link and send a received packet that
                    # gets completed once it passes through the link
                    dst_time = global_time + link_transfer_time
                    curr_link.update_next_free_time(dst_time)
                    event_src_loc = curr_packet.get_curr_loc()
                    # print 'Curr location: ', curr_packet.get_curr_loc()
                    # print 'Curr host: ', curr_host
                    curr_packet.set_curr_loc(curr_link.get_link_endpoint(curr_host))
                    event_dst_loc = curr_packet.get_curr_loc()
                    # print 'Curr location: ', curr_packet.get_curr_loc()
                    new_event = Event(PACKET_RECIEVED, dst_time, event_src_loc, event_dst_loc, None, curr_packet)
                    eq.put((new_event.get_initial_time(), new_event))

                    # Decrease actual packets
                    link.dec_actual_packet()
                else:
                    # Else, update event completion time
                    event_top.initial_time = curr_link.get_free_time()
                    eq.put((event_top.initial_time, event_top))


                # if curr_link.insert_into_buffer(curr_packet.get_capacity()):
                #     dst_time = global_time + buf_to_link_time
                #     newEvent = Event(BUFFER_TO_LINK, dst_time, event_top.get_src(), event_top.get_dest(), event_top.get_flow(), curr_packet)
                #     eq.put((dst_time, newEvent))
                # else:
                #     dropped_packets.append(curr_packet)

                # dst_time = global_time + timeout_val
                # timeout_event = Event(TIMEOUT_EVENT, dst_time, event_top.get_src(), event_top.get_dest(), event_top.get_flow(), curr_packet)
                # eq.put((dst_time, timeout_event))

            else:
                assert False


        # elif event_top.get_type() == BUFFER_TO_LINK:
        elif event_top.get_type() == PACKET_RECIEVED:
            # Router component
            if event_top.get_data().get_curr_loc() in routers:
                print 'Packet received in router....'            
                curr_router = routers[event_top.get_data().get_curr_loc()]
                curr_packet = event_top.get_data()

                ##### Indicate somehow that the link you just came from was free

                curr_link.dec_packet()

                # Need to compute the next link from routing table
                dest = curr_router.get_routing_table()[curr_packet.get_dest()]
                next_link = curr_router.get_link_for_dest(dest)


                # curr_link = routers[event_top.get_data().get_curr_loc()].get_link()

                # If link buffer has space, insert packet into it, else drop packet
                if next_link.get_num_packets() < MAX_BUFFER_SIZE:
                    next_link.inc_packet()
                    next_link.inc_actual_packet()

                    new_event = Event(LINK_TO_ENDPOINT, global_time, curr_packet.get_src(), curr_packet.get_dest(), None, curr_packet)
                    eq.put((new_event.get_initial_time(), new_event))





            # Host component
            if event_top.get_data().get_curr_loc() in hosts:
                curr_host = hosts[event_top.get_data().get_curr_loc()]
                curr_packet = event_top.get_data()
                curr_link = hosts[event_top.get_data().get_curr_loc()].get_link()
                # Acknowledgment packet
                if curr_packet.get_type() == ACK_PACKET:
                    print 'Acknowledged this shit'

                    # Insert acknowledgement into dictionary
                    if curr_packet.packet_id in acknowledged_packets:
                        acknowledged_packets[curr_packet.packet_id] += 1
                    else:
                        acknowledged_packets[curr_packet.packet_id] = 1

                    # Convert packet from host queue into event and insert into buffer
                    curr_link.dec_packet()
                    if int(curr_link.buf) > window_size:
                        assert curr_link.get_num_packets() - window_size < 0
                        while curr_link.get_num_packets() < window_size:
                            pkt = curr_host.remove_packet()
                            if pkt != None:
                                curr_link.inc_packet()
                                curr_link.inc_actual_packet()

                                new_event = Event(LINK_TO_ENDPOINT, global_time, pkt.get_src(), pkt.get_dest(), None, pkt)
                                eq.put((new_event.get_initial_time(), new_event))

                                dst_time = global_time + timeout_val
                                timeout_event = Event(TIMEOUT_EVENT, dst_time, pkt.get_src(), pkt.get_dest(), None, pkt)
                                eq.put((timeout_event.get_initial_time(), timeout_event))
                            else:
                                break

                else:
                    # Other packets
                    print 'Received host'

                    # dst_time = global_time + link_transfer_time
                    # curr_link.update_next_free_time(dst_time)

                    # p = Packet(ACK_PACKET, 1, curr_packet.get_dest(), curr_packet.get_src(), curr_link.get_link_endpoint(curr_host))
                    # p.packet_id = curr_packet.packet_id

                    assert curr_link.get_free_time() <= t

                    if curr_link.get_free_time() <= t:
                        print 'Running...'

                        # If link free, use link and send a received packet that
                        # gets completed once it passes through the link
                        dst_time = global_time + link_transfer_time
                        curr_link.update_next_free_time(dst_time)

                        # Make sure the ack packet has the same id as the original packet
                        p = Packet(ACK_PACKET, 1, curr_packet.get_dest(), curr_packet.get_src(), curr_link.get_link_endpoint(curr_host))
                        p.packet_id = curr_packet.packet_id

                        # print event_top
                        # print p.get_dest()
                        # print p.get_src()

                        # Determine the event start and end location
                        event_src_loc = p.get_src()
                        event_dst_loc = curr_link.get_link_endpoint(curr_host)

                        new_event = Event(PACKET_RECIEVED, dst_time, event_src_loc, event_dst_loc, None, p)
                        eq.put((new_event.get_initial_time(), new_event))

                        # curr_packet.set_curr_loc(curr_link.get_link_endpoint(curr_host))
                        # new_event = Event(PACKET_RECIEVED, dst_time, event_top.get_src(), event_top.get_dest(), event_top.get_flow(), curr_packet)
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
                # Create new packet and insert into host's queue
                p = Packet(MESSAGE_PACKET, 1, curr_packet.get_src(), curr_packet.get_dest(), curr_packet.get_src())
                p.packet_id = curr_packet.packet_id
                curr_host.insert_packet(p)

            print 'Timeout happened!!!!!'
            print 'Other'
        else:
            assert False

    print 'Completed everything '
    # print(pck_graph)
    # graph(pck_graph)

