from Queue import Queue
from constants import *

class Host:
    """
    Represents Host
    """
    def __init__(self, ip):
        self.ip = ip
        self.link = None
        # Queue of packets that need to be sent
        self.q = Queue()
        self.window_count = 0
        self.window_size = WINDOW_SIZE
        self.threshold = THRESHOLD
        self.is_fast = None
        self.flow_id = None
        self.base_RTT = float('inf')
        self.last_RTT = self.base_RTT

    
    """ ACCESSOR METHODS """
    
    def get_link(self):
        return self.link

    def get_links(self):
        '''
        Returns a list representation of the link
        '''
        return [self.link]

    def get_ip(self):
        return self.ip

    def get_window_count(self):
        return self.window_count

    def get_window_size(self):
        return self.window_size

    def get_threshold(self):
        return self.threshold

    def get_tcp(self):
        assert type(self.is_fast) == bool or self.is_fast == None
        print type(self.is_fast)
        return self.is_fast

    def get_flow_id(self):
        return self.flow_id

    def get_base_RTT(self):
        return self.base_RTT

    def get_last_RTT(self):
        return self.last_RTT


    """ MUTATOR METHODS """

    def attach_link(self, link):
        '''
        Attach link to the host.
        '''
        assert self.link == None
        self.link = link
        
    def set_window_count(self, window_count):
        self.window_count = window_count

    def set_window_size(self, window_size):
        self.window_size = window_size

    def set_threshold(self, threshold):
        self.threshold = threshold

    def set_tcp(self, is_fast):
        assert type(is_fast) == bool
        self.is_fast = is_fast

    def set_flow_id(self, flow_id):
        self.flow_id = flow_id

    def set_base_RTT(self, base_RTT):
        self.base_RTT = base_RTT

    def set_last_RTT(self, last_RTT):
        self.last_RTT = last_RTT

    def insert_packet(self, packet):
        self.q.put(packet)

    def remove_packet(self):
        if self.q.empty():
            return None
        else:
            return self.q.get()

    
    """ PRINT METHODS """

    def __str__(self):
        print 'Host IP: ' + self.ip
        print 'Link ID: ' + self.link.link_id
        print 'Window size:', self.get_window_size()
        print 'Window count:', self.get_window_count()
        return ''

    def __repr__(self):
        return self.ip
