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

    def create_routing_packet_received_event(self, end_time, pkt, link, src, dest):
        """
        Takes in packet and link information, creates a PACKET_RECEIVED
        event and adds it to the global queue. Returns the event
        to make it easier to debug code.
        """
        new_event = Event(ROUTING_PACKET_RECEIVED, end_time, src, dest, pkt)
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
        timeout_event = Event(TIMEOUT_EVENT, end_time, pkt.get_src(), pkt.get_dest(), pkt)
        self.eq.put((timeout_event.get_initial_time(), timeout_event))
        return timeout_event

    def create_remove_from_buffer_event(self, end_time, pkt, src, dest):
        remove_from_buffer_event = Event(REMOVE_FROM_BUFFER, end_time, src, dest, pkt)
        self.eq.put((remove_from_buffer_event.get_initial_time(), remove_from_buffer_event))
        return remove_from_buffer_event

    def create_update_window_event(self, curr_host, time):
        assert curr_host.get_is_reno() or curr_host.get_is_fast() or curr_host.get_is_cubic()
        update_window_event = Event(UPDATE_WINDOW, time, curr_host.get_ip(), None, None)
        self.eq.put((update_window_event.get_initial_time(), update_window_event))


