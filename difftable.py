#! /usr/bin/env python3

import math
import numpy as np
import param
import pandas as pd
import panel as pn

from table import Tablereport

class DiffTablereport(Tablereport):
    algorithm1 = param.Selector()
    algorithm2 = param.Selector()
    precentual = param.Boolean(False)
    
    
    def __init__(self, **params):
        print("DiffTablereport init")
        super().__init__(**params)
        self.param_view = pn.Param(self.param,  widgets= { "attributes": {"type": pn.widgets.CrossSelector, "definition_order" : False, "width" : 500}})
        print("DiffTablereport init end")
        
    
    def set_experiment_data_dependent_parameters(self):
        print("DiffTablereport set_experiment_data_dependent_parameters")
        param_updates = super().set_experiment_data_dependent_parameters()
        self.param.algorithm1.objects = ["--", *self.experiment_data.algorithms]
        self.param.algorithm2.objects = ["--", *self.experiment_data.algorithms]
        param_updates["algorithm1"] = "--"
        param_updates["algorithm2"] = "--"
        print("DiffTablereport set_experiment_data_dependent_parameters end")
        return param_updates


    def compute_view_data(self):
        if self.algorithm1 == "--" or self.algorithm2 == "--":
            return pd.DataFrame()
            
        mapping = dict()
        retdata = self.table_data[["Index",self.algorithm1, self.algorithm2]].copy()
        col1_numeric = pd.to_numeric(self.table_data[self.algorithm1], errors="coerce")
        col2_numeric = pd.to_numeric(self.table_data[self.algorithm2], errors="coerce")
        if self.precentual:
            retdata["Diff"] = (col2_numeric / col1_numeric)-1
        else:
            retdata["Diff"] = col2_numeric - col1_numeric
        return retdata       

    def get_current_columns(self):
        if self.algorithm1 != "--" and self.algorithm2 != "--":
            return [self.algorithm1, self.algorithm2]
        else:
            return []

    def style_table_by_row(self, row):
        style = super().style_table_by_row(row)
        if row.name[0] not in self.MIN_WINS:
            return style
            
        min_wins = self.MIN_WINS[row.name[0]]
        color = 'black'
        if (row["Diff"] > 0 and min_wins) or (row["Diff"] < 0 and not min_wins):
            color = 'red'
        elif (row["Diff"] < 0 and min_wins) or (row["Diff"] > 0 and not min_wins):
            color= 'green'
        style[-1] += f"color: {color}"
        return style

        
    def param_view(self):
        print("DiffTablereport param_view (end)")
        return self.param_view
        

