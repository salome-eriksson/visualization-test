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

    def style_table_by_row(self, row):
        is_aggregate = (row['problem'] == "")
        retarray = (["background-color: #d1d1e0;"] if is_aggregate else [""])*len(row)
        if row[:1] < 0:
          retarray[:1] += "color: red"
        elif row[:1] > 0:
          retarray[:1] += "color: green"
        print(retarray)
        return retarray
        
    def compute_view_data(self):
        if not self.algorithm1 or not self.algorithm2:
            self.data_view = pd.DataFrame()
            return
        mapping = dict()
        for alg in [self.algorithm1, self.algorithm2]:
            mapping[str(alg)+"_"+str(self.attribute)] = str(alg)
        data = self.experiment_data.data
        self.view_data = data[[x for x in data.columns.values if x in mapping.keys()]]
        self.view_data = self.view_data.rename(columns=mapping)
        if self.precentual:
            self.view_data["diff"] = (self.view_data[self.algorithm2] / self.view_data[self.algorithm1])-1
        else:
            self.view_data["diff"] = self.view_data[self.algorithm2] - self.view_data[self.algorithm1]


    def set_experiment_data_dependent_parameters(self):
        super().set_experiment_data_dependent_parameters()
        self.param.algorithm1.objects = self.experiment_data.algorithms
        self.param.algorithm2.objects = self.experiment_data.algorithms
        self.algorithm1 = self.experiment_data.algorithms[0]
        self.algorithm2 = self.experiment_data.algorithms[1]
