# Network-Simulator
A network congestion simulator. Project for CS 143



This is a sophisticated network congestion simulator that models several TCP/IP protocols and 
analyzes their performance under different situations. The code base is entirely in Python 2.7.0.

Steps to run program
1. Clone the repository (make sure you have the configuration files as well)
2. Go to the configuration files (.conf) and set desired parameters for the network
    - Here is where you also specify for the type of congestion (Reno, Fast, Cubic)
3. Go to constants.py and set the desired simulation values
4. Go to graph.py and set the desired flows and links to plot
4. Enter into command line python main.py
5. Program execution time ranges from a few seconds to a few minutest depending on network and simulation parameters
6. Six graphs will be shown
    -Link rate vs time
    -Buffer occupancy vs time
    -Packet loss vs time
    -Flow rate vs time
    -Window size vs time
    -Packet delay vs time


Example parameters for Reno


