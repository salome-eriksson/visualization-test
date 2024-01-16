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
        self.param_view = pn.Param(self.param,  widgets= {"algorithms": {"type": pn.widgets.CrossSelector, "definition_order" : False, "width" : 500},
                                                          "attributes": {"type": pn.widgets.CrossSelector, "definition_order" : False, "width" : 500}})
        print("AbsoluteTablereport init end")

    def set_experiment_data_dependent_parameters(self):
        print("AbsoluteTablereport set_experiment_data_dependent_parameters")
        param_updates = super().set_experiment_data_dependent_parameters()
        self.param.algorithms.objects = self.experiment_data.algorithms
        param_updates["algorithms"] = self.experiment_data.algorithms
        print("AbsoluteTablereport set_experiment_data_dependent_parameters end")
        return param_updates

    def compute_view_data(self):
        return self.table_data[["Index"] + self.algorithms]
        
    def get_current_columns(self):
        return self.algorithms
        
    def style_table_by_row(self, row):
        style = super().style_table_by_row(row)
        if row.name[0] not in self.MIN_WINS:
            return style
            
        min_wins = self.MIN_WINS[row.name[0]]
        numeric_values = pd.to_numeric(row,errors='coerce')
        min_val = numeric_values.dropna().min()
        max_val = numeric_values.dropna().max()
        if min_val == max_val:
            return style
        for i, val in enumerate(numeric_values):
            if not pd.isnull(val):
                y = ((val - min_val) / (max_val-min_val)*200).astype(int)
                if min_wins:
                  y = 200-y
                style[i] = style[i]+ "color: #00{:02x}{:02x};".format(y,200-y)
        return style

    def param_view(self):
        print("AbsoluteTablereport param_view (end)")
        return self.param_view
