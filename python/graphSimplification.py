import networkx as nx
import os

def readGraph(filename):
    # Reads in instance in AMPL format and creates networkx graph

    f = open(filename)
    lines = f.readlines()
    
    G = nx.Graph()
    edge_mode = False
    node_weight_mode = False
    for line in lines:

        line_rep = line.strip()
        line_rep = line_rep.replace(";", "")
        words = line_rep.split(" ")

        # Empty line
        if (len(words) <= 1):
            continue

        # Params
        if (words[1] == "k"):
            k = int(words[-1])

        elif (words[1] == "m"):
            m = int(words[-1])

        # Add all vertices (assumes numeric type)
        elif (words[1] == "Vertices"):
            for j in words[3:]:
                if(j.isdigit()):
                    G.add_node(int(j))
        
        # All remaining elements are edges
        elif (words[1] == "u"):
            edge_mode = True

        elif (words[1] == "w"):
            edge_mode = False
            node_weight_mode = True

        # Add edge with capcity
        elif (edge_mode):
            word_nums = []
            for j in words:
                if (j.isdigit()):
                    word_nums.append(int(j))
            G.add_edge(word_nums[0], word_nums[1], 
                    capacity = word_nums[2])

       
        elif (node_weight_mode):
            word_nums = []
            for j in words:
                if (j.isdigit()):
                    word_nums.append(int(j))
            G.nodes[word_nums[0]]["weight"] = word_nums[1]

    f.close()
    return(G, k, m)


def findVertices(G,k):
    # Finds minimum set of vertices that disconnect nodes from k

    # Dictionary for whether we have explored path from node to k
    explored = dict()
    for i in G.nodes():
        explored[i] = False

    # All vertices that we will find subgraphs for
    verts = dict()

    # Go through all vertices
    for i in G.nodes():

        # If already saw that it has 1 path we can continue
        if ((i == k) | (explored[i])):
            continue

        # Otherwise follow path if only one node-disjoint one
        paths = list(nx.node_disjoint_paths(G, i, k))
        if (len(paths) == 1):
            
            # Go through path and find first vertex > 1 path or reach k
            for ind_j in range(len(paths[0])):
                j = paths[0][ind_j]
                explored[j] = True
                paths_j = list(nx.node_disjoint_paths(G,j,k))

                # If j has more than one path- here is where disconnect happens
                if ((len(paths_j) > 1) and (j != k)):
                    if (j not in verts):
                        verts[j] = set(paths[0][0:ind_j])
                    else:
                        verts[j].update(paths[0][0:ind_j])
                    break

                # If we reach k then that whole path could be condensed
                elif ((j == k) & (len(paths[0]) > 2)):
                    last_j = paths[0][-2]
                    if (last_j not in verts):
                        verts[last_j] = set(paths[0][0:(ind_j-1)])
                    else:
                        verts[last_j].update(paths[0][0:(ind_j-1)])
                    break


    return(verts)


def newGraph(G, verts):
    # Creates the new graph (weighted) by condensing vertices in verts to leaves
    # in the new graph 
    # Runs the simplification procedure outlined in paper

    next_id = max(G.nodes())+1
    num_removed = 0

    for v in verts.keys():

        # Get max flow from each removed element to v
        max_flows = dict()
        for u in verts[v]:
            flow_u = nx.maximum_flow(G, u, v)[0]
            if (flow_u in max_flows):
                max_flows[flow_u] += 1
            else:
                max_flows[flow_u] = 1

        # Remove old nodes
        for u in verts[v]:
            num_removed += 1
            G.remove_node(u)

	# Add new weighted nodes
        for u in max_flows:
            G.add_node(next_id, weight = max_flows[u])
            G.add_edge(next_id, v, capacity = u)
            next_id += 1

    #print(num_removed)
    return(G, num_removed)

def writeGraph(G, k, m):
    # Writes instance in AMPL format

    # add vertices
    s = "set Vertices := "
    for v in G.nodes():
        s += str(v)+" "
    s += "; \n"

    # add params
    s += "param k := " + str(k) + ";\n"
    s += "param m := " + str(m) + ";\n"

    # add edges
    s += "set Edges := "
    for e in G.edges():
        s += "("+str(e[0])+","+str(e[1])+") "
    s += ";\n"

    # add edges without k
    s += "set EdgesPrime := "
    for e in G.edges():
        if (e[0] != k) and (e[1] != k):
            s += "("+str(e[0])+","+str(e[1])+") "
    s += ";\n"

    # add edge weights
    s += "param u := \n"
    for e in G.edges(data = True):
        s += str(e[0])+" "+str(e[1]) + " " + str(e[2]["capacity"])+"\n"
    s += "; \n"

    # add node weights
    s += "param w := \n"
    for v in G.nodes(data = True):
        if "weight" in v[1]:
            s += str(v[0])+" " + str(v[1]["weight"])+"\n"
        else:
            s += str(v[0])+" 1\n"
    s += ";"

    return(s)


def run_all_simp():
    # Runs graph simplification and creates new data file for
    # the simplified graph
    
    my_path = "/Users/alice/Dropbox/Network_Interdiction/Data/"
    files = [f for f in os.listdir(my_path) if os.path.isfile(os.path.join(my_path,f))]
    res_str = "File name, n, m, # single VD path, n', m' \n"
    for f in files:
        print(f)
        if (f == ".DS_Store"):
            continue 
        G,k,m = readGraph(os.path.join(my_path,f))
        init_nodes = len(G.nodes())
        init_edges = len(G.edges())
        print(len(G.nodes()), len(G.edges()))
        res_str += f+","+str(len(G.nodes()))+","+str(len(G.edges()))+","
        verts = findVertices(G,k)
        H, num_removed = newGraph(G, verts)
        s = writeGraph(H, k, m)
        print(len(H.nodes()), len(H.edges()))
        if (len(H.nodes()) < init_nodes) or (len(H.edges()) < init_edges):
            f2 = open("/Users/Alice/Dropbox/Network_Interdiction/SimpData/upd-"+f,"w")
            f2.write(s)
            f2.close()
        res_str += str(num_removed)+","+str(len(H.nodes()))+","+str(len(H.edges()))+"\n"

    f = open("/Users/Alice/Dropbox/Network_Interdiction/simp_results.csv","w")
    f.write(res_str)
    f.close()
#run_all_simp()
