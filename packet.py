from router import *
from host import *

MESSAGE_SIZE = 1024
ACK_SIZE = 64
ROUTER_SIZE = 64

MESSAGE_PACKET = "MESSAGE_PACKET", 
ACK_PACKET = "ACK_PACKET",
ROUTER_PACKET = "ROUTER_PACKET"

type_lst = [MESSAGE_PACKET, ACK_PACKET, ROUTER_PACKET]


class Packet:
    """Defines a Packet class which contains details about the
    packet type, payload, metadata(Dest, Source)

    Packet Type:
    0 - Message Packet
    1 - Acknowledgement Packet
    2 - Router Packet
    """
    def __init__(self, packet_type, payload, src, dest, curr_loc, init_time):
        self.check_type(packet_type)
        self.type = packet_type
        self.set_capacity()
        self.check_payload(payload)


        assert type(src) == str
        assert type(dest) == str or packet_type == ROUTER_PACKET
        assert curr_loc == None or type(curr_loc) == str 
        
        self.payload = payload
        self.src = src
        self.dest = dest
        self.curr_loc = curr_loc
        self.packet_id = id(self)
        self.init_time = init_time

    def set_capacity(self):
        if self.type == MESSAGE_PACKET:
            self.capacity = MESSAGE_SIZE
        elif self.type == ACK_PACKET:
            self.capacity = ACK_SIZE
        elif self.type == ROUTER_PACKET:
            self.capacity = ROUTER_SIZE

    def check_type(self, packet_type):
        assert packet_type == MESSAGE_PACKET or packet_type == ACK_PACKET or packet_type == ROUTER_PACKET

    def check_payload(self, payload):
        assert payload <= self.capacity or self.type == ROUTER_PACKET


    """ MUTATOR METHODS """

    def get_type(self):
        return self.type

    def get_capacity(self):
        return self.capacity

    def get_payload(self):
        return self.payload

    def get_src(self):
        return self.src

    def get_dest(self):
        return self.dest

    def get_curr_loc(self):
        return self.curr_loc

    def get_init_time(self):
        return self.init_time


    """ ACCESSOR METHODS """

    def set_type(self, packet_type):
        self.check_type(packet_type)
        self.type = packet_type

    def set_payload(self, payload):
        self.check_payload(payload)
        self.payload = payload

    def set_src(self, src):
        assert type(src) == str
        self.src = src

    def set_dest(self, dest):
        assert type(dest) == str
        self.dest = dest

    def set_curr_loc(self, curr_loc):
        assert type(curr_loc) == str
        # assert self.curr_loc == None
        self.curr_loc = curr_loc

    def set_init_time(self, init_time):
        self.init_time = init_time

    """ PRINT METHODS """
    def __str__(self):
        print "Printing Packet Details"
        print "Type: ", self.type
        print "Capacity: ", self.capacity
        print "Payload: ", self.payload
        print "Source: ", self.src
        print "Destination: ", self.dest
        print "Current Location: ", self.curr_loc
        print "Packet ID: ", self.packet_id
        return ""