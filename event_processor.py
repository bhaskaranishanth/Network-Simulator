from packet import *
from constants import *
from event import *
from eventqueue import *
from router import *
from link import *
from host import *

class EventProcessor:
    def __init__(self, ec, hosts, routers, links, flows):
        self.ec = ec
        self.hosts = hosts
        self.routers = routers
        self.links = links
        self.flows = flows
        

    def get_link_from_event(self, event_top, links):
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
        if curr_link == None:
            print "exp_packet_id: ", event_top.get_src()
            print "exp_packet_id: ", event_top.get_dest()
            assert curr_link != None
        return curr_link


    def insert_packet_into_buffer(self, curr_packet, next_link, dropped_packets, global_time, next_hop):
        """
        Function takes the given packet, converts it into an event, and adds it to the
        link's buffer. If the packet is not able to be added to the buffer, it
        will be dropped.
        """
        print 'Insert packet into buffer..'
        print 'Curr loc', curr_packet.get_curr_loc()
        print 'Nxt:', next_hop
        assert curr_packet.get_curr_loc() == next_hop.get_ip()

        # Insert packet into buffer
        if next_link.insert_into_buffer(curr_packet):
            # if len(next_link.packet_queue) == 1:
            #     print 'Creating received event from top element of queue'
            #     next_link.remove_from_buffer(curr_packet, curr_packet.get_capacity())

            #     self.ec.create_packet_received_event(global_time, curr_packet, next_link, next_link.get_link_endpoint(next_hop).get_ip(), next_hop.get_ip())
            return True
        else:
            dropped_packets.append(curr_packet)
            next_link.increment_drop_packets()
            return False

    def insert_routing_packet_into_buffer(self, routing_pkt, next_link, dropped_packets, global_time, next_hop):
        """
        Function takes the given packet, converts it into an event, and adds it to the
        link's buffer. If the packet is not able to be added to the buffer, it
        will be dropped.
        """
        assert routing_pkt.get_dest() == None
        assert routing_pkt.get_type() == ROUTER_PACKET

        # Insert packet into buffer
        if next_link.insert_into_buffer(routing_pkt):
            return True
            # if len(next_link.packet_queue) == 1:
            #     self.ec.create_routing_packet_received_event(global_time, routing_pkt, next_link, next_link.get_link_endpoint(next_hop).get_ip(), next_hop.get_ip())
        else:
            dropped_packets.append(routing_pkt)
            next_link.increment_drop_packets()
            return False

    def process_remove_from_buffer_event(self, event_top, global_time):
        curr_link = self.get_link_from_event(event_top, self.links)
        assert len(curr_link.packet_queue) > 0
        curr_packet = event_top.get_data()
        assert curr_packet == curr_link.packet_queue[0]
        curr_link.remove_from_buffer(curr_packet, curr_packet.get_capacity())
        # print curr_packet
        curr_dest = curr_packet.get_curr_loc()
        curr_entity = self.routers if curr_dest in self.routers else self.hosts
        curr_src = curr_link.get_link_endpoint(curr_entity[curr_dest]).get_ip()
        end_time = global_time + curr_link.get_prop_time() + \
            curr_packet.get_capacity() / curr_link.get_trans_time()

        if curr_packet.get_type() == ROUTER_PACKET:
            self.ec.create_routing_packet_received_event(end_time, curr_packet, 
                curr_link, curr_src, curr_dest)
        else:
            self.ec.create_packet_received_event(end_time, curr_packet, 
                curr_link, curr_src, curr_dest)

        curr_link.set_direction((curr_src, curr_dest))
        curr_link.set_last_pkt_dest_time(end_time)

        if len(curr_link.packet_queue) > 0:
            next_pkt = curr_link.packet_queue[0]
            next_dest = next_pkt.get_curr_loc()
            next_entity = self.routers if next_dest in self.routers else self.hosts
            next_src = curr_link.get_link_endpoint(next_entity[next_dest]).get_ip()
            print "next source", type(next_src)
            print "next dest", type(next_dest)
            assert curr_link.get_direction() != None
            if curr_link.get_direction() == (next_src, next_dest):
                self.ec.create_remove_from_buffer_event(global_time + next_pkt.get_capacity() / curr_link.get_trans_time(), next_pkt, next_src, next_dest)
            elif curr_link.get_direction() == (next_dest, next_src):
                next_time = max(curr_link.get_last_pkt_dest_time(), global_time)
                self.ec.create_remove_from_buffer_event(next_time, next_pkt, next_dest, next_src)
            else:
                print curr_link.get_direction()
                assert False


    def process_routing_packet_received_event(self, event_top, hosts, links, dropped_packets, global_time, routers):
        # curr_link = self.get_link_from_event(event_top, links)
        curr_packet = event_top.get_data()
        assert curr_packet.get_type() == ROUTER_PACKET
        # curr_link.remove_from_buffer(curr_packet, curr_packet.get_capacity())

        # self.ec.create_next_packet_event(curr_link, global_time, event_top, hosts, routers)
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

            if len(l.packet_queue) == 0:
                if l.get_direction() == (curr_router, dest.get_ip()):
                    # Insert packet into the next link's buffer
                    if self.insert_routing_packet_into_buffer(new_pkt, l, dropped_packets, global_time, dest):
                        self.ec.create_remove_from_buffer_event(global_time, new_pkt, curr_router, dest.get_ip())
                elif l.get_direction() == (dest.get_ip(), curr_router):
                    if self.insert_routing_packet_into_buffer(new_pkt, l, dropped_packets, global_time, dest):
                        next_time = max(l.get_last_pkt_dest_time(), global_time)
                        self.ec.create_remove_from_buffer_event(next_time, new_pkt, dest.get_ip(), curr_router)
                else:
                    print "link: ", l
                    print "Direction: ", l.get_direction()
                    print "Curr: ", (curr_router, dest.get_ip())
                    assert False
            else:
                self.insert_routing_packet_into_buffer(new_pkt, l, dropped_packets, global_time, dest)
            # self.insert_routing_packet_into_buffer(new_pkt, l, dropped_packets, global_time, dest)


    def process_packet_received_event(self, event_top, global_time, links, routers, hosts, dropped_packets, acknowledged_packets, window_size_dict):
        # Retrieve the previous link and remove the received
        # packet from the buffer
        print 'Processing packet received event '
        print '*' * 40
        # curr_link = self.get_link_from_event(event_top, links)
        curr_packet = event_top.get_data()
        assert curr_packet.get_type() != ROUTER_PACKET
        # curr_link.remove_from_buffer(curr_packet, curr_packet.get_capacity())
        # print curr_packet

        # self.ec.create_next_packet_event(curr_link, global_time, event_top, hosts, routers)

        # Sending packets into the next buffer
        # Router component
        if curr_packet.get_curr_loc() in routers:
            print 'Packet received in router....'     
            curr_router = routers[curr_packet.get_curr_loc()]
            next_hop = curr_router.get_routing_table()[hosts[curr_packet.get_dest()]]
            next_link = curr_router.get_link_for_dest(next_hop)
            curr_packet.set_curr_loc(next_hop.get_ip())

            if len(next_link.packet_queue) == 0:
                if next_link.get_direction() == (curr_router.get_ip(), next_hop.get_ip()):
                    # Insert packet into the next link's buffer
                    if self.insert_packet_into_buffer(curr_packet, next_link, dropped_packets, global_time, next_hop):
                        self.ec.create_remove_from_buffer_event(global_time, curr_packet, curr_router.get_ip(), next_hop.get_ip())
                elif next_link.get_direction() == (next_hop.get_ip(), curr_router.get_ip()):
                    if self.insert_packet_into_buffer(curr_packet, next_link, dropped_packets, global_time, next_hop):
                        next_time = max(next_link.get_last_pkt_dest_time(), global_time)
                        self.ec.create_remove_from_buffer_event(next_time, curr_packet, next_hop.get_ip(), curr_router.get_ip())
                else:
                    print "link: ", next_link
                    print "Direction: ", next_link.get_direction()
                    print "Curr: ", (curr_router.get_ip(), next_hop.get_ip())
                    assert False
            else:
                self.insert_packet_into_buffer(curr_packet, next_link, dropped_packets, global_time, next_hop)

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
                print "changing window size base RTT", curr_host.get_base_RTT()
                print "changing window size last RTT", curr_host.get_last_RTT()
                # if not curr_host.get_tcp():
                #     print "performing Reno"
                #     exit(1)
                #     if curr_host.get_window_size() < curr_host.get_threshold():
                #         curr_host.set_window_size(curr_host.get_window_size() + 1.0)
                #     else:
                #         curr_host.set_window_size(curr_host.get_window_size() + 1.0 / curr_host.get_window_size())
                #     print "window size 1: %f, threshold: %f" % (curr_host.get_window_size(), curr_host.get_threshold())

                window_size_dict[curr_host.get_flow_id()].append((global_time, curr_host.get_window_size()))

                # Insert acknowledgement into dictionary

                curr_host.set_bytes_received(curr_host.get_bytes_received() + MESSAGE_SIZE)
                if curr_packet.get_packet_id() in acknowledged_packets:
                    acknowledged_packets[curr_packet.get_packet_id()] += 1
                    # if not curr_host.get_tcp():
                    #     print "performing Reno2"
                    #     exit(1)
                    #     print "exp_packe Location 1: ", acknowledged_packets[curr_packet.get_packet_id()], " and id: ", curr_packet.get_packet_id()
                    #     if acknowledged_packets[curr_packet.get_packet_id()] > 3:
                    #         acknowledged_packets[curr_packet.get_packet_id()] = -3

                    #         # Change window and threshold to w/2 
                    #         print "exp_packe before: ", curr_host.get_window_size()

                    #         curr_host.set_window_size(curr_host.get_window_size() / 2.0)
                    #         print "exp_packe after: ", curr_host.get_window_size()
                    #         curr_host.set_threshold(curr_host.get_window_size())
                    #         print "window size 2:", curr_host.get_window_size()

                    window_size_dict[curr_host.get_flow_id()].append((global_time, curr_host.get_window_size()))
                    #         # exit(1)

                    #         print "threshold:", curr_host.get_threshold()
                    #         # print "exp_packe: ", next_dest
                    #         # print 'exp_packe ', curr_packet.get_packet_id()
                    #         # print "exp_packe ", acknowledged_packets
                    #         # exit(1)


                    #         # Retransmit same packet
                    #         curr_link = curr_host.get_link()
                    #         next_hop = curr_link.get_link_endpoint(curr_host)
                    #         p = Packet(MESSAGE_PACKET, 1, curr_packet.get_dest(), curr_packet.get_src(), next_hop.get_ip(), global_time)

                    #         # Send the packet id greater than the previous packet
                    #         p.set_packet_id(curr_packet.get_packet_id() + 1)
                    #         dropped_packets.append(p)

                    #         if curr_link.insert_into_buffer(p):
                    #             print "exp_packe inserted into buffer"
                    #             if len(curr_link.packet_queue) == 1:
                    #                 assert p.get_curr_loc() == next_hop.get_ip()
                    #                 curr_link.remove_from_buffer(p, p.get_capacity())

                    #                 self.ec.create_packet_received_event(global_time, p, curr_link, p.get_src(), next_hop.get_ip())
                    #         else:
                    #             dropped_packets.append(p)
                    #             curr_link.increment_drop_packets()

                        #     # exit(1)
                        # # Receiving an extra ack packet should not do anything besides
                        # # increasing the window size of the host
                        # elif acknowledged_packets[curr_packet.get_packet_id()] < -1:
                        #     acknowledged_packets[curr_packet.get_packet_id()] = -3
                        # else:
                        #     curr_host.set_window_size(curr_host.get_window_size() + 1)

                else:
                    # Store ack packet id for the first time
                    acknowledged_packets[curr_packet.get_packet_id()] = 1
                    curr_host.set_window_count(curr_host.get_window_count() - 1)
                    # curr_host.set_bytes_received(curr_host.get_bytes_received() + MESSAGE_SIZE)
                    print "exp_packe t waht, "

                    for h in hosts:
                        if curr_packet.get_packet_id() in hosts[h].get_outstanding_pkts():
                            hosts[h].del_outstanding_pkt(curr_packet.get_packet_id())
                            break


                    # exit(1)

                # Convert packet from host queue into event and insert into buffer
                # if curr_host.get_window_count() < curr_host.get_window_size():
                while curr_host.get_window_count() < curr_host.get_window_size():
                    pkt = curr_host.remove_packet()
                    if pkt != None:
                        assert pkt.get_curr_loc() != None
                        self.ec.create_timeout_event(TIMEOUT_VAL + global_time, pkt)
                        if len(next_link.packet_queue) == 0:
                            if next_link.get_direction() == (curr_host.get_ip(), next_dest.get_ip()):
                                # Insert packet into the next link's buffer
                                if self.insert_packet_into_buffer(pkt, next_link, dropped_packets, global_time, next_dest):
                                    self.ec.create_remove_from_buffer_event(global_time, pkt, curr_host.get_ip(), next_dest.get_ip())
                                    curr_host.set_window_count(curr_host.get_window_count()+1)
                                # else:
                                #     assert False
                            elif next_link.get_direction() == (next_dest.get_ip(), curr_host.get_ip()):
                                if self.insert_packet_into_buffer(pkt, next_link, dropped_packets, global_time, next_dest):
                                    next_time = max(next_link.get_last_pkt_dest_time(), global_time)
                                    self.ec.create_remove_from_buffer_event(next_time, pkt, next_dest.get_ip(), curr_host.get_ip())
                                    curr_host.set_window_count(curr_host.get_window_count()+1)
                                # else:
                                #     assert False
                            else:
                                assert False
                        else:
                            if self.insert_packet_into_buffer(pkt, next_link, dropped_packets, global_time, next_dest):
                                curr_host.set_window_count(curr_host.get_window_count()+1)
                            # else:
                            #     # TODO
                            #     assert False


                        # if next_link.insert_into_buffer(pkt):
                        #     curr_host.set_window_count(curr_host.get_window_count()+1)
                        #     if len(next_link.packet_queue) == 1:
                        #         next_link.remove_from_buffer(pkt, pkt.get_capacity())

                        #         self.ec.create_packet_received_event(global_time, pkt, next_link, curr_host.get_ip(), next_dest.get_ip())

                        #     dst_time = global_time + TIMEOUT_VAL
                        #     self.ec.create_timeout_event(dst_time, pkt, global_time)
                        # else:
                        #     # Put the packet back into the host queue
                        #     curr_host.insert_packet(pkt)
                        #     break
                    else:
                        break
            # Process other packets received by the hosts
            else:
                print 'Received host'
                print 'Running...'

                # Create acknowlegment packet with same packet id as the original packet
                p = Packet(ACK_PACKET, 1, curr_host.get_ip(), curr_packet.get_src(), next_dest.get_ip(), global_time)
                p.set_packet_id(curr_packet.get_packet_id())
                next_hop = next_dest

                if len(next_link.packet_queue) == 0:
                    if next_link.get_direction() == (curr_host.get_ip(), next_hop.get_ip()):
                        # Insert packet into the next link's buffer
                        if self.insert_packet_into_buffer(p, next_link, dropped_packets, global_time, next_hop):
                            self.ec.create_remove_from_buffer_event(global_time, p, curr_host.get_ip(), next_hop.get_ip())
                    elif next_link.get_direction() == (next_hop.get_ip(), curr_host.get_ip()):
                        if self.insert_packet_into_buffer(p, next_link, dropped_packets, global_time, next_hop):
                            next_time = max(next_link.get_last_pkt_dest_time(), global_time)
                            self.ec.create_remove_from_buffer_event(next_time, p, next_hop.get_ip(), curr_host.get_ip())
                    else:
                        assert False
                else:
                    self.insert_packet_into_buffer(p, next_link, dropped_packets, global_time, next_hop)


                # last_recv_pkt = curr_host.get_last_received_pkt_id()
                # exp_packet_id = 1 if last_recv_pkt == None else (last_recv_pkt + 1)
                # # print "new pkt: ", p
                # print "last_recv_pkt: ", last_recv_pkt
                # print "exp_packet_id: ", exp_packet_id, " curr_packet_id: ", curr_packet.get_packet_id()

                # # Update the received packets and missing packets list in the host
                # if exp_packet_id != curr_packet.get_packet_id():
                #     # Takes care of packets sent by timeouts
                #     if curr_packet.get_packet_id() not in curr_host.get_received_pkt_ids():
                #         assert(exp_packet_id < curr_packet.get_packet_id())
                #         print "Invalid packet ids received"
                #         print "Expected id: ", exp_packet_id
                #         print "Current id: ", curr_packet.get_packet_id()
                #         p = Packet(ACK_PACKET, 1, curr_host.get_ip(), curr_packet.get_src(), next_dest.get_ip(), global_time)
                #         p.set_packet_id(exp_packet_id - 1)
                #         print p
                #         # Insert ack packet into the buffer
                #         self.insert_packet_into_buffer(p, next_link, dropped_packets, global_time, next_dest)
                #         # exit(1)
                #     # exit(1)
                # else:
                #     # Create acknowlegment packet with same packet id as the original packet
                #     # p = Packet(ACK_PACKET, 1, curr_host.get_ip(), curr_packet.get_src(), next_dest.get_ip(), global_time)
                #     # p.set_packet_id(curr_packet.get_packet_id())

                #     # # Insert ack packet into the buffer
                #     # insert_packet_into_buffer(p, next_link, dropped_packets, global_time, next_dest)

                #     # Add it to the received packet list
                #     curr_host.insert_recv_pkt(curr_packet)
                #     # Set the last packed received to be the packet id we added
                #     curr_host.set_last_received_pkt_id(curr_packet.get_packet_id())

                #     # Update the last received packet
                #     # This newest one can be in the missing packets list
                #     curr_host.update_last_recv_pkt()

                #     print "The last non-missing value is : ", curr_host.get_last_received_pkt_id()
                #     # print curr_host.get_received_pkt_ids()


    def process_timeout_event(self, event_top, global_time, hosts, dropped_packets, acknowledged_packets):
        curr_packet = event_top.get_data()
        curr_host = hosts[curr_packet.get_src()]
        p_id = curr_packet.get_packet_id()

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
            p.set_packet_id(curr_packet.get_packet_id())
            dropped_packets.append(p)

            # Attempt to insert new packet back to buffer
            # self.insert_packet_into_buffer(p, curr_link, dropped_packets, global_time, next_hop)
            if len(curr_link.packet_queue) == 0:
                if curr_link.get_direction() == (curr_host.get_ip(), next_hop.get_ip()):
                    # Insert packet into the next link's buffer
                    if self.insert_packet_into_buffer(p, curr_link, dropped_packets, global_time, next_hop):
                        self.ec.create_remove_from_buffer_event(global_time, p, curr_host.get_ip(), next_hop.get_ip())
                elif curr_link.get_direction() == (next_hop.get_ip(), curr_host.get_ip()):
                    if self.insert_packet_into_buffer(p, curr_link, dropped_packets, global_time, next_hop):
                        next_time = max(curr_link.get_last_pkt_dest_time(), global_time)
                        self.ec.create_remove_from_buffer_event(next_time, p, next_hop.get_ip(), curr_host.get_ip())
                else:
                    assert False
            else:
                self.insert_packet_into_buffer(p, curr_link, dropped_packets, global_time, next_hop)

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
            self.ec.create_timeout_event(dst_time, p)

        print 'Timeout happened!!!!!'
        print 'Other'