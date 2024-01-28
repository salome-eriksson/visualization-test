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
    percentual = param.Boolean(False)
    
    
    def __init__(self, **params):
        print("DiffTablereport init")
        super().__init__(**params)
        self.param_view = pn.Param(self.param,  widgets= { "attributes": {"type": pn.widgets.CrossSelector, "definition_order" : False, "width" : 500}})
        
        self.param_view = pn.Column(
            pn.pane.HTML("Attributes", styles={'font-size': '10pt', 'font-family': 'Arial', 'padding-left': '10px'}),
            pn.widgets.CrossSelector.from_param(self.param.attributes, definition_order = False, width = 475, styles={'padding-left': '10px'}),
            pn.Param(self.param.algorithm1),
            pn.Param(self.param.algorithm2),
            pn.Param(self.param.custom_min_wins),
            pn.Param(self.param.custom_aggregators),
            pn.Param(self.param.percentual),
            pn.pane.Markdown("""
                ### Information
                Data is organized by attribute, then domain, then problem. 
                You can click on attributes/domains to unfold the next level, 
                and reclick to fold again.
                
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
        print("DiffTablereport param_view (end)")
        return self.param_view


    def get_param_config(self):
        param_config = super().get_param_config()
        alg1_string = "" if self.algorithm1 == "--" else str(self.experiment_data.algorithms.index(self.algorithm1))
        alg2_string = "" if self.algorithm2 == "--" else str(self.experiment_data.algorithms.index(self.algorithm2))
        percentual_string = "1" if self.percentual else "0"
        param_config += f";{alg1_string};{alg2_string};{percentual_string}"
        return param_config


    def get_params_from_string(self, config_string):
        print(f"DiffTablereport get_params_from_string {config_string}") 
        if len(config_string) != 6:
            return dict()
        ret = super().get_params_from_string(config_string[0:3])
        all_algorithms = self.experiment_data.algorithms
        if config_string[3] != "":
            ret["algorithm1"] = all_algorithms[int(config_string[3])]
        if config_string[4] != "":
            ret["algorithm2"] = all_algorithms[int(config_string[4])]
        ret["percentual"] = bool(int(config_string[5]))
        return ret
