ext = '1'

HOST_FILE = './conf/host' + ext + '.conf'
ROUTER_FILE = './conf/router' + ext + '.conf'
LINK_FILE = './conf/link' + ext + '.conf'
FLOW_FILE = './conf/flow' + ext + '.conf'


TIMEOUT_VAL = 2
ROUTING_INTERVAL = 60
WINDOW_SIZE = 1
THRESHOLD = 100
PERIODIC_FAST_INTERVAL = .1
GRAPH_EVENT_INTERVAL = .1

ALPHA = 100
GAMMA = .7

# If FAST = 1, use Fast TCP. Otherwise, TCP Reno. 
# FAST = 0