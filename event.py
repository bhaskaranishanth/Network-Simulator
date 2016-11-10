
TIMEOUT_EVENT = 0
ENQUEUE_EVENT = 1
NORMAL_EVENT = 2

type_dict = {TIMEOUT_EVENT: "TIMEOUT_EVENT", 
            ENQUEUE_EVENT : "ENQUEUE_EVENT",
            NORMAL_EVENT : "NORMAL_EVENT"}
class Event:
    """Defines Event which contains the details about the event type, and 
    the information

    Packet Type:
    0 - Timeout Event
    1 - Acknowledgement Packet
    2 - Router Packet
    """
    def __init__(self, event_type, initial_time, src, dest, flow, data):
        self.check_type(event_type)
        self.type = event_type
        self.src = src
        self.dest = dest 
        self.flow = flow
        self.initial_time = initial_time
        self.event_data = data

    def check_type(self, event_type):
        assert event_type in [TIMEOUT_EVENT, ENQUEUE_EVENT, NORMAL_EVENT]


    """ MUTATOR METHODS """

    def get_type(self):
        return type_dict[self.type]

    def get_src(self):
        return self.src

    def get_dest(self):
        return self.dest

    def get_initial_time(self):
        return self.initial_time

    def get_flow(self):
        return self.flow

    def get_data(self):
        return self.event_data

    """ ACCESSOR METHODS """

    def set_type(self, event_type):
        self.check_type(event_type)
        self.type = event_type

    def set_src(self, src):
        self.src = src

    def set_dest(self, dest):
        self.dest = dest

    def set_flow(self, flow):
        self.flow = flow

    def set_initial_time(self, initial_time):
        self.flow = initial_time

    def set_data(self, data):
        self.event_data = data


    """ PRINT METHODS """
    def __str__(self):
        print "Printing Event Details"
        print "Type: ", type_dict[self.type]
        print "Source: ", self.src
        print "Destination: ", self.dest
        print "Flow: ", self.flow
        print "Initial Time: ", initial_time
        return ""