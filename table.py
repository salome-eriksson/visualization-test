#! /usr/bin/env python3

import math
import numpy as np
import param
import pandas as pd
#import holoviews as hv
#import hvplot.pandas
import panel as pn

from report import Report
from experimentdata import ExperimentData

class Tablereport(Report):
    attribute = param.Selector()
    aggregator = param.Selector(["sum", "mean", "min", "max"])
    height = param.Integer(1000)
    width = param.Integer(1500)
    
    def __init__(self, **params):
        print("TableReport init")
        super().__init__(**params)

    def set_experiment_data_dependent_parameters(self):
        # ~ print("Scatterplot set experiment data dependent parameters")
        self.param.attribute.objects = self.experiment_data.attributes

    #@param.depends('algorithm_selector', 'algorithm_selector.algorithm_pairs')
    def data_view(self):
        if not self.experiment_data.data.empty:
            mapping = dict()
            for alg in self.experiment_data.algorithms:
                mapping[str(alg)+"_"+str(self.attribute)] = str(alg)
            data = self.experiment_data.data
            selected_data = data[[x for x in data.columns.values if x in mapping.keys()]]
            selected_data = selected_data.rename(columns=mapping)
            return pn.widgets.DataFrame(value=selected_data, hierarchical=True, aggregators={'problem': self.aggregator},
                                        width=self.width, height=self.height)

        
    #@param.depends('algorithm_selector')
    def param_view(self):
        retcol = pn.Column(pn.Param(self.param))
        return retcol
