#! /usr/bin/env python3

import math
import numpy as np
import param
import pandas as pd
import panel as pn

from table import Tablereport

class AbsoluteTablereport(Tablereport):
    algorithms = param.ListSelector()
    
    
    def __init__(self, **params):
        print("AbsoluteTablereport init")
        super().__init__(**params)

    def style_table_by_row(self, row):
        is_aggregate = (row['problem'] == "")
        numeric_values = pd.to_numeric(row,errors='coerce')
        min_val = numeric_values.dropna().min()
        max_val = numeric_values.dropna().max()
        min_equal_max = max_val - min_val == 0
        retarray = []
        for elem in numeric_values:
            formatting_string = ""
            if not min_equal_max != 0 and pd.notna(elem):
                val = ((elem - min_val) / (max_val-min_val)*200).astype(int)
                formatting_string = "color: #00{:02x}{:02x};".format(val,200-val)
            if is_aggregate:
                formatting_string += "background-color: #d1d1e0;"
            retarray.append(formatting_string)
        return retarray
        
    def compute_view_data(self):
        mapping = dict()
        for alg in self.algorithms:
            mapping[str(alg)+"_"+str(self.attribute)] = str(alg)
        data = self.experiment_data.data
        self.view_data = data[[x for x in data.columns.values if x in mapping.keys()]]
        self.view_data = self.view_data.rename(columns=mapping)


    def set_experiment_data_dependent_parameters(self):
        super().set_experiment_data_dependent_parameters()
        self.param.algorithms.objects = self.experiment_data.algorithms
        self.algorithms = self.experiment_data.algorithms
