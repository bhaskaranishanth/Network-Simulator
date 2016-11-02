
class Router:
    """
    Represents routers
    """
    def __init__(self, ip):
        self.ip = ip
        self.table = None

    def set_routing_table(self, table):
        self.table = table

    def get_routing_table(self, table):
        return self.table
        


    def __str__(self):
        print 'Routing details'
        print 'IP: ', self.ip
        print 'Routing table: ', self.table