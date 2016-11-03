
class EventQueue:
    """
    Defines global EventQueue class to keep track of all events in the network.
    Note: Enqueues at beginning (index 0) and dequeues at end of array.
    """
    def __init__(self):
        events = []

    
    """ Queue methods """

    def is_empty(self):
        return self.events == []

    def enqueue(self, event):
        self.events.insert(0, event)

    def dequeue(self):
        return self.events.pop()

    def size(self):
        return len(self.events)


    """ Print methods """
    def __str__(self):
        print "Printing EventQueue details..."
        for i in range(len(self.events)):
            print "Event", i, ":", self.events[i]
        return ""

