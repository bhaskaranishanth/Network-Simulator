from router import *
from host import *

class Link:
    """
    Represents Link.
    """
    def __init__(self, link_id, length, buf, prop_time, trans_time, congestion, direction):
        self.link_id = link_id
        self.length = length
        self.buf = buf
        self.prop_time = prop_time
        self.trans_time = trans_time
        self.congestion = congestion
        self.direction = direction

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

    def __str__(self):
        s = [
         'Link Details: ' + str(self.link_id),
         'Length: ' + str(self.length),
         'Buffer: ' + str(self.buf),
         'Propagation Time: ' + str(self.prop_time),
         'Transmission Time: ' + str(self.trans_time),
         'Congestion: ' + str(self.congestion),
         'Direction: ' + str(self.direction),
         'Source: ' + str(self.src.ip),
         'Destination: ' + str(self.dst.ip)
        ]
        return '\n'.join(s)

    def __repr__(self):
        return str(self)




