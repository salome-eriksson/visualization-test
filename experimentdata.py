import json
import numpy as np
import pandas as pd


class ExperimentData():
    def compute_ipc_score(self):
        print("computing ipc score")
        upper_bounds = pd.read_json("upper_bounds.json", orient="index")
        upper_bounds = upper_bounds.set_index(["domain","problem"])
        
        costs = self.data[[f"{alg}_cost" for alg in self.algorithms]]
        costs_and_ub = pd.concat([costs,upper_bounds], axis=1).reindex(costs.index)
        min_costs = costs_and_ub.min(axis=1)
        min_costs_without_ub = costs.min(axis=1)
        
        for algorithm in self.algorithms:
            self.data[f"{algorithm}_ipc-sat-score"] = (min_costs/self.data[f"{algorithm}_cost"]).fillna(0)
            self.data[f"{algorithm}_ipc-sat-score-no-planning-domains"] = (min_costs_without_ub/self.data[f"{algorithm}_cost"]).fillna(0)
        self.attributes = sorted(self.attributes + ["ipc-sat-score", "ipc-sat-score-no-planning-domains"])
        self.numeric_attributes = sorted(self.numeric_attributes + ["ipc-sat-score", "ipc-sat-score-no-planning-domains"])
  
    def __init__(self, properties_file=""):
        # ~ print(f"Experiment data init with properties file '{properties_file}'")
        self.algorithms = []
        self.domains = []
        self.problems = dict()
        self.attributes = []
        self.numeric_attributes = [""]
        self.data = pd.DataFrame()
        try:
            self.data = pd.read_json(properties_file, orient="index")
            self.data = self.data.set_index(["algorithm","domain","problem"])

            self.algorithms = sorted(list(set(self.data.index.get_level_values(0))))
            self.domains = sorted(list(set(self.data.index.get_level_values(1))))
            self.attributes = sorted(self.data.columns.values.tolist())
            self.numeric_attributes = [x for x in self.attributes if pd.api.types.is_numeric_dtype(self.data.dtypes[x])]
            if len(self.numeric_attributes) == 0:
                self.numeric_attributes = [""]
            
            self.data = self.data.unstack(level=-3)
            self.data.columns = self.data.columns.get_level_values(1) + "_" + self.data.columns.get_level_values(0)
            
            for domain in self.domains:
                self.problems[domain] = [x for x in self.data.loc[domain].index.get_level_values('problem')]
            
            self.compute_ipc_score()
            print(f"Successfully loaded file '{properties_file}'")
        except Exception as ex:
            print(ex)
            print(f"Could not open file '{properties_file}'")

        # ~ print(f"Experiment data init with properties file '{properties_file}' end")
