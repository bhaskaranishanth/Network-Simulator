from router import *
from host import *
from collections import deque

class Link:
    """
    Represents Link.
    """
    def __init__(self, link_id, buf, prop_time, trans_time, congestion, direction):
        self.link_id = link_id
        # Buffer size given in KB
        self.buf = float(buf) * 10 ** 3
        # Prop time given in Mbps
        self.prop_time = float(prop_time) * (10 ** 6) / 8
        # Trans time given in ms
        self.trans_time = float(trans_time) * 10 ** (-3)
        self.congestion = congestion
        self.direction = direction

        self.packet_queue = deque()

        self.capacity = 0
        self.num_packets = 0
        self.next_free_time = -1
        self.num_dropped_packets = 0

        # Source and destinations are either Routers or Hosts
        self.src = None
        self.dst = None


    """ ACCESSOR METHODS """


    def connect(self, src, dst):
        '''
        Uses the link to connect the src and dst.
        '''
        assert isinstance(src, Router) or isinstance(src, Host)
        assert isinstance(dst, Router) or isinstance(dst, Host)
        self.src = src
        self.dst = dst


    def get_endpoints(self):
        '''
        Return endpoints of the nodes
        '''
        return (self.src, self.dst)

    def get_link_endpoint(self, start):
        assert isinstance(start, Router) or isinstance(start, Host)
        return self.dst if self.src == start else self.src

    def get_weight(self):
        '''
        Return weight of link.
        '''
        return len(self.packet_queue)

    def get_trans_time(self):
        return self.trans_time

    def get_prop_time(self):
        return self.prop_time

    def get_num_packets(self):
        '''
        Number of packets in window.
        '''
        return self.num_packets

    def get_free_time(self):
        return self.next_free_time

    
    """ MUTATOR METHODS """

    def connect(self, src, dst):
        """
        Uses the link to connect the src and dst.
        """
        assert isinstance(src, Router) or isinstance(src, Host)
        assert isinstance(dst, Router) or isinstance(dst, Host)
        self.src = src
        self.dst = dst

    def insert_into_buffer(self, packet, packet_size):
        """
        Inserts the packet into the link's buffer and return
        a boolean indicating success or failure.
        """
        print 'insert_into_buffer....'
        # print 'capacity: ', self.capacity
        # print 'packet size: ', packet_size
        # print 'Buffer: ', self.buf
        # print type(self.capacity), type(packet_size), type(self.buf)
        # print self.capacity + packet_size > self.buf
        # print self.link_id
        if self.capacity + packet_size > self.buf:
            return False
        else:
            self.capacity += packet_size
            self.num_packets += 1
            self.packet_queue.append(packet)
            return True

    def increment_drop_packets(self):
        self.num_dropped_packets += 1

    def get_drop_packets(self):
        return self.num_dropped_packets
        
    def remove_from_buffer(self, packet, packet_size):
        """
        Remove the packet from the link's buffer and return
        a boolean indicating success or failure.
        """
        print 'remove_from_buffer....'
        # print 'capacity: ', self.capacity
        # print 'packet size: ', packet_size
        # print 'Buffer: ', self.buf
        # print self.link_id
        if self.capacity - packet_size < 0:
            assert False
        self.capacity -= packet_size
        self.num_packets -= 1
        self.packet_queue.popleft()
        assert self.num_packets >= 0

    def update_next_free_time(self, free_time):
        self.next_free_time = free_time


    """ PRINT METHODS """
    
    def __str__(self):
        print 'Link id: ' + str(self.link_id)
        print 'Buffer: ' + str(self.buf)
        print 'Propagation Time: ' + str(self.prop_time)
        print 'Transmission Time: ' + str(self.trans_time)
        print 'Congestion: ' + str(self.congestion)
        print 'Direction: ' + str(self.direction)
        print 'Source: ' + str(self.src.ip)
        print 'Destination: ' + str(self.dst.ip)
        print 'Weight: ' + str(self.get_weight())
        return ''

    def __repr__(self):
        return self.link_id


