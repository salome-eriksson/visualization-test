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
    
    def __init__(self, **params):
        print("TableReport init")
        super().__init__(**params)

    def set_experiment_data_dependent_parameters(self):
        # ~ print("Scatterplot set experiment data dependent parameters")
        self.param.attribute.objects = self.experiment_data.attributes

    #@param.depends('algorithm_selector', 'algorithm_selector.algorithm_pairs')
    def data_view(self):
        pn.widgets.DataFrame(value=self.experiment_data.data, hierarchical=True, height=400).show()
        
    #@param.depends('algorithm_selector')
    def param_view(self):
        retcol = pn.Column(pn.Param(self.param))
        return retcol
