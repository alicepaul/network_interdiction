import os
import time
import networkx as nx
import graphSimplification as gs
from docplex.mp.model import Model

def runMIP(G, k, m):
    # Runs MIP to find optimal subset to remove to maximize vitality of k

    # nodes and edges
    V = []
    V_k = []
    for v in G.nodes():
        V.append(v)
        if (v != k):
            V_k.append(v)

    E = []
    E_k = []
    for (i,j) in G.edges():
        E.append((i,j))
        E.append((j,i))
        if (i != k) and (j != k):
            E_k.append((i,j))
            E_k.append((j,i))

    S_T = [(s,t) for s in V_k for t in V_k if (s != t) and (s <= t)]

    # capacities
    caps = nx.get_edge_attributes(G, 'capacity')
    for (i,j) in G.edges():
        caps[(j,i)] = caps[(i,j)]

    # weights
    weights = dict()
    weights_G = nx.get_node_attributes(G, 'weight')
    for v in V:
        if v not in weights_G:
            weights_G[v] = 1
    for (s,t) in S_T:
        weights[(s,t)] = weights_G[s]*weights_G[t]

    # model
    mod = Model(name='vimax')
    mod.set_time_limit(60*60*2)

    # z variables
    z = mod.binary_var_dict(V, name='z')
    mod.add_constraint(z[k] == 1, 'key vertex')
    mod.add_constraint(mod.sum(z[v] for v in V) >= len(V)-m)
    for v in V:
        if (G.degree[v] == 0):
            mod.add_constraint(z[v] == 1)

    # x variables
    x_ids = [(i,j,s,t) for (i,j) in E for (s,t) in S_T]
    x = mod.continuous_var_dict(x_ids, lb=0, name="x")

    # w variables
    w_ids = [(i,j) for (i,j) in E]
    w = mod.continuous_var_dict(w_ids, lb=0, name="w")

    # y_node vars 
    y_node_ids = [(i,s,t) for i in V_k for (s,t) in S_T]
    y_node = mod.continuous_var_dict(y_node_ids, name="y_node")

    # y_edge vars
    y_edge_ids = [(i,j,s,t) for (i,j) in E_k for (s,t) in S_T]
    y_edge = mod.continuous_var_dict(y_edge_ids, name="y_edge")

    # v variables
    v_ids = S_T
    v = mod.continuous_var_dict(v_ids, lb = 0, name="v")

    # w constraints
    for (i,j) in E:
        mod.add_constraint(w[(i,j)] <= z[i])
        mod.add_constraint(w[(i,j)] <= z[j])
        mod.add_constraint(w[(i,j)] >= z[i]+z[j]-1)

    # x constraints - flow
    for i in V:
        for (s,t) in S_T:
            rhs = 0
            if (s == i):
                rhs = v[(s,t)]
            if (t == i):
                rhs = -v[(s,t)]
            mod.add_constraint(mod.sum(x[(i,j,s,t)] for (_,j) in G.edges(i)) -
                               mod.sum(x[(j,i,s,t)] for (_,j) in G.edges(i)) == rhs)

    # x constraints - relate to w
    for (i,j) in E:
        for (s,t) in S_T:
            mod.add_constraint(x[(i,j,s,t)] <= caps[(i,j)]*w[(i,j)]) 

    # y constraints - flow
    for (i,j) in E_k:
        for (s,t) in S_T:
            mod.add_constraint(y_node[(i,s,t)]-y_node[(j,s,t)]+y_edge[(i,j,s,t)] >= -( 1 - w[(i,j)]))

    # y constraints - pairs
    for (s,t) in S_T:
        mod.add_constraint(-y_node[(s,s,t)]+y_node[(t,s,t)] >= 1)

    # obj function
    mod.maximize(mod.sum(weights[(s,t)]*v[(s,t)] for (s,t) in S_T)- mod.sum(weights[(s,t)]*caps[(i,j)]*y_edge[(i,j,s,t)] for (i,j) in E_k for (s,t) in S_T))

    # solve
    print("Solving model...")
    solution = mod.solve()
    #mod.print_solution()

    # store z values and return solution value and relative MIP gap
    sol_dict = dict()
    for v in V:
        sol_dict[v] = z[v].solution_value

    return(sol_dict, solution.get_objective_value(), mod.solve_details.mip_relative_gap)


# Runs MIP on folder file
my_path = "/Users/Alice/Dropbox/network_interdiction/Data/"
files = [f for f in os.listdir(my_path) if os.path.isfile(os.path.join(my_path,f))]
#files = ["DrugDataRem5Cap1Trial2-undir.dat"]
results = "filename, n, num_edges, time, obj, gap, removed \n"
res_f = open("mip_results_simp2.csv", "w")
res_f.write(results)
res_f.close()
for f in files:
    
    # Read graph
    if (f == ".DS_Store"): 
        continue
    print(f)
    G,k,m = gs.readGraph(os.path.join(my_path,f))
    init_nodes = len(G.nodes())
    init_edges = len(G.edges())

    if (m == 1):
        continue 
    
    results = f+","+str(len(G.nodes()))+"," + str(len(G.edges()))+","

    # Graph simplification
    start = time.time()
    Q = gs.findVertices(G,k)
    H, num_removed = gs.newGraph(G, Q)

    # Check difference
    if (len(Q) == 0):
        continue
    
    # Run MIP
    sol_dict, obj, mip_gap = runMIP(H,k,m)
    end = time.time()

    # Number removed
    num_removed = 0
    for v in H.nodes():
        if sol_dict[v] == 0:
            num_removed += 1

    # Store results
    results += str(end-start)+","+str(obj)+","+str(mip_gap)+","+str(num_removed)+ "\n"
    res_f = open("mip_results_simp2.csv", "a")
    res_f.write(results)
    res_f.close()


