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
        retarray = ["background-color: #d1d1e0;" if row['problem'] == "" else ""] * len(row)
        min_wins = False if self.attribute not in self.min_wins_by_attribute else self.min_wins_by_attribute[self.attribute]
        color = 'black'
        if (row[-1] > 0 and min_wins) or (row[-1] < 0 and not min_wins):
            color = 'red'
        elif (row[-1] < 0 and min_wins) or (row[-1] > 0 and not min_wins):
            color= 'green'
        retarray[-1] += f"color: {color}"
        return retarray
        
    def compute_view_data(self):
        algs = []
        if not self.algorithm1 or not self.algorithm2:
            self.view_data = pd.DataFrame()
            return False
        mapping = dict()
        for alg in [self.algorithm1, self.algorithm2]:
            name = str(alg)+"_"+str(self.attribute)
            mapping[name] = str(alg)
            algs.append(name)
        data = self.experiment_data.data
        self.view_data = data[algs]
        self.view_data = self.view_data.rename(columns=mapping)
        if self.precentual:
            self.view_data["diff"] = (self.view_data[self.algorithm2] / self.view_data[self.algorithm1])-1
        else:
            self.view_data["diff"] = self.view_data[self.algorithm2] - self.view_data[self.algorithm1]
        return True

    def set_experiment_data_dependent_parameters(self):
        super().set_experiment_data_dependent_parameters()
        self.param.algorithm1.objects = self.experiment_data.algorithms
        self.param.algorithm2.objects = self.experiment_data.algorithms
        self.algorithm1 = self.experiment_data.algorithms[0]
        self.algorithm2 = self.experiment_data.algorithms[1]
