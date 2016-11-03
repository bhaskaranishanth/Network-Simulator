
class Flow:
    def __init__(self, data_size, src=None, dest=None):
        """
        Defines Flow class containing the total amount of data (data_size), 
        source, and destination of the flow
        """
        self.data_size = data_size
        self.src = src
        self.dest = dest

    
    """ Accessor methods """

    def get_data_size(self):
        return self.data_size

    def get_src(self):
        return self.src

    def get_dest(self):
        return self.dest

    
    """ Mutator methods """

    def set_data_size(self, data_size):
        self.data_size = data_size

    def set_src(self, src):
        self.src = src

    def set_dest(self, dest):
        self.dest = dest


    """ Print methods """
    def __str__(self):
        print "Printing flow details..."
        print "Data size:", self.data_size
        print "Source:", self.src
        print "Destination:", self.dest
        return ""

    