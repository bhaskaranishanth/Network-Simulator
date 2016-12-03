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

            assert len(link.packet_queue) == 0 or len(link.packet_queue) == h.get_window_size()


    def create_packet_events(self):
        # Creates timeout events for all packets in buffer
        # Creates packet received event for first packet in buffer
        for _, h in self.hosts.iteritems():
            link = h.get_link()
            for i, p in enumerate(link.packet_queue):
                if i == 0:
                    # Create the first packet received event
                    # TODO: possibly remove the packet from the buffer?
                    curr_src = h
                    next_dest = link.get_link_endpoint(h)
                    self.ec.create_packet_received_event(p.get_init_time(), 
                        p, link, curr_src.get_ip(), next_dest.get_ip())

                # Creates timeout event
                self.ec.create_timeout_event(TIMEOUT_VAL + p.get_init_time(),
                    p, p.get_init_time())


    # def create_packet_received_event(self, global_time, pkt, link, src, dest):
    #     """
    #     Takes in packet and link information, creates a PACKET_RECEIVED
    #     event and adds it to the global queue. Returns the event
    #     to make it easier to debug code.
    #     """
    #     new_event = Event(PACKET_RECEIVED, 
    #         global_time + pkt.get_capacity() / link.get_trans_time() + link.get_prop_time(), 
    #         src, dest, pkt)
    #     self.eq.put((new_event.get_initial_time(), new_event))
    #     return new_event

    # def create_timeout_event(self, end_time, pkt, global_time):
    #     """
    #     Takes in end time and packet, creates a TIMEOUT_EVENT
    #     event and adds it to the global queue. Returns the event
    #     to make it easier to debug code.
    #     """
    #     pkt.set_init_time(global_time)
    #     timeout_event = Event(TIMEOUT_EVENT, end_time, pkt.get_src(), pkt.get_dest(), pkt)
    #     self.eq.put((timeout_event.get_initial_time(), timeout_event))
    #     return timeout_event

    def initialize_flow_RTT(self):
        '''
        Sets each hosts base RTT to be infinity
        '''
        base_rtt_table = self.get_base_RTT()
        print base_rtt_table
        for _, h in self.hosts.iteritems():
            h.set_base_RTT(float('inf'))



    def initialize_packets(self):
        for key in self.flows:
            event_list = []
            count = 0
            curr_host = self.hosts[self.flows[key].get_src()]
            curr_host.set_tcp(self.flows[key].get_tcp())
            curr_host.set_flow_id(key)

            for packet in self.flows[key].gen_packets():
                count += 1
                packet.set_packet_id(count)
                curr_host.insert_packet(packet)

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



