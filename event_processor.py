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
        

    def acknowledge(self, acknowledged_packets, p_id):
        if p_id in acknowledged_packets:
            acknowledged_packets[p_id] += 1
        else:
            acknowledged_packets[p_id] = 1

        return acknowledged_packets[p_id]

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


    def handle_packet_to_buffer_insertion(self, packet, link, dropped_packets, global_time, next_hop):
        """
        Handles the insertion of the given packet into the link's buffer. If the packet is not 
        able to be added to the buffer, it will be dropped.
        """
        print 'Insert packet into buffer..'
        print 'Curr loc', packet.get_curr_loc()
        print 'Nxt:', next_hop

        assert packet.get_curr_loc() == next_hop.get_ip()
        assert packet.get_type() in [MESSAGE_PACKET, ACK_PACKET, ROUTER_PACKET] 

        # Insert packet into buffer
        if link.insert_into_buffer(packet):
            return True
        else:
            dropped_packets.append(packet)
            link.increment_drop_packets()
            return False


    def insert_packet_into_buffer(self, link, curr_router, next_hop, packet, dropped_packets, global_time):
        """
        Takes any type of packet and inserts it into the buffer. Creates a remove_from_buffer_event
        indicating the time when packet should be removed.
        """
        src1_ip = curr_router.get_ip()
        src2_ip = next_hop.get_ip()

        assert src1_ip != src2_ip
        assert packet.get_type() in [MESSAGE_PACKET, ACK_PACKET, ROUTER_PACKET] 
        assert (packet.get_dest() == None) if packet.get_type() == ROUTER_PACKET else True

        if len(link.packet_queue) == 0:
            if link.get_direction() == (src1_ip, src2_ip):
                # Insert packet into the next link's buffer
                if self.handle_packet_to_buffer_insertion(packet, link, dropped_packets, global_time, next_hop):
                    self.ec.create_remove_from_buffer_event(global_time, packet, src1_ip, src2_ip)
                    return True
            elif link.get_direction() == (src2_ip, src1_ip):
                if self.handle_packet_to_buffer_insertion(packet, link, dropped_packets, global_time, next_hop):
                    next_time = max(link.get_last_pkt_dest_time(), global_time)
                    self.ec.create_remove_from_buffer_event(next_time, packet, src1_ip, src2_ip)
                    return True
            else:
                print "link: ", link
                print "Direction: ", link.get_direction()
                print "Curr: ", (src1_ip, src2_ip)
                assert False
        else:
            return self.handle_packet_to_buffer_insertion(packet, link, dropped_packets, global_time, next_hop)


    def process_remove_from_buffer_event(self, event_top, global_time):
        print "event details", event_top
        curr_link = self.get_link_from_event(event_top, self.links)
        assert len(curr_link.packet_queue) > 0
        curr_packet = event_top.get_data()
        print "current packet", curr_packet
        print "curr link", curr_link
        # curr_link.print_link_buffer()
        assert curr_packet == curr_link.packet_queue[0]
        curr_link.remove_from_buffer(curr_packet, curr_packet.get_capacity())
        assert curr_packet.get_packet_id() != 0

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
            print "next source", next_src
            print "next dest", next_dest
            assert curr_link.get_direction() != None
            if curr_link.get_direction() == (next_src, next_dest):
                self.ec.create_remove_from_buffer_event(global_time + next_pkt.get_capacity() / curr_link.get_trans_time(), next_pkt, next_src, next_dest)
            elif curr_link.get_direction() == (next_dest, next_src):
                next_time = max(curr_link.get_last_pkt_dest_time(), global_time)
                self.ec.create_remove_from_buffer_event(next_time, next_pkt, next_src, next_dest)
            else:
                print curr_link.get_direction()
                print "packet details", next_pkt
                assert False


    def process_routing_packet_received_event(self, event_top, hosts, links, dropped_packets, global_time, routers):
        # curr_link = self.get_link_from_event(event_top, links)
        curr_packet = event_top.get_data()
        assert curr_packet.get_type() == ROUTER_PACKET
        assert curr_packet.get_packet_id() != 0
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

            self.insert_packet_into_buffer(l, routers[curr_router], dest, new_pkt, dropped_packets, global_time)

    def process_packet_received_event(self, event_top, global_time, links, routers, hosts, dropped_packets, acknowledged_packets, window_size_dict, network):
        # Retrieve the previous link and remove the received
        # packet from the buffer
        print 'Processing packet received event '
        print '*' * 40

        # curr_link = self.get_link_from_event(event_top, links)
        curr_packet = event_top.get_data()
        print "Host: curr loc", curr_packet.get_curr_loc()
        assert curr_packet.get_type() != ROUTER_PACKET
        assert curr_packet.get_packet_id() != 0

        # curr_link.remove_from_buffer(curr_packet, curr_packet.get_capacity())
        # print curr_packet

        # self.ec.create_next_packet_event(curr_link, global_time, event_top, hosts, routers)

        # Sending packets into the next buffer
        # Router component
        if curr_packet.get_curr_loc() in routers:
            print 'Packet received in router....'     
            curr_router = routers[curr_packet.get_curr_loc()]
            next_hop = curr_router.get_routing_table()[hosts[curr_packet.get_dest()]]
            print "next hop", next_hop
            next_link = curr_router.get_link_for_dest(next_hop)
            curr_packet.set_curr_loc(next_hop.get_ip())

            self.insert_packet_into_buffer(next_link, curr_router, next_hop, curr_packet, dropped_packets, global_time)

        # Host receives a packet
        elif curr_packet.get_curr_loc() in hosts:
            print 'Host receives a packet'
            curr_host = hosts[curr_packet.get_curr_loc()]
            next_link = hosts[curr_packet.get_curr_loc()].get_link()
            next_dest = next_link.get_link_endpoint(curr_host)
            curr_packet.set_curr_loc(next_dest.get_ip())

            assert curr_packet.get_packet_id() != 0
            # assert curr_packet.get_actual_id() != 0


            # Acknowledgment packet received
            if curr_packet.get_type() == ACK_PACKET:
                print 'Acknowledged this shit'
                window_size_dict[curr_host.get_flow_id()].append((global_time, curr_host.get_window_size()))

                # Fast code
                RTT = global_time - curr_packet.get_init_time()
                if RTT < curr_host.get_base_RTT():
                    curr_host.set_base_RTT(RTT)
                curr_host.set_last_RTT(RTT)
                curr_host.set_bytes_received(curr_host.get_bytes_received() + MESSAGE_SIZE)

                if curr_host.flow_done():
                    return

                print "fast recovery A first time", curr_packet.get_packet_id()
                exp_packet_id = curr_host.get_outstanding_pkts()[0]
                # Duplicate ack
                # if curr_packet.get_packet_id() in acknowledged_packets:
                num_packs = self.acknowledge(acknowledged_packets, curr_packet.get_packet_id())
                if num_packs == 1:
                    curr_host.set_window_count(curr_host.get_window_count() - 1)
                    curr_host.del_outstanding_pkt(curr_packet.get_packet_id())

                # If we are in Reno
                if not curr_host.get_tcp():
                    # 18 (13), add 18 to ack packet
                    if exp_packet_id != curr_packet.get_packet_id():
                        num_last_rec = self.acknowledge(acknowledged_packets, exp_packet_id - 1)

                        if num_last_rec == 4:
                            print "fast recovery A pkt id", curr_packet.get_packet_id()
                            # print "fast recovery A actual id", curr_packet.get_actual_id()
                            # assert curr_host.get_fast_recovery() == 0
                            curr_host.set_fast_recovery(1)
                            # Retransmit lost packet
                            next_link = curr_host.get_link()
                            next_hop = next_link.get_link_endpoint(curr_host)
                            p = Packet(MESSAGE_PACKET, 1, curr_host.get_ip(), curr_packet.get_src(), next_hop.get_ip(), global_time)
                            p.set_packet_id(exp_packet_id)
                            # p.set_actual_id(curr_packet.get_packet_id() + 1)
                            self.insert_packet_into_buffer(next_link, curr_host, next_hop, p, dropped_packets, global_time)
                                # curr_host.set_window_count(curr_host.get_window_count() + 1)

                            # Change window and threshold to w/2 
                            curr_host.set_window_size(curr_host.get_window_size() / 2.0 + 3)
                            curr_host.set_threshold(max(curr_host.get_window_size() - 3, 2.0))
                            
                        elif num_last_rec > 4:
                            curr_host.set_window_size(curr_host.get_window_size() + 1)

                    else:
                        curr_host.set_fast_recovery(0)
                    # if curr_packet.get_actual_id() not in acknowledged_packets:
                    #     print "fast recovery A ack packets", acknowledged_packets
                    #     acknowledged_packets[curr_packet.get_actual_id()] = 1
                    #     curr_host.del_outstanding_pkt(curr_packet.get_actual_id())

                    # if acknowledged_packets[curr_packet.get_packet_id()] == 4:

                    if not curr_host.get_fast_recovery():
                        if curr_host.get_window_size() < curr_host.get_threshold():
                            curr_host.set_window_size(curr_host.get_window_size() + 1.0)
                        else:
                            curr_host.set_window_size(curr_host.get_window_size() + 1.0 / curr_host.get_window_size())

                # else:
                #     # Store ack packet id for the first time
                #     # assert curr_packet.get_packet_id() == curr_packet.get_actual_id()
                #     self.acknowledge(acknowledged_packets, curr_packet.get_packet_id())
                #     # print "fast recovery A outstanding", curr_host.get_outstanding_pkts()
                #     curr_host.del_outstanding_pkt(curr_packet.get_packet_id())

                #     # If Reno
                #     if not curr_host.get_tcp():
                #         if curr_host.get_outstanding_pkts()[0] < curr_packet.get_packet_id():
                #             dest_host = curr_packet.get_src()
                #             assert dest_host != curr_host.get_ip()
                #             exp_packet_id = curr_host.get_outstanding_pkts()[0]
                #             print "fast recovery A expected", exp_packet_id - 1
                #             # assert curr_packet.get_actual_id() < exp_packet_id
                #             hosts[dest_host].set_last_received_pkt_id(exp_packet_id - 1)
                #             curr_host.set_fast_recovery(1)
                          
                #         elif curr_host.get_outstanding_pkts()[0] >= curr_packet.get_packet_id() + 1: 
                #             # assert curr_host.get_outstanding_pkts()[0] == curr_packet.get_packet_id()
                #             if curr_host.get_fast_recovery():
                #                 curr_host.set_fast_recovery(0)
                #                 curr_host.set_window_size(curr_host.get_threshold())
                #                 print "fast recovery src", curr_packet.get_src()
                #                 print "fast recovery dest", curr_packet.get_dest()
                #                 # Set the new last received packet on receiving host
                #                 dest_host = curr_packet.get_src()
                #                 assert dest_host != curr_host.get_ip()
                #                 exp_packet_id = curr_host.get_outstanding_pkts()[0]
                #                 print "fast recovery B expected", exp_packet_id - 1
                #                 assert curr_packet.get_actual_id() < exp_packet_id
                #                 hosts[dest_host].set_last_received_pkt_id(exp_packet_id - 1)
                #         else:
                #             print "fast recovery error curr packet", curr_packet.get_packet_id()
                #             print "fast recovery error", curr_host.get_outstanding_pkts()[0]
                #             assert False


                print "threshold", curr_host.get_threshold()
                network.populate_packets_into_buffer(curr_host, global_time, dropped_packets)

            # Process other packets received by the hosts
            else:
                print 'Received host'
                print 'Running...'
                assert curr_packet.get_type() == MESSAGE_PACKET

                # Create acknowlegment packet with same packet id as the original packet

                # last_recv_pkt = curr_host.get_last_received_pkt_id()
                # exp_packet_id = hosts[curr_packet.get_src()].get_outstanding_pkts()[0] if last_recv_pkt == None else (last_recv_pkt + 1)
                # assert exp_packet_id != None

                # print "fast recovery B exp_packet_id", exp_packet_id
                # print "fast recovery B actual_packet_id", curr_packet.get_actual_id()

                # Create ack packet and send
                p = Packet(ACK_PACKET, 1, curr_host.get_ip(), curr_packet.get_src(), next_dest.get_ip(), global_time)
                p.set_packet_id(curr_packet.get_packet_id())
                # p.set_actual_id(curr_packet.get_actual_id())
                next_hop = next_dest

                # Set ID for packet that we are acknowledging
                # if exp_packet_id != curr_packet.get_actual_id():
                #     p.set_packet_id(exp_packet_id - 1)
                # else:
                #     p.set_packet_id(exp_packet_id)
                #     curr_host.set_last_received_pkt_id(exp_packet_id)

                self.insert_packet_into_buffer(next_link, curr_host, next_hop, p, dropped_packets, global_time)




    def process_timeout_event(self, event_top, global_time, hosts, dropped_packets, acknowledged_packets):
        curr_packet = event_top.get_data()
        curr_host = hosts[curr_packet.get_src()]
        p_id = curr_packet.get_packet_id()

        assert curr_packet.get_packet_id() != 0

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
                curr_host.set_threshold(max(curr_host.get_window_size() / 2.0, 2.0))
                curr_host.set_window_size(1)
                print "window size 3: %f, threshold: %f" % (curr_host.get_window_size(), curr_host.get_threshold())

            curr_link = curr_host.get_link()
            next_hop = curr_link.get_link_endpoint(curr_host)
            # Create new packet
            p = Packet(MESSAGE_PACKET, 1, curr_packet.get_src(), curr_packet.get_dest(), next_hop.get_ip(), global_time)
            p.set_packet_id(curr_packet.get_packet_id())
            # p.set_actual_id(curr_packet.get_actual_id())
            dropped_packets.append(p)

            # Insert resend packet into buffer
            self.insert_packet_into_buffer(curr_link, curr_host, next_hop, p, dropped_packets, global_time)
                # curr_host.set_window_count(curr_host.get_window_count() + 1)

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