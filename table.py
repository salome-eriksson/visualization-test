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

pn.extension('tabulator')

def highlight_max(s):
    print(s)
    print(s.max())
    val = (((s-s.min())/ (s.max()-s.min()))*255).fillna(0).astype(int)
    return ['color: #00{:02x}{:02x}'.format(v,255-v) if s.max() != s.min() else '' for v in val]

class Tablereport(Report):
    attribute = param.Selector()
    aggregator = param.Selector(["sum", "mean", "min", "max"])
    height = param.Integer(1000)
    width = param.Integer(1500)
    algorithms = param.ListSelector()
    
    def __init__(self, **params):
        print("TableReport init")
        super().__init__(**params)

    def set_experiment_data_dependent_parameters(self):
        # ~ print("Scatterplot set experiment data dependent parameters")
        self.param.attribute.objects = self.experiment_data.attributes        
        self.param.algorithms.objects = self.experiment_data.algorithms

    #@param.depends('algorithm_selector', 'algorithm_selector.algorithm_pairs')
    def data_view(self):
        if not self.experiment_data.data.empty:
            mapping = dict()
            for alg in self.algorithms:
                mapping[str(alg)+"_"+str(self.attribute)] = str(alg)
            data = self.experiment_data.data
            selected_data = data[[x for x in data.columns.values if x in mapping.keys()]]
            selected_data = selected_data.rename(columns=mapping)
            return pn.widgets.DataFrame(value=selected_data, hierarchical=True, aggregators={'problem': self.aggregator},
                                          width=self.width, height=self.height).style.apply(highlight_max, axis=1)
        else:
            return pn.pane.Markdown("### Hello")

        
    #@param.depends('algorithm_selector')
    def param_view(self):
        return pn.Param(self.param)
