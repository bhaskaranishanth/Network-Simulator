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

            # if count == 1000:
            #     break




if __name__ == '__main__':
    # Process input
    hosts, routers, links, flows = process_input()

    print_dict(hosts, 'HOSTS')
    print_dict(routers, 'ROUTERS')
    print_dict(links, 'LINKS')
    print_dict(flows, 'FLOWS')

    # Create routing table
    d = Djikstra()
    d.update_routing_table(routers.values())
    print_dict(routers, 'ROUTERS')

    timeout_val = 1

    window_size = 100
    initialize_packets(flows, hosts)
    # Fills up all the link's buffers connected to the host 
    for host_id in hosts:
        link = hosts[host_id].get_link()
        if hosts[host_id].get_window_count() < window_size:
            # Load window number of packets from host queue to buffer
            while link.get_num_packets() < window_size:
                curr_packet = hosts[host_id].remove_packet()
                if curr_packet != None:
                    if link.insert_into_buffer(curr_packet, curr_packet.get_capacity()):
                        hosts[host_id].set_window_count(hosts[host_id].get_window_count()+1)
                        if len(link.packet_queue) == 1:
                            curr_src = hosts[curr_packet.get_src()]
                            next_dest = link.get_link_endpoint(curr_src)
                            assert next_dest not in hosts.values()
                            assert next_dest not in hosts
                            # print 'Curr src: ', curr_src
                            # print 'Curr dest: ', next_dest
                            # print type(curr_src)
                            # print type(next_dest)
                            # break
                            # break



                            new_event = Event(PACKET_RECEIVED, 
                                curr_packet.get_init_time() + curr_packet.get_capacity() / link.get_prop_time() + link.get_trans_time(), curr_src.get_ip(), next_dest, curr_packet)
                            eq.put((new_event.get_initial_time(), new_event))

                        timeout_event = Event(TIMEOUT_EVENT, timeout_val + curr_packet.get_init_time(), curr_packet.get_src(), curr_packet.get_dest(), curr_packet)
                        eq.put((timeout_event.get_initial_time(), timeout_event))
                    else:
                        # Put packet back into the host since buffer is full
                        hosts[host_id].insert_packet(curr_packet)
                        break
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
    dropped_packets = []
    pck_drop_graph = []
#     timeout_val = 1

    # Continuously pull events from the priority queue
    while eq.qsize() != 0:
        print 'Queue size: ', eq.qsize()
        print '-' * 80
        t, event_top = eq.get()
        pck_graph.append(pck_tot_buffers(t, links))
        pck_drop_graph.append(drop_packets(t, links))
        assert t != None
        global_time = t
        print t, event_top

        assert event_top.get_type() != LINK_TO_ENDPOINT

        # Host or Router receives a packet
        if event_top.get_type() == PACKET_RECEIVED:
            curr_link = None
            for l in links:
                print event_top.get_src()
                print event_top.get_dest()
                print links[l].get_endpoints()[0]
                endpoints_id = (links[l].get_endpoints()[0].get_ip(), links[l].get_endpoints()[1].get_ip())
                if event_top.get_src() in endpoints_id and event_top.get_dest() in endpoints_id:
                    curr_link = links[l]
                    break
            assert curr_link != None

            curr_packet = event_top.get_data()
            curr_link.remove_from_buffer(curr_packet, curr_packet.get_capacity())
            print 'Removing from buffer.....'
            print curr_link
            if len(curr_link.packet_queue) != 0:
                next_packet = curr_link.packet_queue[0]
                # print 'This is the next packet: ', next_packet
                # next_src = next_packet.get_curr_loc()
                curr_entity = routers if next_packet.get_curr_loc() in routers else hosts

                # if next_packet.get_curr_loc() == next_packet.get_src():
                curr_src = curr_entity[next_packet.get_curr_loc()]
                next_dest = curr_link.get_link_endpoint(curr_src)
                print 'Next packet: ', next_packet
                print next_dest
                # assert next_dest not in hosts.values()
                # assert next_dest not in hosts

                # print 'Next src: ', curr_src
                # print 'Next dest: ', next_dest
                new_event = Event(PACKET_RECEIVED, 
                    global_time + next_packet.get_capacity() / curr_link.get_prop_time() + curr_link.get_trans_time(), curr_src.get_ip(), next_dest, next_packet)
                eq.put((new_event.get_initial_time(), new_event))
                # print 'New event: ', new_event


            curr_packet.set_curr_loc(event_top.get_dest())
            print 'This is curr location: ', event_top.get_data().get_curr_loc()
            # exit(1)
            # Router component
            if event_top.get_data().get_curr_loc() in routers:
                print 'Packet received in router....'     
                curr_router = routers[event_top.get_data().get_curr_loc()]

                next_hop = curr_router.get_routing_table()[hosts[curr_packet.get_dest()]]
                next_link = curr_router.get_link_for_dest(next_hop)
                print 'This is packet: ', curr_packet
                # break


                # Insert packet into buffer
                if next_link.insert_into_buffer(curr_packet, curr_packet.get_capacity()):
                    if next_link.get_free_time() <= global_time:
                        if len(next_link.packet_queue) == 1:
                            # print 'Next packet: ', curr_packet
                            # print next_hop
                            # assert next_hop not in hosts.values()
                            # assert next_hop not in hosts
                            new_event = Event(PACKET_RECEIVED, 
                                global_time + curr_packet.get_capacity() / next_link.get_prop_time() + next_link.get_trans_time(), curr_packet.get_curr_loc(), next_hop.get_ip(), curr_packet)
                            eq.put((new_event.get_initial_time(), new_event))

                else:
                    dropped_packets.append(curr_packet)
                    next_link.increment_drop_packets()
                    #assert False


            # Host receives a packet
            elif event_top.get_data().get_curr_loc() in hosts:
                curr_host = hosts[event_top.get_data().get_curr_loc()]
                next_link = hosts[event_top.get_data().get_curr_loc()].get_link()
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
                        # assert next_link.get_num_packets() - window_size < 0
                        while next_link.get_num_packets() < window_size:
                            pkt = curr_host.remove_packet()
                            if pkt != None:
                                if next_link.insert_into_buffer(pkt, pkt.get_capacity()):
                                    assert next_link.get_free_time() <= global_time
                                    if next_link.get_free_time() <= global_time:
                                        # hosts[host_id].set_window_count(hosts[host_id].get_window_count()+1)
                                        if len(next_link.packet_queue) == 1:
                                            # assert pkt.get_dest() not in hosts
                                            # assert pkt.get_src() not in hosts

                                            next_hop = curr_router.get_routing_table()[hosts[pkt.get_src()]].get_ip()
                                            assert next_hop not in hosts
                                            new_event = Event(PACKET_RECEIVED, 
                                                global_time + curr_packet.get_capacity() / next_link.get_prop_time() + next_link.get_trans_time(), pkt.get_src(), next_hop, pkt)
                                            eq.put((new_event.get_initial_time(), new_event))

                                        dst_time = global_time + timeout_val
                                        timeout_event = Event(TIMEOUT_EVENT, dst_time, pkt.get_src(), pkt.get_dest(), pkt)
                                        eq.put((timeout_event.get_initial_time(), timeout_event))


                            else:
                                break

                else:
                    # Other packets
                    print 'Received host'
                    # if next_link.get_free_time() <= t:
                    print 'Running...'
                    # Immediately insert the packet into the link buffer
                    dst_time = global_time

                    # Make sure the ack packet has the same id as the original packet
                    # print 'curr_packet ', curr_packet.get_dest()
                    # print 'curr_packet ', curr_packet.get_src()
                    curr_src = hosts[curr_packet.get_dest()]
                    next_dest = next_link.get_link_endpoint(curr_src)

                    p = Packet(ACK_PACKET, 1, curr_src.get_ip(), curr_packet.get_src(), next_dest, global_time)
                    p.packet_id = curr_packet.packet_id
                    # p.set_curr_loc(p.get_src())

                    # print event_top
                    # print p
                    # print 'Src: ', p.get_src()
                    # print 'Dst: ', p.get_dest()
                    # print 'Next dst: ', next_dest
                    # print p

                    # print 'Curr link ....'
                    # print next_link
                    # print 'This is src: ', event_src_loc
                    # print 'This is dst: ', event_dst_loc

                    # Insert ack packet into the buffer
                    if next_link.insert_into_buffer(p, p.get_capacity()):
                        # print 'Inserting....'
                        print len(next_link.packet_queue)
                        # hosts[host_id].set_window_count(hosts[host_id].get_window_count()+1)
                        if len(next_link.packet_queue) == 1:
                            # print 'Is only....'
                            assert next_dest not in hosts.values()
                            assert next_dest not in hosts
                            new_event = Event(PACKET_RECEIVED, 
                                global_time + p.get_capacity() / next_link.get_prop_time() + next_link.get_trans_time(), curr_src.get_ip(), next_dest, p)
                            eq.put((new_event.get_initial_time(), new_event))

                    else:
                        dropped_packets.append(curr_packet)
                        next_link.increment_drop_packets()
                        #assert False


        elif event_top.get_type() == TIMEOUT_EVENT:
            curr_packet = event_top.get_data()
            curr_host = hosts[event_top.get_src()]
            p_id = curr_packet.packet_id

            # Packet was acknowledged beforehand
            if p_id in acknowledged_packets:
                if acknowledged_packets[p_id] == 1:
                    del acknowledged_packets[p_id]
                else:
                    acknowledged_packets[p_id] -= 1
            else:
                print 'Creating timeout packet'
                curr_link = hosts[curr_packet.get_src()].get_link()
                next_hop = curr_link.get_link_endpoint(hosts[curr_packet.get_src()])
                # Create new packet
                p = Packet(MESSAGE_PACKET, 1, curr_packet.get_src(), curr_packet.get_dest(), next_hop, global_time)
                p.packet_id = curr_packet.packet_id
                dropped_packets.append(p)

                # Attempt to insert new packet back to buffer
                if curr_link.insert_into_buffer(p, p.get_capacity()):
                    hosts[host_id].set_window_count(hosts[host_id].get_window_count()+1)
                    if curr_link.get_free_time() <= global_time:
                        if len(curr_link.packet_queue) == 1:
                            assert p.get_curr_loc() == next_hop
                            assert next_dest not in hosts.values()
                            assert next_dest not in hosts
                            new_event = Event(PACKET_RECEIVED, 
                                global_time + p.get_capacity() / curr_link.get_prop_time() + curr_link.get_trans_time(), p.get_src(), next_hop, p)
                            eq.put((new_event.get_initial_time(), new_event))
                else:

                # Create a timeout event for the new packet
                    dropped_packets.append(p)
                    curr_link.increment_drop_packets()
                    #assert False

                dst_time = global_time + timeout_val
                timeout_event = Event(TIMEOUT_EVENT, dst_time, p.get_src(), p.get_dest(), p)
                eq.put((timeout_event.get_initial_time(), timeout_event))

            print 'Timeout happened!!!!!'
            print 'Other'
        else:
            assert False

    print 'Completed everything '
    # print len(dropped_packets)
    # # print(pck_graph)
    graph_pck_buf(pck_graph)
    # points = format_drop_to_rate(pck_drop_graph)
    # graph(points)
    # graph_pck_drop_rate(pck_drop_graph)
    graph_pck_buf(pck_graph)

