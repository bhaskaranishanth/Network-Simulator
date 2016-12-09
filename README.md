# Network-Simulator (Team Aloha Vegas)
Developed a sophisticated network congestion simulator to model and analyze several TCP/IP protocols. Code base is entirely in Python 2.7.0.

## How to run
1. Clone entire repository, including configuration file
2. Edit configuration files appropriately (under conf/, see Configuration Files below)
3. Set parameters in constants.py (see Constants below)
4. Update which links to print out in graph.py
5. Run the command: `python main.py` **WARNING: Execution time ranges from a minute to almost half-an-hour**

## Configuration Files
Flow configuration example (i.e. flow1.conf):
```
Flow ID|Flow Src|Flow Dest|Data Amt|Flow Start|TCP Fast
F1|H1|H2|20|.5|0
```

Changing configuration algorithms for flows is simple. Modify the last parameter for flow file to take the appropriate value.

Reno | Fast | Cubic
--- | --- | ---
*0* | *1* | *2*



## Constants
**TCP FAST Test Case 1**
```
ext = '2'

HOST_FILE = './conf/host' + ext + '.conf'
ROUTER_FILE = './conf/router' + ext + '.conf'
LINK_FILE = './conf/link' + ext + '.conf'
FLOW_FILE = './conf/flow' + ext + '.conf'

TIMEOUT_VAL = 5
ROUTING_INTERVAL = 100
WINDOW_SIZE = 1
THRESHOLD = 1000
PERIODIC_FAST_INTERVAL = .1
GRAPH_EVENT_INTERVAL = .1

ALPHA = 100
GAMMA = .7

# Cubic parameters
BETA = 0.2
C = 4
```
**TCP FAST Test Case 2**

```
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

ALPHA = 100
GAMMA = .1

# Cubic parameters
BETA = 0.2
C = 4
```

**TCP Cubic Test Case 1**
```
ext = '1'

HOST_FILE = './conf/host' + ext + '.conf'
ROUTER_FILE = './conf/router' + ext + '.conf'
LINK_FILE = './conf/link' + ext + '.conf'
FLOW_FILE = './conf/flow' + ext + '.conf'

TIMEOUT_VAL = 5
ROUTING_INTERVAL = 50
WINDOW_SIZE = 1
THRESHOLD = 1000
PERIODIC_FAST_INTERVAL = .1
GRAPH_EVENT_INTERVAL = .1

ALPHA = 15
GAMMA = .5

# Cubic parameters
BETA = 0.2
C = 4
```

**TCP Cubic Test Case 2**

```
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
```

**TCP Reno Test Case 1**
```
ext = '1'

HOST_FILE = './conf/host' + ext + '.conf'
ROUTER_FILE = './conf/router' + ext + '.conf'
LINK_FILE = './conf/link' + ext + '.conf'
FLOW_FILE = './conf/flow' + ext + '.conf'

TIMEOUT_VAL = 2
ROUTING_INTERVAL = 40
WINDOW_SIZE = 1
THRESHOLD = 1000
PERIODIC_FAST_INTERVAL = .1
GRAPH_EVENT_INTERVAL = .1

ALPHA = 15
GAMMA = .5

# Cubic parameters
BETA = 0.2
C = 4
```

**TCP Reno Test Case 2**

```
ext = '2'

HOST_FILE = './conf/host' + ext + '.conf'
ROUTER_FILE = './conf/router' + ext + '.conf'
LINK_FILE = './conf/link' + ext + '.conf'
FLOW_FILE = './conf/flow' + ext + '.conf'

TIMEOUT_VAL = 5
ROUTING_INTERVAL = 100
WINDOW_SIZE = 1
THRESHOLD = 1000
PERIODIC_FAST_INTERVAL = .1
GRAPH_EVENT_INTERVAL = .1

ALPHA = 15
GAMMA = .5

# Cubic parameters
BETA = 0.2
C = 4
```


