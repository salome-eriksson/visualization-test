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
        self.param_view = pn.Param(self.param,  widgets= {"algorithms": {"type": pn.widgets.CrossSelector, "definition_order" : False}})
        print("AbsoluteTablereport init end")

    def style_table_by_row(self, row):
        is_aggregate = (row['problem'] == "")
        numeric_values = pd.to_numeric(row,errors='coerce')[2:]
        min_val = numeric_values.dropna().min()
        max_val = numeric_values.dropna().max()
        min_equal_max = max_val - min_val == 0
        min_wins = False if self.attribute not in self.min_wins_by_attribute else self.min_wins_by_attribute[self.attribute]
        retarray = ["",""]
        if is_aggregate:
            retarray = ["background-color: #d1d1e0;", "background-color: #d1d1e0;"]
        for elem in numeric_values:
            formatting_string = ""
            if not min_equal_max != 0 and pd.notna(elem):
                val = ((elem - min_val) / (max_val-min_val)*200).astype(int)
                formatting_string = "color: #00{:02x}{:02x};".format(200-val if min_wins else val,val if min_wins else 200-val)
            if is_aggregate:
                formatting_string += "background-color: #d1d1e0;"
            retarray.append(formatting_string)
        return retarray
        
    def compute_view_data(self):
        if not self.algorithms:
            self.view_data = pd.DataFrame()
            return False
        mapping = dict()
        columns = []
        for alg in self.algorithms:
            columns.append(str(alg)+"_"+str(self.attribute))
            mapping[str(alg)+"_"+str(self.attribute)] = str(alg)
        data = self.experiment_data.data
        self.view_data = data[columns]
        self.view_data = self.view_data.rename(columns=mapping)
        return True


    def set_experiment_data_dependent_parameters(self):
        print("AbsoluteTablereport set_experiment_data_dependent_parameters")
        super().set_experiment_data_dependent_parameters()
        self.param.algorithms.objects = self.experiment_data.algorithms
        self.algorithms = self.experiment_data.algorithms
        print("AbsoluteTablereport set_experiment_data_dependent_parameters end")

    def param_view(self):
        print("AbsoluteTablereport param_view (end)")
        return self.param_view
