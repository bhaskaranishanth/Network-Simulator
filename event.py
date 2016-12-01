
TIMEOUT_EVENT = "TIMEOUT_EVENT"
LINK_TO_ENDPOINT = "LINK_TO_ENDPOINT"
PACKET_RECEIVED = "PACKET_RECEIVED"
DYNAMIC_ROUTING = "DYNAMIC_ROUTING"
ROUTING_PACKET_RECEIVED = "ROUTING_PACKET_RECEIVED"
UPDATE_WINDOW = "UPDATE_WINDOW"
GRAPH_EVENT = "GRAPH_EVENT"

type_events = [TIMEOUT_EVENT, LINK_TO_ENDPOINT, PACKET_RECEIVED, DYNAMIC_ROUTING, ROUTING_PACKET_RECEIVED, UPDATE_WINDOW, GRAPH_EVENT]


class Event:
    """Defines Event which contains the details about the event type, and 
    the information

    Packet Type:
    0 - Timeout Event
    1 - Acknowledgement Packet
    2 - Router Packet
    """
    def __init__(self, event_type, initial_time, src, dest, data):
        self.check_type(event_type)
        assert type(src) == str or event_type == DYNAMIC_ROUTING or event_type == GRAPH_EVENT
        assert type(dest) == str or event_type == DYNAMIC_ROUTING or event_type == UPDATE_WINDOW or event_type == GRAPH_EVENT

        self.type = event_type
        self.src = src
        self.dest = dest 
        self.initial_time = initial_time
        self.event_data = data

    def check_type(self, event_type):
        assert event_type in type_events


    """ MUTATOR METHODS """

    def get_type(self):
        return self.type

    def get_src(self):
        return self.src

    def get_dest(self):
        return self.dest

    def get_initial_time(self):
        return self.initial_time

    def get_data(self):
        return self.event_data

    """ ACCESSOR METHODS """

    def set_type(self, event_type):
        self.check_type(event_type)
        self.type = event_type

    def set_src(self, src):
        assert type(src) == str
        self.src = src

    def set_dest(self, dest):
        assert type(dest) == str
        self.dest = dest

    def set_initial_time(self, initial_time):
        self.flow = initial_time

    def set_data(self, data):
        self.event_data = data


    """ PRINT METHODS """
    def __str__(self):
        print "Printing Event Details"
        print "Type: ", self.type
        print "Source: ", self.src
        print "Destination: ", self.dest
        print "Initial Time: ", self.initial_time
        print 'Event id: ', id(self)
        if self.event_data != None:
            print 'Packet id: ', self.event_data.packet_id
            print 'Packet Type: ', self.event_data.get_type()
        return ""