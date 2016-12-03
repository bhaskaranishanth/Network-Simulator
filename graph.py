import matplotlib.pyplot as plt 
import numpy as np 
def pck_tot_buffers(time, links):
    all_points = []
    for link_id in links.keys():
        link = links[link_id]
        all_points.append([link_id, time, link.get_num_packets()])
    return all_points

def drop_packets(time, links):
    drop_packets_list = []
    for link_id in links.keys():
        link = links[link_id]
        drop_packets_list.append([link_id, time, link.get_drop_packets()])
    return drop_packets_list

def graph_window_size(window_size_dict):
    for key in window_size_dict:
        window_size_list = window_size_dict[key]
        lines = []
        x = [elem[0] for elem in window_size_list]
        y = [elem[1] for elem in window_size_list]
        line_up, = plt.plot(x, y, linewidth = 2.0, label=key)
        lines.append(line_up)
        # interval = 0
        # step = 5
        # start = 100
        # i = 100
        # new_x = [elem[0] for elem in window_size_list[:i]]
        # new_y = [elem[1] for elem in window_size_list[:i]]

        # while i < len(x):
        #     new_sum_x = 0
        #     new_sum_y = 0
        #     while i < len(x) and interval < x[i] and x[i] < interval + step:
        #         new_sum_x += x[i]
        #         new_sum_y += y[i]
        #         i += 1
        #     if i >= len(x):
        #         break

        #     new_avg_x = 0
        #     new_avg_y = 0
        #     if start - i == 0:
        #         new_avg_x = new_sum_x
        #         new_avg_y = new_sum_y
        #     else:
        #         new_avg_x = new_sum_x / (i - start)
        #         new_avg_y = new_sum_y / (i - start)
        #     start = i
        #     i += 1
        #     interval += step
        #     new_x.append(new_avg_x)
        #     new_y.append(new_avg_y)

        # line_up, = plt.plot(new_x, new_y, linewidth = 2.0)

    plt.ylabel("Window Size")
    plt.xlabel("Time")
    plt.legend()
    #plt.axis([0,max_x, 0, max_y * 2])
    plt.show()

def graph_packet_delay(packet_delay_dict):
    for key in packet_delay_dict:
        packet_delay_list = packet_delay_dict[key]
        lines = []
        x = [elem[0] for elem in packet_delay_list]
        y = [elem[1] for elem in packet_delay_list]
        line_up, = plt.plot(x, y, linewidth = 2.0, label=key)
        lines.append(line_up)

    plt.ylabel("Packet delay")
    plt.xlabel("Time")
    plt.legend()
    #plt.axis([0,max_x, 0, max_y * 2])
    plt.show()

def graph_flow_rate(flow_rate_dict):
    for key in flow_rate_dict:
        flow_rate_list = flow_rate_dict[key]
        lines = []
        x = [elem[0] for elem in flow_rate_list]
        y = [elem[1] for elem in flow_rate_list]
        line_up, = plt.plot(x, y, linewidth = 2.0, label=key)
        lines.append(line_up)

    plt.ylabel("Flow rate")
    plt.xlabel("Time")
    plt.legend()
    #plt.axis([0,max_x, 0, max_y * 2])
    plt.show()



def graph_pck_drop_rate(drop_packets):
    max_time = int(drop_packets[len(drop_packets) - 1][0][1]) + 1
    drop_rate_arr = [[0 for y in range(max_time)] for z in range(len(drop_packets[0]))]
    old_time = 0
    for t in range(len(drop_packets)):
        for l in range(len(drop_packets[0])):
            time_dropped = int(drop_packets[t][l][1])
            pck_dropped = drop_packets[t][l][2]
            drop_rate_arr[l][time_dropped]= pck_dropped
    for l in range(len(drop_rate_arr)):
        for t in range(max_time - 1, 0, -1):
            drop_rate_arr[l][t] = drop_rate_arr[l][t] - drop_rate_arr[l][t - 1]
    lines = []
    for l in range(len(drop_rate_arr)):
        lab = drop_packets[0][l][0]
        x = range(max_time)
        y = drop_rate_arr[l]
        line_up, = plt.plot(x, y, linewidth = 2.0, label = lab)
        lines.append(line_up)
    plt.ylabel("Rate Of Packets Dropped")
    plt.xlabel("Time")
    plt.legend(lines)
    #plt.axis([0,max_x, 0, max_y * 2])
    plt.show()

def graph_pck_buf(points):
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
    for i in range(0, len(points[0]), 1):

        x = [elem[0][1] for elem in points][0:len(points):500]
        y = [elem[i][2] for elem in points][0:len(points):500]

        if points[0][i][0] in ['L2', 'L1', 'L3']:
            line_up, = plt.plot(x, y, linewidth = 2.0, label = points[0][i][0])
            lines.append(line_up)

    plt.ylabel("Packets In Buffer")
    plt.xlabel("Time")
    plt.legend()
    #plt.axis([0,max_x, 0, max_y * 2])
    plt.show()

