import matplotlib.pyplot as plt 
import numpy as np 
def pck_tot_buffers(time, links):
    all_points = []
    for link_id in links.keys():
        link = links[link_id]
        all_points.append([link_id, time, link.get_num_packets()])
    return all_points

def graph(points):
    # x_coord = []
    # y_coord = []
    # max_y = -1000000000000
    # max_x = -1000000000000
    # for i in range(len(points)):
    #     x_coord.append(points[i][0])
    #     y_coord.append(points[i][1])
    #     if points[i][1] > max_y:
    #         max_y = points[i][1]
    #     if points[i][0] > max_x:
    #         max_x = points[i][0]

    # num_links = len(points[0])
    # num_times = len(points)
    # x_coord = [] 
    # for i in range(len(points)):
    #     x_coord.append(points[i][0][1])

    # y_coord = np.zeros((num_links, num_times))
    # for i in range(len(num_links)):
    #     for j in range(len(num_times)):
    #         y_coord[i][j] = points[j][i][2]

    lines = []
    for i in range(len(points[0])):
        x = [elem[0][1] for elem in points]
        y = [elem[i][2] for elem in points]
        line_up, = plt.plot(x, y, linewidth = 2.0, label = points[0][i][0])
        lines.append(line_up)

    plt.ylabel("Packets In Buffer")
    plt.xlabel("Time")
    plt.legend(handles = lines)
    #plt.axis([0,max_x, 0, max_y * 2])
    plt.show()

