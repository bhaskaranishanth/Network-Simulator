
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
        assert self.link == None
        self.link = link
        

    def get_link(self):
        return self.link

    def get_links(self):
        '''
        Returns a list representation of the link
        '''

        return [self.link]

    def __str__(self):
        print 'Host IP: ' + self.ip
        print 'Link ID: ' + self.link.link_id
        return ''

    def __repr__(self):
        return self.ip
