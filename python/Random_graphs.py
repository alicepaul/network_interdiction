import networkx as nx
from graphSimplification import writeGraph
import random

def ER_graph(n, p):
    # Creates random ER graph with n^2 nodes

    # Create random graph
    connected = False
    while (connected == False):
        G = nx.gnm_random_graph(n**2, 2*(n**2)-2*n)
        connected = nx.is_connected(G)
    
    # Create capacities
    random_caps = [i for i in range(1, n+1)]
    cap_dict = {}
    for e in G.edges():
        cap_dict[e]= {'capacity': random.choice(random_caps)} 
    nx.set_edge_attributes(G, cap_dict)
    return(G)

def find_k_central(G):
    bet = nx.betweenness_centrality(G)
    max_bet = 0
    vert = None
    for i in G.nodes():
        if (bet[i] > max_bet):
            max_bet = bet[i]
            vert = i
    return(i)

def find_k_random(G):
    return(random.choice(list(G.nodes())))

#n = 5
#p = 4/(n**2 -1)
#G = ER_graph(n,p)
#m1 = 1
#m2 = n
#k1 = find_k_central(G)
#k2 = find_k_random(G)
#print(G)

num_nodes = [5,6,7,8]
for n in num_nodes:
    for m in [1, n]:
        for i in range(3):
            p = 0.2
            G = ER_graph(n, p)
            k = find_k_central(G)
            s = writeGraph(G, int(k), m)
            f = open("/Users/Alice/Dropbox/Network_Interdiction/Data/ER"+str(n**2)+
            "Rem"+str(m)+"Cap"+str(n)+"Trial"+str(i+1)+".dat", "w")
            f.write(s)
            f.close()



    



