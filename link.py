from router import *
from host import *

class Link:
    """
    Represents Link.
    """
    def __init__(self, link_id, length, buf, prop_time, trans_time, congestion, direction):
        self.link_id = link_id
        self.length = length
        self.buf = float(buf) * 10 ** 3
        self.prop_time = float(prop_time)
        self.trans_time = float(trans_time)
        self.congestion = congestion
        self.direction = direction

        self.capacity = 0
        self.num_packets = 0
        self.actual_packets = 0
        self.next_free_time = -1

        # Source and destinations are either Routers or Hosts
        self.src = None
        self.dst = None

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
        return self.dst.get_ip() if self.src == start else self.src.get_ip()

    def get_weight(self):
        '''
        Return weight of link.
        '''
        if self.length == None:
            self.length = 1
        return self.length

    def insert_into_buffer(self, packet_size):
        # print 'insert_into_buffer....'
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
            return True

    def remove_from_buffer(self, packet_size):
        # print 'remove_from_buffer....'
        # print 'capacity: ', self.capacity
        # print 'packet size: ', packet_size
        # print 'Buffer: ', self.buf
        # print self.link_id
        if self.capacity - packet_size < 0:
            assert False
        self.capacity -= packet_size
        self.num_packets -= 1
        assert self.num_packets >= 0

    def get_num_packets(self):
        '''
        Number of packets in window.
        '''
        return self.num_packets


    def get_free_time(self):
        return self.next_free_time

    def update_next_free_time(self, free_time):
        self.next_free_time = free_time


    def __str__(self):
        print 'Link id: ' + str(self.link_id)
        print 'Length: ' + str(self.length)
        print 'Buffer: ' + str(self.buf)
        print 'Propagation Time: ' + str(self.prop_time)
        print 'Transmission Time: ' + str(self.trans_time)
        print 'Congestion: ' + str(self.congestion)
        print 'Direction: ' + str(self.direction)
        print 'Source: ' + str(self.src.ip)
        print 'Destination: ' + str(self.dst.ip)
        return ''

    def __repr__(self):
        return self.link_id


