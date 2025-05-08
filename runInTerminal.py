# import external libraries
from qiskit import qpy
import evaluation_functions as evf
import mcts_group_selection as mcts
from structure import Circuit
import itertools
import os
# import seaborn as sns
from tqdm import tqdm
import csv
# import functions, classes and objects

#reload kernal for changes in file
import importlib
importlib.reload(mcts)

num_runs = 10
params = {
    'collect_data': [True],
    'evaluation_function': [evf.h2, evf.lih, evf.h2o, evf.vqls_0, evf.vqls_1],
    # 'choices': [{'a': 20, 'd': 20, 's': 20, 'c': 20, 'p': 20}],
    # 'stop_deterministic': [False],


 # TEST BEST ONES

# Change from here
    'group_by_gates': [False],
    'group_by_action': [True],
    'terminal_nodes': [False],
    'group_by_change': [False],
    'group_by_swap': [False],
    'finite_progressive_widening': [True],

    'selection_method': ['test'],
    'n': [3],
}
name = 'test'

nqbits = {'h2': 4, 'lih': 10, 'h2o': 8,'vqls_1': 4,'vqls_0': 4}
budgets = {'h2': 5000, 'lih': 5000, 'h2o': 10000,'vqls_1': 10000,'vqls_0': 5000}
keys = list(params)
results_folder = 'results'

def test_all_vars_one_problem(max_depth, verbose=False):   
    count = 0 
    for values in tqdm(itertools.product(*map(params.get,keys))):
        count += 1
        print(values)
        for i in range(num_runs):
            evf = values[1]
            evf_name = evf.__name__
            print(evf_name, count)
            folder_name = f"{results_folder}/{name}/{evf_name}"
            os.makedirs(folder_name, exist_ok=True)  # Create the folder if it doesn't exist
            filename = f"{name}_{i}.csv"
            csv_path = os.path.join(folder_name, filename)
            if not os.path.isfile(csv_path):
                root = mcts.Node(Circuit(variable_qubits=nqbits[evf_name], ancilla_qubits=0), max_depth=max_depth)
                results = mcts.mcts(root, **dict(zip(keys,values)), budget=budgets[evf_name], verbose=verbose)
                objective_values = results['data'] 
                objective_values.to_csv(csv_path, index=False)

                qc_last = results['qc'][-1]
                qc_best = results['best_qc']
                data = [
                    ["Category", "EnergyBefore", "ValueBefore", "EnergyAfter", "ValueAfter", "H", "Cx", "Rx", "Ry", "Rz"]
                ]
                for id, circ in {"last": qc_last, "best": qc_best}.items():
                    arr = []
                    with open(f"{results_folder}/{name}/{evf_name}/{name}_{i}_{id}_circuit.qpy", "wb") as file:
                        qpy.dump(circ, file)
                    optim = [evf(quantum_circuit=circ)] if "vqls_0" in evf_name else evf(quantum_circuit=circ, gradient=True)
                    energy_before = optim[0]
                    value_before = -energy_before    
                    energy_after = optim[-1]
                    value_after = -energy_after    
                    gate_counts = dict(circ.count_ops())
                    h_gates = gate_counts["h"] if "h" in gate_counts.keys() else 0
                    cx_gates = gate_counts["rx"] if "rx" in gate_counts.keys() else 0
                    rx_gates = gate_counts["ry"] if "ry" in gate_counts.keys() else 0
                    ry_gates = gate_counts["rz"] if "rz" in gate_counts.keys() else 0
                    rz_gates = gate_counts["cx"] if "cx" in gate_counts.keys() else 0
                    arr = [id, energy_before, value_before, energy_after, value_after, h_gates, cx_gates, rx_gates, ry_gates, rz_gates]
                    data.append(arr)

                with open(f"{results_folder}/{name}/{evf_name}/{name}_{i}_optimized.csv", mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerows(data)
        
test_all_vars_one_problem(10, False)