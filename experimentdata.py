import json
import numpy as np
import pandas as pd

class ExperimentData():
    def __init__(self, properties_file=""):
        # ~ print(f"Experiment data init with properties file '{properties_file}'")
        self.algorithms = []
        self.domains = []
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
            print(f"Successfully loaded file '{properties_file}'")
        except:
            print(f"Could not open file '{properties_file}'")

        # ~ print(f"Experiment data init with properties file '{properties_file}' end")
