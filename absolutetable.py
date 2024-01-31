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
        # ~ self.param_view = pn.Param(self.param,  widgets= {"algorithms": {"type": pn.widgets.CrossSelector, "definition_order" : False, "width" : 500},
                                                          # ~ "attributes": {"type": pn.widgets.CrossSelector, "definition_order" : False, "width" : 500}})
        self.param_view = pn.Column(
            pn.pane.HTML("Attributes", styles={'font-size': '10pt', 'font-family': 'Arial', 'padding-left': '10px'}),
            pn.widgets.CrossSelector.from_param(self.param.attributes, definition_order = False, width = 475, styles={'padding-left': '10px'}),
            pn.pane.HTML("Algorithms", styles={'font-size': '10pt', 'font-family': 'Arial', 'padding-left': '10px'}),
            pn.widgets.CrossSelector.from_param(self.param.algorithms, definition_order = False, width = 475, styles={'padding-left': '10px'}),
            pn.Param(self.param.custom_min_wins),
            pn.Param(self.param.custom_aggregators),
            pn.pane.Markdown("""
                ### Information
                Data is organized by attribute, then domain, then problem. 
                You can click on attributes/domains to unfold the next level, 
                and reclick to fold again.
                
                Numeric values are aggregated over the set of instances where
                all selected algorithms have a value for the corresponding attribute.
                You can customize which aggregator to use with the dictionary 
                "custom aggregators", for example `{"expansions" : "gmean"}`.
                Currently supported aggregators are "sum", "mean" and "gmean".
                
                Numeric values are also color-coded, with blue denoting a worse 
                and green a better value. You can customize whether the smaller value 
                is better or not with the dictionary "custom min wins", for 
                example `{"expansions" : True}` means smaller is better.
                """),
            width=500
        )
        print("AbsoluteTablereport init end")


    def set_experiment_data_dependent_parameters(self):
        print("AbsoluteTablereport set_experiment_data_dependent_parameters")
        param_updates = super().set_experiment_data_dependent_parameters()
        self.param.algorithms.objects = self.experiment_data.algorithms
        self.param.algorithms.default = self.experiment_data.algorithms
        param_updates["algorithms"] = self.experiment_data.algorithms
        print("AbsoluteTablereport set_experiment_data_dependent_parameters end")
        return param_updates


    def compute_view_data(self):
        return self.table_data[["Index"] + self.algorithms]


    def get_current_columns(self):
        return self.algorithms


    def style_table_by_row(self, row):
        style = super().style_table_by_row(row)
        attribute = row.name[0]
        min_wins = self.custom_min_wins[attribute] if attribute in self.custom_min_wins else self.DEFAULT_MIN_WINS[attribute]

        if min_wins is None:
            return style

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


    def get_params_as_dict(self):      
        params = super().get_params_as_dict()
        
        # shorten the algorithms parameter by using indices instead of the attribute names
        if "algorithms" in params:
            params["algorithms"] = [self.param.algorithms.objects.index(a) for a in params["algorithms"]]
        return params


    def set_params_from_dict(self, params):
        super().set_params_from_dict(params)
        if "algorithms" in params:
            params["algorithms"] = [self.param.algorithms.objects[x] for x in params["algorithms"]]
        self.param.update(params) #TODO: currently we need to make sure that the child calls this, maybe redesign...
