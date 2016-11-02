
class Host:
    """
    Represents Host
    """
    def __init__(self, ip):
        self.ip = ip
        self.link = None

    def attach_link(self, link):
        '''
        Attach link to the host.
        '''
        self.link = link
        

    def get_link(self):
        return self.link

    