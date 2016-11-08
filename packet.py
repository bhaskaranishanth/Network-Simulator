MESSAGE_SIZE = 1024
ACK_SIZE = 64
ROUTER_SIZE = 64

MESSAGE_PACKET = 0
ACK_PACKET = 1
ROUTER_PACKET = 2

type_dict = {MESSAGE_PACKET : "MESSAGE_PACKET", 
            ACK_PACKET : "ACK_PACKET",
            ROUTER_PACKET : "ROUTER_PACKET"}

class Packet:
    """Defines a Packet class which contains details about the
    packet type, payload, metadata(Dest, Source)

    Packet Type:
    0 - Message Packet
    1 - Acknowledgement Packet
    2 - Router Packet
    """
    def __init__(self, packet_type, payload, src, dest):
        self.check_type(packet_type)
        self.type = packet_type
        self.set_capacity()
        self.check_payload(payload)
        
        self.payload = payload
        self.src = src
        self.dest = dest

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
        assert payload < self.capacity


    """ MUTATOR METHODS """

    def get_type(self):
        return type_dict[self.type]

    def get_capacity(self):
        return self.capacity

    def get_payload(self):
        return self.payload

    def get_src(self):
        return self.src

    def get_dest(self):
        return self.dest


    """ ACCESSOR METHODS """

    def set_type(self, packet_type):
        self.check_type(packet_type)
        self.type = packet_type

    def set_payload(self, payload):
        self.check_payload(payload)
        self.payload = payload

    def set_src(self, src):
        self.src = src

    def set_dest(self, dest):
        self.dest = dest

    """ PRINT METHODS """
    def __str__(self):
        print "Printing Packet Details"
        print "Type: ", type_dict[self.type]
        print "Capacity: ", self.capacity
        print "Payload: ", self.payload
        print "Source: ", self.src
        print "Destination: ", self.dest
        return ""