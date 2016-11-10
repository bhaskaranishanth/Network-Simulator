from packet import *
from math import ceil

class Flow:
    def __init__(self, flow_id, data_size, flow_src, flow_dest, flow_start):
        """
        Defines Flow class containing the flow ID, total amount of data 
        (data_size), source, destination, and start time of the flow
        """
        self.flow_id = flow_id
        self.data_size = float(data_size)
        self.flow_src = flow_src
        self.flow_dest = flow_dest
        self.flow_start = float(flow_start)

    
    """ Accessor methods """

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

    
    """ Mutator methods """

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


    """ Creating packets """

    def gen_packets(self):
        packets = []
        n = int(ceil(self.data_size * 10**6 / MESSAGE_SIZE))
        for i in range(n):
            p = Packet(MESSAGE_PACKET, MESSAGE_SIZE, self.get_src(), self.get_dest())
            packets.append(p)

        return packets, self.get_start()

    """ Print methods """
    def __str__(self):
        print "Printing flow details..."
        print "Data size:", self.data_size
        print "Source:", self.flow_src
        print "Destination:", self.flow_dest
        return ""

    