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
