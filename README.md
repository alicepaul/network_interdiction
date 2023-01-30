# Network Interdiction
Code for the paper **The All-Pairs Vitality-Maximization (VIMAX) Problem**.

# Data

The **Data** folder contains the AMPL files for the random and grid networks used. The drug networks used are from the paper below and are not found in the folder. The **SimpData** folder contains the AMPL files for the simplified networks after running our graph simplification procedure.

M. Natarajan. Understanding the Structure of a Drug Trafficking Organization: A Conversational Analysis, pages 273–298. From Illegal Drug Markets: From Research to Prevention Policy. Criminal Justice Press/Willow Tree Press, United States, 2000.

# Code

The **python** folder contains the code used in our computational experiments.

  **graphSimplification.py** contains the code to read/write AMPL files from/to networkx graphs and also contains the code for our graph simplification algorithm.  
  **vimaxMIP.py** contains the code to run the MIP.  
  **simAnnealing.py** contains the code to run the simulated annealing algorithm.
  **randomGraphs.py** contains the code to generate a random graph. 

