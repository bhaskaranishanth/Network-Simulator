import matplotlib.pyplot as plt 
def pck_tot_buffers(time, links):
    tot_pckt = 0
    for link_id in links.keys():
        link = links[link_id]
        tot_pckt += link.get_num_packets()
    return [time, tot_pckt]

def graph(points):
    x_coord = []
    y_coord = []
    max_y = -1000000000000
    max_x = -1000000000000
    for i in range(len(points)):
        x_coord.append(points[i][0])
        y_coord.append(points[i][1])
        if points[i][1] > max_y:
            max_y = points[i][1]
        if points[i][0] > max_x:
            max_x = points[i][0]
    plt.plot(x_coord, y_coord)
    plt.ylabel("Packets In Buffer")
    plt.xlabel("Time")
    plt.axis([0,max_x, 0, max_y * 2])
    plt.show()

