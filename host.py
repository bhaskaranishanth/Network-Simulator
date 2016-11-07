
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

    def __str__(self):
        s = [
         'Host Details: ' + str(self.ip),
         'Link: ' + self.link.link_id,
        ]
        return '\n'.join(s)
