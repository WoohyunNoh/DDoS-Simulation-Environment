from mininet.cli import CLI
from mininet.net import Mininet
from mininet.link import Link, TCLink, Intf
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import random as rand

if '__main__' == __name__:
    net = Mininet(link=TCLink)
    G = nx.Graph()

    number_of_routers = int(input("Number of routers : "))
    avg_links_per_node = int(input("Average links per node : "))
    hosts_per_router = int(input("Hosts per router : "))
    rand_seed = int(input("Rand seed : "))
    rand.seed(rand_seed)
    router_nodes = []
    host_nodes = []
    routers_appended = [[0 for cols in range(1)] for rows in range(number_of_routers)]
    path = []
    band = {}
    gw = {}
    color_map = []


    def append_hosts_to_switch(router_num):
        i = 1
        switch_num = str(router_num)
        for host_num in range((router_num - 1) * hosts_per_router + 1, router_num * hosts_per_router + 1):
            inum = str(i)
            num = str(host_num)
            hnum = net.addHost('h' + num)
            net.addLink(hnum, 's' + switch_num)
            hnum.cmd("ip addr add " + switch_num + ".0.0." + inum + "/24 brd + dev h" + num + "-eth0")
            hnum.cmd("ip route add default via " + switch_num + ".0.0.254")
            G.add_node('h' + num)
            G.add_edge(router_num, 'h' + num)

            i = i + 1


    def append_and_link_switch(router_num):
        num = str(router_num)
        switch = net.addSwitch('s' + num)
        router = router_nodes[router_num-1]
        net.addLink(router, switch)
        router.cmd("ifconfig r"+num+"-eth0 "+num+".0.0.254 netmask 255.255.255.0")
        router.cmd("echo 1 > /proc/sys/net/ipv4/ip_forward")
        link = num + 'tos'
        band[link] = num + ".0.0.0"
        return switch


    def set_br(switch, num):
        switch.cmd("ifconfig br"+num+" down")
        switch.cmd("brctl delbr br"+num)
        switch.cmd("brctl addbr br"+num)
        for intf_num in range (1, hosts_per_router+2):
            i_num = str(intf_num)
            switch.cmd("brctl addif br"+num+" s"+num+"-eth"+i_num)
        switch.cmd("ifconfig br"+num+" up")


    def draw_router_matrix(router_num):
        nt_graph = np.zeros((router_num, router_num))
        links = router_num * avg_links_per_node
        link_count = 0
        vertex = 0
        while link_count <= links:
            n = rand.randrange(0, router_num - 1)
            if nt_graph[vertex, n] == 0 and vertex != n:
                nt_graph[vertex, n] = 1
                nt_graph[n, vertex] = 1
                routers_appended[vertex].append(n + 1)
                routers_appended[n].append(vertex + 1)
                add_data(vertex + 1, n + 1)
                link_count += 2
                link_router(vertex + 1, n + 1)
                vertex += 1
                if vertex == router_num:
                    vertex = 0


    def link_router(vertex, n):
        num1 = str(vertex)
        num2 = str(n)
        G.add_edge(vertex, n)
        net.addLink(router_nodes[vertex-1], router_nodes[n-1])
        if(vertex>n):
            v_intf = str(routers_appended[vertex-1].index(n))
            n_intf = str(routers_appended[n-1].index(vertex))
            router_nodes[vertex-1].cmd("ifconfig r"+num1+"-eth"+v_intf+" "+num1+".0."+v_intf+".1 netmask 255.255.255.0")
            router_nodes[n-1].cmd("ifconfig r"+num2+"-eth"+n_intf+" "+num1+".0."+v_intf+".2 netmask 255.255.255.0")
        else:
            v_intf = str(routers_appended[vertex - 1].index(n))
            n_intf = str(routers_appended[n - 1].index(vertex))
            router_nodes[vertex - 1].cmd("ifconfig r" +num1+ "-eth" +v_intf+ " " +num2+ ".0."+n_intf+".2 netmask 255.255.255.0")
            router_nodes[n - 1].cmd("ifconfig r" +num2+ "-eth"+ n_intf + " " +num2+ ".0."+n_intf+".1 netmask 255.255.255.0")


    def add_data(vertex, node):
        if vertex > node:
            v_intf = str(routers_appended[vertex - 1].index(node))
            v = str(vertex)
            n = str(node)
            link = v + 'to' + n
            band[link] = v + ".0." + v_intf + ".0"
            gw[link] = v + ".0." + v_intf + ".2"
            link = n + 'to' + v
            band[link] = v + ".0." + v_intf + ".0"
            gw[link] = v + ".0." + v_intf + ".1"
        else:
            n_intf = str(routers_appended[node - 1].index(vertex))
            v = str(vertex)
            n = str(node)
            link = v + 'to' + n
            band[link] = n + ".0." + n_intf + ".0"
            gw[link] = n + ".0." + n_intf + ".1"
            link = n + 'to' + v
            band[link] = n + ".0." + n_intf + ".0"
            gw[link] = n + ".0." + n_intf + ".2"


    def routing(path, source, destination):
        length = len(path)
        src = str(source)
        dst = str(destination)
        for l in range(0, length):
            r_num = path[l] - 1
            if path[l] == source:
                next = str(path[l + 1])
                b_link = dst + "tos"
                g_link = src + "to" + next
                router_nodes[r_num].cmd(" ip route add " + band[b_link] + "/24 via " + gw[g_link])
                continue
            if path[l] == destination:
                prev = str(path[l - 1])
                b_link = src + "tos"
                g_link = dst + "to" + prev
                router_nodes[r_num].cmd(" ip route add " + band[b_link] + "/24 via " + gw[g_link])
                continue
            current = str(path[l])
            next = str(path[l + 1])
            prev = str(path[l - 1])
            b_link = dst + "tos"
            g_link = current + "to" + next
            router_nodes[r_num].cmd(" ip route add " + band[b_link] + "/24 via " + gw[g_link])
            b_link = src + "tos"
            g_link = current + "to" + prev
            router_nodes[r_num].cmd(" ip route add " + band[b_link] + "/24 via " + gw[g_link])


    for router_num in range(1, number_of_routers+1):
        num = str(router_num)
        router_nodes.append(net.addHost('r'+num))
        switch_node = append_and_link_switch(router_num)
        append_hosts_to_switch(router_num)
        set_br(switch_node, num)
        G.add_node(router_num)
    draw_router_matrix(router_num)

    for source in range(1, number_of_routers + 1):
        for destination in range(1, number_of_routers):
            if source == destination:
                continue
            path = nx.dijkstra_path(G, source, destination)
            routing(path, source, destination)

    for node in G:
        if type(node) is str:
            color_map.append('green')
        else:
            color_map.append('red')
    nx.draw(G, node_color = color_map, with_labels=True)
    plt.show(block=False)
    CLI(net)
    net.stop()
