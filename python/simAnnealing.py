import networkx as nx
import numpy as np
import graphSimplification as gs
from random import sample

def gomoryFlow(T, u, v):
    path = nx.shortest_path(T, u, v, weight="weight")
    cut_value, _ =  min((T[u][v]["weight"], (u, v)) for (u, v) in zip(path, path[1:])) 
    return cut_value

def getAllPairsFlow(G, k, vertDict, weighted = False):
    # Gets cost of a solution represented by vertDict
    # Assumes k is not in the dictionary

    # Get graph with and without k
    H = G.copy()
    Hk = H.copy()
    Hk.remove_node(k)

    # Remove vertices marked
    for v in vertDict.keys():
        if vertDict[v] == 0:
            H.remove_node(v)
            Hk.remove_node(v)

    # Get gomory-hu trees
    H_tree = nx.gomory_hu_tree(H)
    Hk_tree = nx.gomory_hu_tree(Hk)

    # Calculate all pairs max flow
    V = list(vertDict.keys())
    flow1 = 0
    flow2 = 0
    for i in range(len(V)-1):
        weight_i = 1
        if (weighted):
            weight_i = G.node[V[i]]['weight']

        for j in range(i+1, len(V)):
            weight_j = 1
            if (weighted):
                weight_j = G.node[V[j]]['weight']

            # For pairs both in current solution - find max flow in both graphs
            if (vertDict[V[i]] == 1) and (vertDict[V[j]] == 1):
                flow1 += weight_i*weight_j*gomoryFlow(H_tree, V[i], V[j])
                flow2 += weight_i*weight_j*gomoryFlow(Hk_tree, V[i], V[j])
    
    return(flow1-flow2)

def localSearch(G, k, m, vertDict, maxiters = 100, eps = .01):
    # Local search - only looks at single flips
    # Starts with vertDict solution

    # Starting conditions
    obj = getAllPairsFlow(G, k, vertDict)
    chosen = 0
    for v in vertDict:
        if vertDict[v] == 0:
            chosen += 1
    iters = 0

    # Max iterations
    V = list(vertDict.keys())
    while (iters < maxiters):
        iters += 1
        start_obj = obj

        for i in range(len(V)-1):

            # Try swapping just i
            vi = V[i]
            if (chosen+2*vertDict[vi]-1) <= m:
                vertDict[vi] = 1-vertDict[vi]
                try_obj = getAllPairsFlow(G, k, vertDict)
                if (try_obj > obj):
                    obj = try_obj
                    chosen -= 2*vertDict[vi]-1
                else:
                    vertDict[vi] = 1-vertDict[vi]
            
        if (start_obj > 0) and (obj - start_obj)/start_obj <= eps:
            break
    
    return(obj, vertDict)

def getAcceptanceProb(e1, e2, T):
    # Calculates acceptance probability based on diff in obj fcn
    if (e2 > e1):
        return(1)
    return np.exp(-(e1-e2)/T)

def getInitTemp(G, k, vertDict):
    # Finds initial temperature so that will accept 90% of currrent obj
    # with 95% probability
    obj = getAllPairsFlow(G, k, vertDict)
    V = list(vertDict.keys())
    min_obj = 0.9*obj
    T  = (min_obj-obj)/np.log(0.95)
    return(T)

def simulatedAnnealing(G, k, m, vertDict = dict(), maxIters = 1000, alpha = 0.95):
    # Simulated annealing
    # Stops if no improvement in maxIters iterations
     
    # Create starting solution with no vertices chosen
    # vertDict = dict()
    V = [] # don't consider removing leaves
    for i in G.nodes():
        if (i != k):
            if (i not in vertDict.keys()):
                vertDict[i] = 1
            if (G.degree(i) > 1):
                V.append(i)

    chosen = 0
    obj = getAllPairsFlow(G, k, vertDict)
    best_obj = obj
    best_V = vertDict
    iters = 0
    T = getInitTemp(G, k, vertDict)
    
    while (iters < maxIters):
        iters += 1
        T = alpha*T
        
        # Flip coin for which type of neighbor
        flip = np.random.uniform(0, 1, 1)

        # Generate random neighbor
        if (flip < 0.5) and (len(V) > 1):

            # Random pair to both flip - must be feasible
            vi,vj = sample(V, 2)
            if (chosen+2*vertDict[vi]+2*vertDict[vj]-2) <= m:
                    vertDict[vi] = 1-vertDict[vi]
                    vertDict[vj] = 1-vertDict[vj]

                    # Calculate objective function and acceptance prob
                    try_obj = getAllPairsFlow(G, k, vertDict)
                    acc_prob = getAcceptanceProb(obj, try_obj, T)
                    
                    # Flip coin whether to accept
                    if (np.random.uniform(0,1,1) < acc_prob):
                        obj = try_obj
                        chosen -= 2*vertDict[vi]+2*vertDict[vj]-2
                    else:
                        vertDict[vi] = 1-vertDict[vi]
                        vertDict[vj] = 1-vertDict[vj]
        else:
            # Random node to flip - must be feasible
            vi = sample(V, 1)[0]
            if (chosen+2*vertDict[vi]-1) <= m:
                vertDict[vi] = 1-vertDict[vi]

                # Calculate objective function and acceptance prob
                try_obj = getAllPairsFlow(G, k, vertDict)
                acc_prob = getAcceptanceProb(obj, try_obj, T)
                
                # Flip coin whether to accept
                if (np.random.uniform(0,1,1) < acc_prob):
                    obj = try_obj
                    chosen -= 2*vertDict[vi]-1
                else:
                    vertDict[vi] = 1-vertDict[vi]

        # Check whether to update best seen
        if (obj > best_obj):
            best_obj = obj
            best_V = vertDict

    
    # One iteration local search
    best_obj, best_V = localSearch(G, k, m, best_V, 1)

    return(best_obj, best_V)



# Runs simulated annealing on folder file
import os
import time
my_path = "/Users/alice/Dropbox/Network_Interdiction/Data/"
files = [f for f in os.listdir(my_path) if os.path.isfile(os.path.join(my_path,f))]
#files = ["DrugDataRem5Cap1Trial3-undir.dat"]
results = "filename, n, num_edges, time, obj, removed \n"
res_f = open("sim_results.csv", "w")
res_f.write(results)
res_f.close()
for f in files:

    if (f == ".DS_Store"):
        continue
    
    # Read graph
    print(f)
    G,k,m = gs.readGraph(os.path.join(my_path,f))
    
    results = f+","+str(len(G.nodes()))+"," + str(len(G.edges()))+","
    
    # Run simulated annealing
    start = time.time()
    obj, V = simulatedAnnealing(G,k,m,dict(),10000)
    end = time.time()

    # Number removed
    num_removed = 0
    for v in V:
        if V[v] == 0:
            num_removed += 1

    # Store results
    results += str(end-start)+","+str(obj)+","+str(num_removed)+ "\n"
    res_f = open("sim_results.csv", "a")
    res_f.write(results)
    res_f.close()


