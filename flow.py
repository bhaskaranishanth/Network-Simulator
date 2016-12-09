from packet import *
from math import ceil

class Flow:
    def __init__(self, flow_id, data_size, flow_src, flow_dest, flow_start, is_fast):
        """
        Defines Flow class containing the flow ID, total amount of data 
        (data_size), source, destination, and start time of the flow
        """
        self.flow_id = flow_id
        self.data_size = float(data_size)
        assert type(flow_src) == str and type(flow_dest) == str
        self.flow_src = flow_src
        self.flow_dest = flow_dest
        self.flow_start = float(flow_start)
        assert is_fast in ['0','1','2']
        self.is_reno = int(is_fast) == 0
        self.is_fast = int(is_fast) == 1
        self.is_cubic = int(is_fast) == 2
        self.tcp_val = is_fast

    
    """ ACCESSOR METHODS """

    def get_id(self):
        return self.flow_id

    def get_data_size(self):
        return self.data_size

    def get_src(self):
        return self.flow_src

    def get_dest(self):
        return self.flow_dest

    def get_start(self):
        return self.flow_start

    # def get_tcp(self):
    #     assert self.is_fast == 1
    #     return self.is_fast == 1

    def is_reno(self):
        assert type(self.is_reno) == bool
        return self.is_reno

    def is_fast(self):
        assert type(self.is_fast) == bool
        return self.is_fast
    
    def is_cubic(self):
        assert type(self.is_cubic) == bool
        return self.is_cubic

    def get_tcp_val(self):
        return self.tcp_val


    
    """ MUTATOR METHODS """

    def set_id(self, flow_id):
        self.flow_id = flow_id

    def set_data_size(self, data_size):
        self.data_size = data_size

    def set_src(self, src):
        self.flow_src = src

    def set_dest(self, dest):
        self.flow_dest = dest

    def set_start(self, start):
        self.flow_start = start

    # def set_tcp(self, is_fast):
    #     assert is_fast in [0,1,2]
    #     self.is_fast = is_fast

    def gen_packets(self):
        """
        Generates list of packets from flow
        """
        packets = []
        # Determine number of packets (total data size / size of message packet),
        n = int(ceil(self.data_size * 10**6 / MESSAGE_SIZE))
        for i in range(n):
            # Create new packet and add to list of packets
            p = Packet(MESSAGE_PACKET, MESSAGE_SIZE, self.get_src(), self.get_dest(), None, self.get_start())
            packets.append(p)

        return packets

    """ PRINT METHODS """
    def __str__(self):
        print "Printing flow details..."
        print "Data size:", self.data_size
        print "Source:", self.flow_src
        print "Destination:", self.flow_dest
        return ""

    