
class Router:
    """
    Represents routers
    """
    def __init__(self, ip):
        self.ip = ip
        self.table = None
        self.lst = set()

    def set_routing_table(self, table):
        self.table = table

    def get_routing_table(self, table):
        return self.table
        
    def add_link(self, link):
        ''' 
        Adds a Link object to the list
        '''
        self.lst.add(link)

    def get_links(self):
        '''
        Returns a list of Link objects
        '''
        return self.lst


    def __str__(self):
        print 'Routing details'
        print 'IP: ', self.ip
        print 'Routing table: ', self.table
        return ''