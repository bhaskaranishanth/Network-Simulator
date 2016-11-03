
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
	def __init__(self, event_type, initialTime, src = None, dest = None, flow = None):
		self.check_type(event_type)
		self.type = event_type
		self.src = src
		self.dest = dest 
		self.flow = flow

	def check_type(self, event_type):
        assert event_type in [TIMEOUT_EVENT, ENQUEUE_EVENT, NORMAL_EVENT]