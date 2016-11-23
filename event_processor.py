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
        global_time + pkt.get_capacity() / link.get_prop_time() + link.get_trans_time(), 
        src, dest, pkt)
    eq.put((new_event.get_initial_time(), new_event))
    return new_event


def get_link_from_event(event_top, links):
    """
    From the provided event and a list of links, the function
    determines which link is being used.
    """
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
    return curr_link


def insert_packet_into_buffer(curr_packet, next_link, dropped_packets, global_time, next_hop):
    """
    Function takes the given packet, converts it into an event, and adds it to the
    link's buffer. If the packet is not able to be added to the buffer, it
    will be dropped.
    """
    # Insert packet into buffer
    if next_link.insert_into_buffer(curr_packet, curr_packet.get_capacity()):
        if next_link.get_free_time() <= global_time:
            if len(next_link.packet_queue) == 1:
                # print 'Next packet: ', curr_packet
                # print next_hop
                # assert next_hop not in hosts.values()
                # assert next_hop not in hosts
                create_packet_received_event(global_time, curr_packet, next_link, curr_packet.get_curr_loc(), next_hop.get_ip())

    else:
        dropped_packets.append(curr_packet)
        next_link.increment_drop_packets()
        #assert False


def create_timeout_event(end_time, pkt):
    """
    Takes in end time and packet, creates a TIMEOUT_EVENT
    event and adds it to the global queue. Returns the event
    to make it easier to debug code.
    """

    timeout_event = Event(TIMEOUT_EVENT, end_time, pkt.get_src(), pkt.get_dest(), pkt)
    eq.put((timeout_event.get_initial_time(), timeout_event))
    return timeout_event



def process_packet_received_event(event_top, global_time, links, routers, hosts, window_size, dropped_packets, acknowledged_packets):
    # Retrieve the previous link and remove the received
    # packet from the buffer
    curr_link = get_link_from_event(event_top, links)
    curr_packet = event_top.get_data()
    curr_link.remove_from_buffer(curr_packet, curr_packet.get_capacity())
    print 'Removing from buffer.....'
    print curr_link

    # If there are still elements in the buffer, take the first packet 
    # out and send it across the link
    if len(curr_link.packet_queue) != 0:
        next_packet = curr_link.packet_queue[0]

        # TODO: If curr_src represents destination, then shouldn't hosts
        # handle acknowledgement here

        # Determine the source and destination of the new event to add to queue
        curr_entity = routers if next_packet.get_curr_loc() in routers else hosts
        curr_src = curr_entity[next_packet.get_curr_loc()]
        next_dest = curr_link.get_link_endpoint(curr_src)

        # Create new event with the same packet
        create_packet_received_event(global_time, next_packet, curr_link, curr_src.get_ip(), next_dest)
        print 'Next packet: ', next_packet
        print next_dest
        # assert next_dest not in hosts.values()
        # assert next_dest not in hosts


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

        insert_packet_into_buffer(curr_packet, next_link, dropped_packets, global_time, next_hop)


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

                                    next_hop = next_link.get_link_endpoint(curr_host)
                                    # next_hop = curr_router.get_routing_table()[hosts[pkt.get_src()]].get_ip()
                                    # assert next_hop not in hosts
                                    create_packet_received_event(global_time, curr_packet, next_link, pkt.get_src(), next_hop)

                                dst_time = global_time + TIMEOUT_VAL
                                create_timeout_event(dst_time, pkt)


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
                    # assert next_dest not in hosts.values()
                    # assert next_dest not in hosts
                    create_packet_received_event(global_time, p, next_link, curr_src.get_ip(), next_dest)

            else:
                dropped_packets.append(curr_packet)
                next_link.increment_drop_packets()
                #assert False




def process_timeout_event(event_top, global_time, hosts, dropped_packets, acknowledged_packets):
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