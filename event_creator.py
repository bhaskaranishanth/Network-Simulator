from event import *
from router import *
from host import *
from packet import *

class EventCreator:
    def __init__(self, eq):
        self.eq = eq
        

    def create_packet_received_event(self, end_time, pkt, link, src, dest):
        """
        Takes in packet and link information, creates a PACKET_RECEIVED
        event and adds it to the global queue. Returns the event
        to make it easier to debug code.
        """
        new_event = Event(PACKET_RECEIVED, end_time, src, dest, pkt)
        self.eq.put((new_event.get_initial_time(), new_event))

        # link.remove_from_buffer(pkt, pkt.get_capacity())
        print pkt

        return new_event

    def create_routing_packet_received_event(self, global_time, pkt, link, src, dest):
        """
        Takes in packet and link information, creates a PACKET_RECEIVED
        event and adds it to the global queue. Returns the event
        to make it easier to debug code.
        """
        new_event = Event(ROUTING_PACKET_RECEIVED, 
            global_time + pkt.get_capacity() / link.get_trans_time() + link.get_prop_time(), 
            src, dest, pkt)
        self.eq.put((new_event.get_initial_time(), new_event))
        return new_event

    def create_dynamic_routing_event(self, routing_time):
        """
        Takes in packet and link information, creates a PACKET_RECEIVED
        event and adds it to the global queue. Returns the event
        to make it easier to debug code.
        """
        new_event = Event(DYNAMIC_ROUTING, routing_time, None, None, None)
        self.eq.put((new_event.get_initial_time(), new_event))
        return new_event

    def create_graph_event(self, time):
        new_event = Event(GRAPH_EVENT, time, None, None, None)
        self.eq.put((new_event.get_initial_time(), new_event))
        return new_event


    def create_timeout_event(self, end_time, pkt):
        """
        Takes in end time and packet, creates a TIMEOUT_EVENT
        event and adds it to the global queue. Returns the event
        to make it easier to debug code.
        """
        # pkt.set_init_time(global_time)
        timeout_event = Event(TIMEOUT_EVENT, end_time, pkt.get_src(), pkt.get_dest(), pkt)
        self.eq.put((timeout_event.get_initial_time(), timeout_event))
        return timeout_event

    def create_remove_from_buffer_event(self, end_time, pkt, src, dest):
        remove_from_buffer_event = Event(REMOVE_FROM_BUFFER, end_time, src, dest, pkt)
        self.eq.put((remove_from_buffer_event.get_initial_time(), remove_from_buffer_event))
        return remove_from_buffer_event

    def create_next_packet_event(self, curr_link, global_time, event_top, hosts, routers):
        processed_packet_dest_loc = event_top.get_dest()
        if len(curr_link.packet_queue) != 0:
            next_packet = curr_link.packet_queue[0]

            if next_packet.get_type() == ROUTER_PACKET:
                new_dest = next_packet.get_curr_loc()
                curr_entity = routers if new_dest in routers else hosts
                new_src = curr_link.get_link_endpoint(curr_entity[new_dest])

                if new_dest == processed_packet_dest_loc:
                    self.create_routing_packet_received_event(global_time - curr_link.get_prop_time(), next_packet, curr_link, new_src.get_ip(), new_dest)
                else:
                    self.create_routing_packet_received_event(global_time, next_packet, curr_link, new_src.get_ip(), new_dest)

                # create_routing_packet_received_event(global_time, next_packet, curr_link, new_src.get_ip(), new_dest)



            else:
                # Determine the source and destination of the new event to add to queue
                curr_entity = routers if next_packet.get_curr_loc() in routers else hosts
                next_dest = next_packet.get_curr_loc()
                curr_src = curr_link.get_link_endpoint(curr_entity[next_packet.get_curr_loc()]).get_ip()

                curr_link.remove_from_buffer(next_packet, next_packet.get_capacity())

                # Create new event with the same packet
                if next_dest == processed_packet_dest_loc:
                    self.create_remove_from_buffer_event(global_time + curr_link.get_prop_time(), next_packet, curr_src, next_dest)
                else:
                    self.create_remove_from_buffer_event(global_time + curr_link.get_prop_time() + pkt.get_capacity() / link.get_trans_time(), next_packet, curr_src, next_dest)


                # create_packet_received_event(global_time, next_packet, curr_link, curr_src, next_dest)

    def create_update_window_event(self, curr_host, time):
        assert curr_host.is_fast
        update_window_event = Event(UPDATE_WINDOW, time, curr_host.get_ip(), None, None)
        self.eq.put((update_window_event.get_initial_time(), update_window_event))


