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

    def set_routing_table(self, table):
        self.table = table

    def get_routing_table(self, table):
        return self.table
        
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
        s = [
        'Router IP: ' + self.ip,
        'Routing Table: ' + str(self.table),
        ]
        return '\n'.join(s)

    def __repr__(self):
        return str(self)







