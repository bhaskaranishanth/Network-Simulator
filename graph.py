import matplotlib.pyplot as plt 
import numpy as np

# List of methods used to plot graphs

def pck_tot_buffers(pck_graph_dict, time, links):
    for link_id in links.keys():
        link = links[link_id]
        if pck_graph_dict.get(link_id) == None:
            pck_graph_dict[link_id] = []
        pck_graph_dict[link_id].append([time, link.get_num_packets()])

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
    plt.ylabel("Window Size")
    plt.xlabel("Time")
    plt.legend()
    plt.show()

def graph_packet_delay(packet_delay_dict):
    for key in packet_delay_dict:
        packet_delay_list = packet_delay_dict[key]
        lines = []
        x = [elem[0] for elem in packet_delay_list]
        y = [elem[1] for elem in packet_delay_list]

        avg_time = 5
        avg_x, avg_y = smooth_avg_list(x, y, avg_time)
        line_up, = plt.plot(avg_x, avg_y, linewidth = 2.0, label=key)
        lines.append(line_up)

    plt.ylabel("Packet delay")
    plt.xlabel("Time")
    plt.legend()
    plt.show()

def smooth_avg_list(x, y, avg_time):
    avg_x = []
    avg_y = []
    current_time = avg_time
    i = 0
    while i < len(x):
        temp_x = []
        temp_y = []
        while i < len(x) and x[i] < current_time:
            temp_x.append(x[i])
            temp_y.append(y[i])
            i += 1
        current_time += avg_time
        avg_x.append(sum(temp_x)/float(len(temp_x) + 1))
        avg_y.append(sum(temp_y)/float(len(temp_y) + 1))

    return avg_x, avg_y

def graph_packet_loss(packet_loss_dict):
    # Switch back and forth between test case links
    for key in ['L1', 'L2', 'L3']:
    # for key in ['L1', 'L2']:
    # for key in ['L1']:
        packet_loss_list = packet_loss_dict[key]
        lines = []
        x = [elem[0] for elem in packet_loss_list]
        y = [elem[1] for elem in packet_loss_list]

        avg_x = []
        avg_y = []
        avg_time = 1
        current_time = avg_time
        i = 0
        start = 0
        end = 0
        while i < len(x):
            while i < len(x) and x[i] < current_time:
                end = y[i]
                i += 1

            current_time += avg_time
            avg_x.append(x[i - 1])
            avg_y.append(end - start)

            start = end

        line_up, = plt.plot(avg_x, avg_y, linewidth = 2.0, label=key)
        lines.append(line_up)

    plt.ylabel("Packet loss")
    plt.xlabel("Time")
    plt.legend()
    plt.show()


def graph_flow_rate(flow_rate_dict):
    for key in flow_rate_dict:
        flow_rate_list = flow_rate_dict[key]
        lines = []

        x = [elem[0] for elem in flow_rate_list]
        y = [elem[1] for elem in flow_rate_list]

        avg_time = 5
        avg_x, avg_y = smooth_avg_list(x, y, avg_time)

        line_up, = plt.plot(avg_x, avg_y, linewidth = 2.0, label=key)
        lines.append(line_up)

    plt.ylabel("Flow rate")
    plt.xlabel("Time")
    plt.legend()
    plt.show()


def graph_link_rate(link_rate_dict):
    # Switch back and forth between test case links
    for key in ['L1', 'L2', 'L3']:
    # for key in ['L1', 'L2']:
    # for key in ['L1']:
        link_rate_list = link_rate_dict[key]
        lines = []
        x = [elem[0] for elem in link_rate_list]
        y = [elem[1] for elem in link_rate_list]

        avg_time = 5
        avg_x, avg_y = smooth_avg_list(x, y, avg_time)

        line_up, = plt.plot(avg_x, avg_y, linewidth = 2.0, label=key)
        lines.append(line_up)

    plt.ylabel("Link rate")
    plt.xlabel("Time")
    plt.legend()
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
    plt.show()

def graph_pck_buf(pck_graph_dict):
    lines = []
    for key,value in pck_graph_dict.iteritems():

        x = [elem[0] for elem in value]
        y = [elem[1] for elem in value]

        avg_time = 5
        avg_x, avg_y = smooth_avg_list(x, y, avg_time)

        # Switch back and forth between test case links
        if key in ['L1', 'L2', 'L3']:
        # if key in ['L1', 'L2']:
        # if key in ['L1']:
            line_up, = plt.plot(avg_x, avg_y, linewidth = 2.0, label = key)
            lines.append(line_up)

    plt.ylabel("Buffer Occupancy")
    plt.xlabel("Time")
    plt.legend()
    plt.show()

