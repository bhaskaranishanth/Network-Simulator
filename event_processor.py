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
    # assert src[0] not in 'ST' or dest[0] not in 'ST'
    new_event = Event(PACKET_RECEIVED, 
        global_time + pkt.get_capacity() / link.get_prop_time() + link.get_trans_time(), 
        src, dest, pkt)
    # print 'Received event: ', new_event
    eq.put((new_event.get_initial_time(), new_event))
    return new_event

def create_routing_packet_received_event(global_time, pkt, link, src, dest):
    """
    Takes in packet and link information, creates a PACKET_RECEIVED
    event and adds it to the global queue. Returns the event
    to make it easier to debug code.
    """
    # assert src[0] not in 'ST' or dest[0] not in 'ST'
    new_event = Event(ROUTING_PACKET_RECEIVED, global_time, src, dest, pkt)
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
        # print event_top.get_src()
        # print event_top.get_dest()
        # print links[l].get_endpoints()[0]
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
    print curr_packet
    print next_hop
    assert curr_packet.get_curr_loc() == next_hop.get_ip()

    # Insert packet into buffer
    if next_link.insert_into_buffer(curr_packet, curr_packet.get_capacity()):
        if next_link.get_free_time() <= global_time:
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
    assert routing_pkt.get_curr_loc() == None

    # Insert packet into buffer
    if next_link.insert_into_buffer(routing_pkt, routing_pkt.get_capacity()):
        if next_link.get_free_time() <= global_time:
            if len(next_link.packet_queue) == 1:
                print 'Creating received event from top element of queue'
                create_routing_packet_received_event(global_time, routing_pkt, next_link, next_link.get_link_endpoint(next_hop).get_ip(), next_hop.get_ip())
                # create_routing_packet_received_event(global_time, routing_pkt, link, host_id, dest):

    else:
        dropped_packets.append(routing_pkt)
        next_link.increment_drop_packets()


def create_timeout_event(end_time, pkt):
    """
    Takes in end time and packet, creates a TIMEOUT_EVENT
    event and adds it to the global queue. Returns the event
    to make it easier to debug code.
    """

    timeout_event = Event(TIMEOUT_EVENT, end_time, pkt.get_src(), pkt.get_dest(), pkt)
    eq.put((timeout_event.get_initial_time(), timeout_event))
    return timeout_event

def process_routing_packet_received_event(event_top, hosts, dropped_packets, global_time, routers):
    # Ignore routing packets sent to host
    if event_top.get_dest() in hosts:
        return 

    # If routing table is not updated, we return
    curr_router = event_top.get_dest()
    weight_table = routers[curr_router].get_weight_table()
    routing_pkt = event_top.get_data()
    print weight_table
    print type(routing_pkt.get_src())
    curr_entity = routers if routing_pkt.get_src() in routers else hosts
    pkt_src = curr_entity[routing_pkt.get_src()]

    print "curr router: ", routers[curr_router]
    print 'pkt source: ', routing_pkt

    if weight_table[pkt_src][1] <= routing_pkt.get_payload():
        print "current weight:", weight_table[pkt_src][1]
        print "new weight:", routing_pkt.get_payload()
        assert False
        return


    # Update packet weight
    hop_entity = routers if event_top.get_src() in routers else hosts
    weight_table[pkt_src] = (hop_entity[event_top.get_src()], routing_pkt.get_payload())
    print 'Modified wieht table: ', weight_table
    # if hop_entity == routers:
    #     routers[curr_router].get_routing_table()[pkt_src] = hop_entity[event_top.get_src()]
    routers[curr_router].get_routing_table()[pkt_src] = hop_entity[event_top.get_src()]
    print routers[curr_router]



    # Create new packets for all its neighbors
    for l in routers[curr_router].get_links():
        dest = l.get_link_endpoint(routers[curr_router])
        new_weight = l.get_weight() + routing_pkt.get_payload()
        assert routing_pkt.get_src() in hosts
        new_pkt = Packet(ROUTER_PACKET, new_weight, routing_pkt.get_src(), None, None, None)
        insert_routing_packet_into_buffer(new_pkt, l, dropped_packets, global_time, dest)



def process_packet_received_event(event_top, global_time, links, routers, hosts, window_size, dropped_packets, acknowledged_packets):
    # Retrieve the previous link and remove the received
    # packet from the buffer
    print 'Processing packet received event '
    print '*' * 40
    curr_link = get_link_from_event(event_top, links)
    curr_packet = event_top.get_data()
    curr_link.remove_from_buffer(curr_packet, curr_packet.get_capacity())
    print curr_packet
    # print 'Removing from buffer.....'
    # print curr_link

    # If there are still elements in the buffer, take the first packet 
    # out and send it across the link
    if len(curr_link.packet_queue) != 0:
        next_packet = curr_link.packet_queue[0]

        # Determine the source and destination of the new event to add to queue
        curr_entity = routers if next_packet.get_curr_loc() in routers else hosts
        next_dest = next_packet.get_curr_loc()
        curr_src = curr_link.get_link_endpoint(curr_entity[next_packet.get_curr_loc()]).get_ip()

        # Create new event with the same packet
        create_packet_received_event(global_time, next_packet, curr_link, curr_src, next_dest)

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

            # Insert acknowledgement into dictionary
            if curr_packet.packet_id in acknowledged_packets:
                acknowledged_packets[curr_packet.packet_id] += 1
            else:
                acknowledged_packets[curr_packet.packet_id] = 1
                # Perform this ack only based on certain acks
                curr_host.set_window_count(curr_host.get_window_count()-1)

            # Convert packet from host queue into event and insert into buffer
            if curr_host.get_window_count() < window_size:
                while next_link.get_num_packets() < window_size:
                    pkt = curr_host.remove_packet()
                    if pkt != None:
                        assert pkt.get_curr_loc() != None
                        if next_link.insert_into_buffer(pkt, pkt.get_capacity()):
                            assert next_link.get_free_time() <= global_time
                            if next_link.get_free_time() <= global_time:
                                curr_host.set_window_count(curr_host.get_window_count()+1)
                                if len(next_link.packet_queue) == 1:
                                    create_packet_received_event(global_time, curr_packet, next_link, curr_host.get_ip(), next_dest.get_ip())

                                dst_time = global_time + TIMEOUT_VAL
                                create_timeout_event(dst_time, pkt)
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
    if p_id in acknowledged_packets:
        if acknowledged_packets[p_id] == 1:
            del acknowledged_packets[p_id]
        else:
            acknowledged_packets[p_id] -= 1
    else:
        # print 'Creating timeout packet'
        curr_link = curr_host.get_link()
        next_hop = curr_link.get_link_endpoint(curr_host)
        # Create new packet
        p = Packet(MESSAGE_PACKET, 1, curr_packet.get_src(), curr_packet.get_dest(), next_hop.get_ip(), global_time)
        p.packet_id = curr_packet.packet_id
        dropped_packets.append(p)

        # Attempt to insert new packet back to buffer
        # insert_packet_into_buffer(p, curr_link, dropped_packets, global_time, next_hop)


        if curr_link.insert_into_buffer(p, p.get_capacity()):
            # Deal with WINDOW SHIT HERE
            hosts[curr_packet.get_src()].set_window_count(hosts[curr_packet.get_src()].get_window_count()+1)
            if curr_link.get_free_time() <= global_time:
                if len(curr_link.packet_queue) == 1:
                    assert p.get_curr_loc() == next_hop
                    create_packet_received_event(global_time, p, curr_link, p.get_src(), next_hop)
        else:

        # Create a timeout event for the new packet
            dropped_packets.append(p)
            curr_link.increment_drop_packets()
            #assert False

        dst_time = global_time + TIMEOUT_VAL
        create_timeout_event(dst_time, p)

    print 'Timeout happened!!!!!'
    print 'Other'