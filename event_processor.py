from packet import *
from constants import *
from event import *
from eventqueue import *
from router import *
from link import *
from host import *


def create_packet_received_event(global_time, pkt, link, src, dest):
    """
    Takes in packet and link information, creates a PACKET_RECEIVED
    event and adds it to the global queue. Returns the event
    to make it easier to debug code.
    """
    new_event = Event(PACKET_RECEIVED, 
        global_time + pkt.get_capacity() / link.get_trans_time() + link.get_prop_time(), 
        src, dest, pkt)
    eq.put((new_event.get_initial_time(), new_event))
    return new_event

def create_routing_packet_received_event(global_time, pkt, link, src, dest):
    """
    Takes in packet and link information, creates a PACKET_RECEIVED
    event and adds it to the global queue. Returns the event
    to make it easier to debug code.
    """
    new_event = Event(ROUTING_PACKET_RECEIVED, 
        global_time + pkt.get_capacity() / link.get_trans_time() + link.get_prop_time(), 
        src, dest, pkt)
    eq.put((new_event.get_initial_time(), new_event))
    return new_event

def create_dynamic_routing_event(routing_time):
    """
    Takes in packet and link information, creates a PACKET_RECEIVED
    event and adds it to the global queue. Returns the event
    to make it easier to debug code.
    """
    new_event = Event(DYNAMIC_ROUTING, routing_time, None, None, None)
    eq.put((new_event.get_initial_time(), new_event))
    return new_event


def get_link_from_event(event_top, links):
    """
    From the provided event and a list of links, the function
    determines which link is being used.
    """
    curr_link = None
    for l in links:
        endpoints_id = (links[l].get_endpoints()[0].get_ip(), links[l].get_endpoints()[1].get_ip())
        if event_top.get_src() in endpoints_id and event_top.get_dest() in endpoints_id:
            curr_link = links[l]
            break
    assert curr_link != None
    return curr_link


def insert_packet_into_buffer(curr_packet, next_link, dropped_packets, global_time, next_hop):
    """
    Function takes the given packet, converts it into an event, and adds it to the
    link's buffer. If the packet is not able to be added to the buffer, it
    will be dropped.
    """
    print 'Insert packet into buffer..'
    assert curr_packet.get_curr_loc() == next_hop.get_ip()

    # Insert packet into buffer
    if next_link.insert_into_buffer(curr_packet, curr_packet.get_capacity()):
        if len(next_link.packet_queue) == 1:
            print 'Creating received event from top element of queue'
            create_packet_received_event(global_time, curr_packet, next_link, next_link.get_link_endpoint(next_hop).get_ip(), next_hop.get_ip())
    else:
        dropped_packets.append(curr_packet)
        next_link.increment_drop_packets()

def insert_routing_packet_into_buffer(routing_pkt, next_link, dropped_packets, global_time, next_hop):
    """
    Function takes the given packet, converts it into an event, and adds it to the
    link's buffer. If the packet is not able to be added to the buffer, it
    will be dropped.
    """
    assert routing_pkt.get_dest() == None
    assert routing_pkt.get_type() == ROUTER_PACKET

    # Insert packet into buffer
    if next_link.insert_into_buffer(routing_pkt, routing_pkt.get_capacity()):
        if len(next_link.packet_queue) == 1:
            create_routing_packet_received_event(global_time, routing_pkt, next_link, next_link.get_link_endpoint(next_hop).get_ip(), next_hop.get_ip())
    else:
        dropped_packets.append(routing_pkt)
        next_link.increment_drop_packets()


def create_timeout_event(end_time, pkt, global_time):
    """
    Takes in end time and packet, creates a TIMEOUT_EVENT
    event and adds it to the global queue. Returns the event
    to make it easier to debug code.
    """
    pkt.set_init_time(global_time)
    timeout_event = Event(TIMEOUT_EVENT, end_time, pkt.get_src(), pkt.get_dest(), pkt)
    eq.put((timeout_event.get_initial_time(), timeout_event))
    return timeout_event

def create_next_packet_event(curr_link, global_time, event_top, hosts, routers):
    if len(curr_link.packet_queue) != 0:
        next_packet = curr_link.packet_queue[0]

        if next_packet.get_type() == ROUTER_PACKET:
            new_dest = next_packet.get_curr_loc()
            curr_entity = routers if new_dest in routers else hosts
            new_src = curr_link.get_link_endpoint(curr_entity[new_dest])
            create_routing_packet_received_event(global_time, next_packet, curr_link, new_src.get_ip(), new_dest)

        else:
            # Determine the source and destination of the new event to add to queue
            curr_entity = routers if next_packet.get_curr_loc() in routers else hosts
            next_dest = next_packet.get_curr_loc()
            curr_src = curr_link.get_link_endpoint(curr_entity[next_packet.get_curr_loc()]).get_ip()

            # Create new event with the same packet
            create_packet_received_event(global_time, next_packet, curr_link, curr_src, next_dest)

def create_update_window_event(curr_host, time):
    assert curr_host.is_fast
    update_window_event = Event(UPDATE_WINDOW, time, curr_host.get_ip(), None, None)
    eq.put((update_window_event.get_initial_time(), update_window_event))


def process_routing_packet_received_event(event_top, hosts, links, dropped_packets, global_time, routers):
    curr_link = get_link_from_event(event_top, links)
    curr_packet = event_top.get_data()
    curr_link.remove_from_buffer(curr_packet, curr_packet.get_capacity())

    create_next_packet_event(curr_link, global_time, event_top, hosts, routers)
    # Ignore routing packets sent to host
    if event_top.get_dest() in hosts:
        return 

    # If routing table is not updated, we return
    curr_router = event_top.get_dest()
    weight_table = routers[curr_router].get_weight_table()
    routing_pkt = event_top.get_data()
    curr_entity = routers if routing_pkt.get_src() in routers else hosts
    pkt_src = curr_entity[routing_pkt.get_src()]

    # If the current weight is already smaller than routing packet's payload, don't update
    if weight_table[pkt_src][1] <= routing_pkt.get_payload():
        return


    # Update packet weight
    hop_entity = routers if event_top.get_src() in routers else hosts
    weight_table[pkt_src] = (hop_entity[event_top.get_src()], routing_pkt.get_payload())
    routers[curr_router].get_routing_table()[pkt_src] = hop_entity[event_top.get_src()]

    # Create new packets for all its neighbors
    for l in routers[curr_router].get_links():
        dest = l.get_link_endpoint(routers[curr_router])
        new_weight = l.get_weight() + routing_pkt.get_payload()
        assert routing_pkt.get_src() in hosts
        new_pkt = Packet(ROUTER_PACKET, new_weight, routing_pkt.get_src(), None, dest.get_ip(), None)
        insert_routing_packet_into_buffer(new_pkt, l, dropped_packets, global_time, dest)


def process_packet_received_event(event_top, global_time, links, routers, hosts, dropped_packets, acknowledged_packets, window_size_dict):
    # Retrieve the previous link and remove the received
    # packet from the buffer
    print 'Processing packet received event '
    print '*' * 40
    curr_link = get_link_from_event(event_top, links)
    curr_packet = event_top.get_data()
    curr_link.remove_from_buffer(curr_packet, curr_packet.get_capacity())
    # print curr_packet

    create_next_packet_event(curr_link, global_time, event_top, hosts, routers)

    # Sending packets into the next buffer
    # Router component
    if curr_packet.get_curr_loc() in routers:
        print 'Packet received in router....'     
        curr_router = routers[curr_packet.get_curr_loc()]
        next_hop = curr_router.get_routing_table()[hosts[curr_packet.get_dest()]]
        next_link = curr_router.get_link_for_dest(next_hop)
        curr_packet.set_curr_loc(next_hop.get_ip())

        # Insert packet into the next link's buffer
        insert_packet_into_buffer(curr_packet, next_link, dropped_packets, global_time, next_hop)

    # Host receives a packet
    elif curr_packet.get_curr_loc() in hosts:
        print 'Host receives a packet'
        curr_host = hosts[curr_packet.get_curr_loc()]
        next_link = hosts[curr_packet.get_curr_loc()].get_link()
        next_dest = next_link.get_link_endpoint(curr_host)
        curr_packet.set_curr_loc(next_dest.get_ip())

        # Acknowledgment packet received
        if curr_packet.get_type() == ACK_PACKET:
            print 'Acknowledged this shit'

            RTT = global_time - curr_packet.get_init_time()
            if RTT < curr_host.get_base_RTT():
                curr_host.set_base_RTT(RTT)
            curr_host.set_last_RTT(RTT)
            # if curr_host.get_tcp():
                # RTT = global_time - curr_packet.get_init_time()
                # if RTT < curr_host.get_base_RTT():
                #     curr_host.set_base_RTT(RTT)
                # # w = curr_host.get_window_size()
                # # if min(2 * w, (1 - GAMMA) * w + GAMMA * (base_RTT / RTT * w + ALPHA)) == 2 * w:
                # #     print "changing window size: double"
                # # else:
                # #     print "changing window size: gamma"
                # # curr_host.set_window_size(min(2 * w, (1 - GAMMA) * w + GAMMA * (base_RTT / RTT * w + ALPHA)))
                # # print "changing window size:", curr_host.get_window_size()
                # # # if curr_host.get_ip() == 'S1':
                # # window_size_dict[curr_host.get_flow_id()].append((global_time, curr_host.get_window_size()))
                # curr_host.set_last_RTT(RTT)
            if not curr_host.get_tcp():
                if curr_host.get_window_size() < curr_host.get_threshold():
                    curr_host.set_window_size(curr_host.get_window_size() + 1.0)
                
                else:
                    curr_host.set_window_size(curr_host.get_window_size() + 1.0 / curr_host.get_window_size())
                print "window size 1: %f, threshold: %f" % (curr_host.get_window_size(), curr_host.get_threshold())
                window_size_dict[curr_host.get_flow_id()].append((global_time, curr_host.get_window_size()))

            # Insert acknowledgement into dictionary
            if curr_packet.packet_id in acknowledged_packets:
                acknowledged_packets[curr_packet.packet_id] += 1
                if not curr_host.get_tcp():
                    if acknowledged_packets[curr_packet.packet_id] > 3:
                        acknowledged_packets[curr_packet.packet_id] -= 3
                        curr_host.set_window_size(curr_host.get_window_size() / 2.0)
                        curr_host.set_threshold(curr_host.get_window_size())
                        print "window size 2:", curr_host.get_window_size()
                        window_size_dict[curr_host.get_flow_id()].append((global_time, curr_host.get_window_size()))
                        exit(1)
                        print "threshold:", curr_host.get_threshold()
            else:
                acknowledged_packets[curr_packet.packet_id] = 1
                # Perform this ack only based on certain acks
                curr_host.set_window_count(curr_host.get_window_count() - 1)

            # Convert packet from host queue into event and insert into buffer
            # if curr_host.get_window_count() < curr_host.get_window_size():
            while curr_host.get_window_count() < curr_host.get_window_size():
                pkt = curr_host.remove_packet()
                if pkt != None:
                    assert pkt.get_curr_loc() != None
                    if next_link.insert_into_buffer(pkt, pkt.get_capacity()):
                        curr_host.set_window_count(curr_host.get_window_count()+1)
                        if len(next_link.packet_queue) == 1:
                            create_packet_received_event(global_time, pkt, next_link, curr_host.get_ip(), next_dest.get_ip())

                        dst_time = global_time + TIMEOUT_VAL
                        create_timeout_event(dst_time, pkt, global_time)
                    else:
                        # Put the packet back into the host queue
                        curr_host.insert_packet(pkt)
                        break
                else:
                    break
        # Process other packets received by the hosts
        else:
            print 'Received host'
            print 'Running...'

            # Create acknowlegment packet with same packet id as the original packet
            p = Packet(ACK_PACKET, 1, curr_host.get_ip(), curr_packet.get_src(), next_dest.get_ip(), global_time)
            p.packet_id = curr_packet.packet_id

            # Insert ack packet into the buffer
            insert_packet_into_buffer(p, next_link, dropped_packets, global_time, next_dest)


def process_timeout_event(event_top, global_time, hosts, dropped_packets, acknowledged_packets):
    curr_packet = event_top.get_data()
    curr_host = hosts[curr_packet.get_src()]
    p_id = curr_packet.packet_id

    # Packet was acknowledged beforehand
    # if p_id in acknowledged_packets:
    #     if acknowledged_packets[p_id] == 1:
    #         del acknowledged_packets[p_id]
    #     else:
    #         acknowledged_packets[p_id] -= 1
    #         assert acknowledged_packets[p_id] > 0
    if p_id not in acknowledged_packets:
        # print 'Creating timeout packet'
        if not curr_host.get_tcp():
            curr_host.set_threshold(curr_host.get_window_size() / 2.0)
            curr_host.set_window_size(1)
            print "window size 3: %f, threshold: %f" % (curr_host.get_window_size(), curr_host.get_threshold())

        curr_link = curr_host.get_link()
        next_hop = curr_link.get_link_endpoint(curr_host)
        # Create new packet
        p = Packet(MESSAGE_PACKET, 1, curr_packet.get_src(), curr_packet.get_dest(), next_hop.get_ip(), global_time)
        p.packet_id = curr_packet.packet_id
        dropped_packets.append(p)

        # Attempt to insert new packet back to buffer
        insert_packet_into_buffer(p, curr_link, dropped_packets, global_time, next_hop)


        # if curr_link.insert_into_buffer(p, p.get_capacity()):
        #     if len(curr_link.packet_queue) == 1:
        #         assert p.get_curr_loc() == next_hop.get_ip()
        #         create_packet_received_event(global_time, p, curr_link, p.get_src(), next_hop.get_ip())
        # else:

        # # Create a timeout event for the new packet
        #     dropped_packets.append(p)
        #     curr_link.increment_drop_packets()
        #     #assert False

        dst_time = global_time + TIMEOUT_VAL
        create_timeout_event(dst_time, p, global_time)

    print 'Timeout happened!!!!!'
    print 'Other'