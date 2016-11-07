
def print_dict(d):
    print 'Dictionary...'
    for k in d:
        print 'Key: %s Value: %s' % (k, d[k])


def print_host(h):
    print 'Hosts..........'
    print '-' * 80
    for k in h:
        print h[k]

def print_router(r):
    print 'Router..........'
    print '-' * 80
    for k in r:
        print r[k]


def print_link(l):
    print 'Link'
    print '-' * 80
    for k in l:
        print l[k]
