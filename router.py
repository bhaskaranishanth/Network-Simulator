from host import *

class Router:
    """
    Represents routers
    """
    def __init__(self, ip):
        self.ip = ip
        self.table = None
        # List of links
        self.link_lst = set()

        self.weight_table = {}

    def set_routing_table(self, table):
        self.table = table

        for k, v in table.iteritems():
            self.weight_table[k] = (v, float('inf'))

    def get_routing_table(self):
        return self.table

    def get_weight_table(self):
        return self.weight_table
        
    def reset_weight_table(self):
        for k, v in self.weight_table.iteritems():
            self.weight_table[k] = (v[0], float('inf'))
        print "Rest: ", self.weight_table

    def add_link(self, link):
        ''' 
        Adds a Link object to the list
        '''
        self.link_lst.add(link)

    def get_links(self):
        '''
        Returns a list of Link objects
        '''
        return self.link_lst

    def get_link_for_dest(self, dest):
        for x in self.link_lst:
            src, dst = x.get_endpoints()
            if src == dest or dst == dest:
                return x
        assert False

    def get_ip(self):
        return self.ip

    def get_hosts(self):
        '''
        Returns a list of Hosts connected to this router.
        '''
        h = []
        for link in self.link_lst:
            src, dst = link.get_endpoints()
            assert self == src or self == dst
            if isinstance(src, Host):
                h.append(src)
            if isinstance(dst, Host):
                h.append(dst)
        return h

    def __str__(self):
        print 'Router IP: ' + self.ip
        print 'Routing Table: ' + str(self.table)
        print 'Weight Table: ' + str(self.weight_table)
        return ''

    def __repr__(self):
        return self.ip







