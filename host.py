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
        self.is_fast = False
        self.is_reno = False
        self.is_cubic = False
        self.flow_id = None
        self.base_RTT = float(10**10)
        self.last_RTT = self.base_RTT
        self.bytes_received = 0
        self.outstanding_pkts = []

        # Store the received and missing packet ids
        # Figure out a way to deal with multiple flows
        self.pkt_id_dict = {}
        self.recv_pkt_ids = []
        self.miss_pkt_ids = []
        self.last_recv_pkt_id = None
        self.last_miss_pkt_id = None

        self.fast_recovery = 0

        # self.abs_window_count = 0 

        # Cubic val parameters
        self.window_size_max = self.window_size
        self.last_congestion_time = 0

    
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

    # def get_tcp(self):
    #     assert type(self.is_fast) == bool or self.is_fast == None
    #     print type(self.is_fast)
    #     return self.is_fast

    def get_flow_id(self):
        return self.flow_id

    def get_base_RTT(self):
        return self.base_RTT

    def get_last_RTT(self):
        return self.last_RTT

    def get_bytes_received(self):
        return self.bytes_received

    def get_queue(self):
        return self.q

    def get_received_pkt_ids(self):
        return self.recv_pkt_ids

    def get_missing_pkt_ids(self):
        return self.miss_pkt_ids

    def get_last_received_pkt_id(self):
        return self.last_recv_pkt_id

    def get_last_missing_pkt_id(self):
        return self.last_miss_pkt_id

    def get_outstanding_pkts(self):
        return self.outstanding_pkts
        
    def flow_done(self):
        return not self.outstanding_pkts

    def get_fast_recovery(self):
        return self.fast_recovery

    def get_is_reno(self):
        assert type(self.is_reno) == bool
        return self.is_reno

    def get_is_fast(self):
        print 'is fast: ', self.is_fast
        assert type(self.is_fast) == bool
        return self.is_fast
    
    def get_is_cubic(self):
        assert type(self.is_cubic) == bool
        return self.is_cubic


    """ MUTATOR METHODS """

    def attach_link(self, link):
        '''
        Attach link to the host.
        '''
        assert self.link == None
        self.link = link
        
    def set_window_count(self, window_count):

        # assert self.window_count == window_count + 1 or self.window_count == window_count - 1
        # self.abs_window_count += 1 if window_count > self.window_count else 0
        # print 'outstanding_pkts packets: ', self.outstanding_pkts
        print 'Window countb: ', window_count
        print 'Window count: ', self.window_count
        # print 'Abs Window count: ', self.abs_window_count
        print 'Window size: ', self.window_size
        assert window_count >= 0
        self.window_count = window_count
        
        # assert self.abs_window_count - self.window_count + len(self.outstanding_pkts) == 70


    def set_window_size(self, window_size):
        assert window_size > 0
        self.window_size = window_size


    def set_threshold(self, threshold):
        self.threshold = threshold

    def set_tcp(self, tcp_val):
        assert tcp_val in ['0','1','2']
        # assert type(is_fast) == bool
        self.is_reno = int(tcp_val) == 0
        self.is_fast = int(tcp_val) == 1
        self.is_cubic = int(tcp_val) == 2

    def set_flow_id(self, flow_id):
        self.flow_id = flow_id

    def set_base_RTT(self, base_RTT):
        self.base_RTT = base_RTT

    def set_last_RTT(self, last_RTT):
        self.last_RTT = last_RTT

    def set_bytes_received(self, packet_size):
        self.bytes_received = packet_size

    def set_fast_recovery(self, fast_recovery):
        self.fast_recovery = fast_recovery

    def insert_packet(self, packet):
        self.q.put(packet)

    def insert_recv_pkt(self, packet):
        self.recv_pkt_ids.append(packet.get_packet_id())

    def insert_miss_pkt(self, packet):
        self.miss_pkt_ids.append(packet.get_packet_id())

    def update_last_recv_pkt(self):
        """
        Function that finds the next missing
        packet id and sets the last packet received
        to be that id value minus 1.
        """
        curr_val = self.last_recv_pkt_id
        # print "cur val: ", curr_val
        # print "list: ", self.recv_pkt_ids
        while curr_val in self.recv_pkt_ids:
            curr_val += 1
        #     print "ya"
        # print "new id: ", self.last_recv_pkt_id
        self.last_recv_pkt_id = curr_val - 1

    def set_last_received_pkt_id(self, id):
        self.last_recv_pkt_id = id

    def set_last_missing_pkt_id(self, id):
        self.last_miss_pkt_id = id



    def remove_packet(self):
        if self.q.empty():
            return None
        else:
            return self.q.get()

    def add_outstanding_pkt(self, pkt):
        self.outstanding_pkts.append(pkt)

    def del_outstanding_pkt(self, pkt):
        self.outstanding_pkts.remove(pkt)


    
    """ PRINT METHODS """

    def print_queue(self):
        for elem in list(self.q.queue):
            print elem

    def __str__(self):
        print 'Host IP: ' + self.ip
        print 'Link ID: ' + self.link.link_id
        print 'Window size:', self.get_window_size()
        print 'Window count:', self.get_window_count()
        return ''

    def __repr__(self):
        return self.ip
