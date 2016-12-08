ext = '2'

HOST_FILE = './conf/host' + ext + '.conf'
ROUTER_FILE = './conf/router' + ext + '.conf'
LINK_FILE = './conf/link' + ext + '.conf'
FLOW_FILE = './conf/flow' + ext + '.conf'


TIMEOUT_VAL = 5
ROUTING_INTERVAL = 500
WINDOW_SIZE = 1
THRESHOLD = 1000
PERIODIC_FAST_INTERVAL = .1
GRAPH_EVENT_INTERVAL = .1

ALPHA = 15
GAMMA = .5


# Cubic parameters
BETA = 0.2
C = 4

# If FAST = 1, use Fast TCP. Otherwise, TCP Reno. 
# FAST = 0
