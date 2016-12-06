from Queue import PriorityQueue
from host import *
from router import *
from link import *
from flow import *
from djikstra import *
from event_creator import *
from event_processor import *

class NetworkSystem:

    def __init__(self):
        # Initialize network system
        self.eq = PriorityQueue(maxsize=0)
        self.hosts, self.routers, self.links, self.flows = self.process_input()
        self.ec = EventCreator(self.eq)
        self.ep = EventProcessor(self.ec, self.hosts, self.routers, self.links, self.flows)

    def retrieve_system(self):
        return self.hosts, self.routers, self.links, self.flows

    def update_routing_table(self):
        # Create routing table
        d = Djikstra()
        d.update_routing_table(self.routers.values())

    def get_system_queue(self):
        return self.eq

    def get_event_creator(self):
        return self.ec

    def get_event_processor(self):
        return self.ep

    def init_packet_hop(self):
        # Update every packets next hop location
        for _, h in self.hosts.iteritems():
            link = h.get_link()
            next_hop = link.get_link_endpoint(h).get_ip()
            q_len = h.q.qsize()
            for x in range(q_len):
                x = h.q.get()
                x.set_curr_loc(next_hop)
                h.q.put(x)
            assert h.q.qsize() == q_len

    def populate_link_buffers(self):
        # Fills up all the link's buffers connected to the host 
        for _, h in self.hosts.iteritems():
            link = h.get_link()
            # Load window number of packets from host queue to buffer
            while h.get_window_count() < h.get_window_size():
                curr_packet = h.remove_packet()
                if curr_packet != None:
                    if link.insert_into_buffer(curr_packet):
                        h.set_window_count(h.get_window_count()+1)
                    else:
                        # Put packet back into the host since buffer is full
                        h.insert_packet(curr_packet)
                        break
                else:
                    break

            # assert len(link.packet_queue) == 0 or len(link.packet_queue) == h.get_window_size()


    def create_packet_events(self):
        # Creates timeout events for all packets in buffer
        # Creates remove from buffer event for first packet in buffer
        for _, h in self.hosts.iteritems():
            link = h.get_link()
            for i, p in enumerate(link.packet_queue):
                # Creates timeout event
                self.ec.create_timeout_event(TIMEOUT_VAL + p.get_init_time(), p)
            if len(link.packet_queue) > 0:
                # Create the first packet received event
                # TODO: possibly remove the packet from the buffer?
                p = link.packet_queue[0]
                curr_src = h
                next_dest = link.get_link_endpoint(h)
                # link.remove_from_buffer(p, p.get_capacity())
                self.ec.create_remove_from_buffer_event(p.get_init_time(), p, curr_src.get_ip(), next_dest.get_ip())


    def populate_packets_into_buffer(self, curr_host, global_time, dropped_packets):

        while curr_host.get_window_count() < curr_host.get_window_size():
            pkt = curr_host.remove_packet()
            # if pkt.packet_id == 9000:
            #     print 'Host Window Reached here'
            #     exit(1)
            next_link = curr_host.get_link()
            next_dest = next_link.get_link_endpoint(curr_host)
            if pkt != None:
                assert pkt.get_curr_loc() != None
                # self.ec.create_timeout_event(TIMEOUT_VAL + global_time, pkt)
                if len(next_link.packet_queue) == 0:
                    if next_link.get_direction() == (curr_host.get_ip(), next_dest.get_ip()):
                        # Insert packet into the next link's buffer
                        if self.ep.handle_packet_to_buffer_insertion(pkt, next_link, dropped_packets, global_time, next_dest):
                            self.ec.create_remove_from_buffer_event(global_time, pkt, curr_host.get_ip(), next_dest.get_ip())
                            curr_host.set_window_count(curr_host.get_window_count()+1)
                            self.ec.create_timeout_event(TIMEOUT_VAL + global_time, pkt)
                        else:
                            curr_host.insert_packet(pkt)
                            break
                    elif next_link.get_direction() == (next_dest.get_ip(), curr_host.get_ip()):
                        if self.ep.handle_packet_to_buffer_insertion(pkt, next_link, dropped_packets, global_time, next_dest):
                            next_time = max(next_link.get_last_pkt_dest_time(), global_time)
                            self.ec.create_remove_from_buffer_event(next_time, pkt, next_dest.get_ip(), curr_host.get_ip())
                            self.ec.create_timeout_event(TIMEOUT_VAL + global_time, pkt)
                            curr_host.set_window_count(curr_host.get_window_count()+1)
                        else:
                            curr_host.insert_packet(pkt)
                            break
                    else:
                        assert False
                else:
                    if self.ep.handle_packet_to_buffer_insertion(pkt, next_link, dropped_packets, global_time, next_dest):
                        self.ec.create_timeout_event(TIMEOUT_VAL + global_time, pkt)
                        curr_host.set_window_count(curr_host.get_window_count()+1)
                    else:
                        # TODO
                        curr_host.insert_packet(pkt)
                        break
            else:
                break


    def initialize_flow_RTT(self):
        '''
        Sets each hosts base RTT to be infinity
        '''
        base_rtt_table = self.get_base_RTT()
        print base_rtt_table
        for _, h in self.hosts.iteritems():
            h.set_base_RTT(float('inf'))



    def initialize_packets(self):
        count = 0
        for key in self.flows:
            event_list = []
            # count = 0
            curr_host = self.hosts[self.flows[key].get_src()]
            curr_host.set_tcp(self.flows[key].get_tcp())
            curr_host.set_flow_id(key)

            for packet in self.flows[key].gen_packets():
                count += 1
                packet.set_packet_id(count)
                curr_host.insert_packet(packet)
                curr_host.add_outstanding_pkt(count)

                # if count == 1000:
                #     break

    def process_input(self):
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

            print src, dst, link_id
            # Create two way links
            src_node = hosts[src] if src in hosts else routers[src]
            dst_node = hosts[dst] if dst in hosts else routers[dst]
            l = Link(link_id, buf, prop_time, trans_time, congestion, direction)
            # print l
            print l.get_endpoints()
            l.connect(src_node, dst_node)
            l.direction = (src, dst)
            print "what"
            print l.get_direction()
            assert l.get_direction() != None
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
            flow_id, src, dst, data_amt, flow_start, is_fast = line.strip().split('|')
            flows[flow_id] = Flow(flow_id, data_amt, src, dst, flow_start, is_fast)

        return hosts, routers, links, flows




    def get_base_RTT(self):
        base_RTT_table = {}
        for h1 in self.hosts.values():
            for h2 in self.hosts.values():
                if h1 != h2:
                    tup = (h1,h2)
                    if tup not in base_RTT_table:
                        time = 0
                        link_adj = h1.get_link()
                        time += link_adj.get_prop_time() + MESSAGE_SIZE/link_adj.get_trans_time()
                        dest = link_adj.get_link_endpoint(h1)
                        print h1.get_ip()
                        print h2.get_ip()
                        print "Dest: ", dest
                        while dest != h2: 
                            new_dest = dest.get_routing_table()[h2] 
                            link_adj = dest.get_link_for_dest(new_dest)
                            time += link_adj.get_prop_time() + MESSAGE_SIZE/link_adj.get_trans_time()
                            dest = new_dest
                        time *= 2
                        base_RTT_table[tup] = time 
        return base_RTT_table



