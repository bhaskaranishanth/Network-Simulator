
class Link:
    """
    Represents Link.
    """
    def __init__(self, length, buf, prop_time, trans_time, congestion, direction):
        self.length = length
        self.buf = buf
        self.prop_time = prop_time
        self.trans_time = trans_time
        self.congestion = congestion
        self.direction = direction

        self.src = None
        self.dst = None

    def connect(src, dst):
        '''
        Uses the link to connect the src and dst.
        '''
        self.src = src
        self.dst = dst

    def get_endpoints():
        '''
        Return endpoints of the nodes
        '''
        return (self.src, self.dst)

    def __str__(self):
        print 'Link details'
        print 'Length: ', self.length
        print 'Buffer: ', self.buf
        print 'Propagation Time: ', self.prop_time
        print 'Transmission Time: ', self.trans_time
        print 'Congestion: ', self.congestion
        print 'Direction: ', self.direction
        print 'Source: ', self.src
        print 'Destination: ', self.dst
