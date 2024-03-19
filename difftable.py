#! /usr/bin/env python3

import math
import numpy as np
import param
import pandas as pd
import panel as pn

from table import Tablereport

class DiffTablereport(Tablereport):
    algorithm1 = param.Selector(default="--")
    algorithm2 = param.Selector(default="--")
    percentual = param.Boolean(default=False)
    
    
    def __init__(self, **params):
        super().__init__(**params)
        self.param_view = pn.Param(self.param,  widgets= { "attributes": {"type": pn.widgets.CrossSelector, "definition_order" : False, "width" : 500}})
        
        self.param_view = pn.Column(
            pn.pane.HTML("Attributes", styles={'font-size': '10pt', 'font-family': 'Arial', 'padding-left': '10px'}),
            pn.widgets.CrossSelector.from_param(self.param.attributes, definition_order = False, width = 475, styles={'padding-left': '10px'}),
            pn.pane.HTML("Domains", styles={'font-size': '10pt', 'font-family': 'Arial', 'padding-left': '10px'}),
            pn.widgets.CrossSelector.from_param(self.param.domains, definition_order = False, width = 475, styles={'padding-left': '10px'}),
            pn.Param(self.param.algorithm1),
            pn.Param(self.param.algorithm2),
            pn.Param(self.param.custom_min_wins),
            pn.Param(self.param.custom_aggregators),
            pn.Param(self.param.percentual),
            pn.pane.Markdown("""
                ### Information
                Data is organized by attribute, then domain, then problem. 
                You can click on attributes/domains to unfold the next level, 
                and reclick to fold again. Clicking on a concrete problem opens
                a ProblemReport comparing all attributes on all algorithms for
                this specific problem.
                
                Numeric values are aggregated over the set of instances where
                both algorithms have a value for the corresponding attribute.
                You can customize which aggregator to use with the dictionary 
                "custom aggregators", for example `{"expansions" : "gmean"}`.
                Currently supported aggregators are "sum", "mean" and "gmean".
                
                Numeric values are also color-coded, with blue denoting a worse 
                and green a better value. You can customize whether the smaller value 
                is better or not with the dictionary "custom min wins", for 
                example `{"expansions" : True}` means smaller is better.
                
                Percentual computes the Diff column with (Algorithm2/Algorithm1)-1 
                instead of Algorithm2-Algorithm1.
                """),
            width=500
        )


    def set_experiment_data_dependent_parameters(self):
        param_updates = super().set_experiment_data_dependent_parameters()
        self.param.algorithm1.objects = ["--", *self.experiment_data.algorithms]
        self.param.algorithm2.objects = ["--", *self.experiment_data.algorithms]
        param_updates["algorithm1"] = "--"
        param_updates["algorithm2"] = "--"
        return param_updates


    def compute_view_data(self):
        if self.algorithm1 == "--" or self.algorithm2 == "--" or self.algorithm1 == self.algorithm2:
            return pd.DataFrame()
            
        mapping = dict()
        retdata = self.table_data[["Index",self.algorithm1, self.algorithm2]].copy()
        col1_numeric = pd.to_numeric(self.table_data[self.algorithm1], errors="coerce")
        col2_numeric = pd.to_numeric(self.table_data[self.algorithm2], errors="coerce")
        if self.percentual:
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
        attribute = row.name[0]
        min_wins = self.custom_min_wins[attribute] if attribute in self.custom_min_wins else self.DEFAULT_MIN_WINS[attribute]
        
        if min_wins is None:
            return style
            
        color = 'black'
        if (row["Diff"] > 0 and min_wins) or (row["Diff"] < 0 and not min_wins):
            color = 'red'
        elif (row["Diff"] < 0 and min_wins) or (row["Diff"] > 0 and not min_wins):
            color= 'green'
        style[-1] += f"color: {color}"
        return style

        
    def param_view(self):
        return self.param_view


    def get_params_as_dict(self):      
        return super().get_params_as_dict()


    def set_params_from_dict(self, params):
        super().set_params_from_dict(params)
        self.param.update(params) #TODO: currently we need to make sure that the child calls this, maybe redesign...
