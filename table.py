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


class Tablereport(Report):
    attribute = param.Selector()
    algorithms = param.ListSelector()
    active_domains = param.List(precedence=-1)
    view_data = None
    
    def __init__(self, **params):
        print("TableReport init")
        super().__init__(**params)
        
    
    def style_table_by_row(self, row):
        is_aggregate = (row['problem'] == "")
        numeric_values = pd.to_numeric(row,errors='coerce')
        min_val = numeric_values.dropna().min()
        max_val = numeric_values.dropna().max()
        min_equal_max = max_val - min_val == 0
        retarray = []
        for elem in numeric_values:
            formatting_string = ""
            if not min_equal_max != 0 and pd.notna(elem):
                val = ((elem - min_val) / (max_val-min_val)*255).astype(int)
                formatting_string = "color: #00{:02x}{:02x};".format(val,255-val)
            if is_aggregate:
                formatting_string += "background-color: #d1d1e0;"
            retarray.append(formatting_string)
        return retarray
        
    def filter_by_active_domains(self, df, active_domains):
        return df[df["domain"].isin(active_domains) | df["problem"].isin([""])]

    def on_click_callback(self, e):
        domain = self.view_data.iloc[e.row]["domain"]
        if self.view_data.iloc[e.row]["problem"] != "":
            return
        tmp = [x for x in self.active_domains]
        if domain in tmp:
            tmp.remove(domain)
        else:
            tmp.append(domain)
        self.active_domains = tmp



    def set_experiment_data_dependent_parameters(self):
        # ~ print("Scatterplot set experiment data dependent parameters")
        self.param.attribute.objects = self.experiment_data.attributes
        self.param.algorithms.objects = self.experiment_data.algorithms
        self.algorithms = self.experiment_data.algorithms

  
    def data_view(self):
        if not self.experiment_data.data.empty:
            mapping = dict()
            for alg in self.algorithms:
                mapping[str(alg)+"_"+str(self.attribute)] = str(alg)
            data = self.experiment_data.data
            selected_data = data[[x for x in data.columns.values if x in mapping.keys()]]
            selected_data = selected_data.rename(columns=mapping)
            
            #aggregate over domain
            temp_data = selected_data.groupby(level=0).agg('sum')
            temp_data['problem'] = ""
            temp_data = temp_data.set_index('problem',append=True)
            selected_data = pd.concat([selected_data,temp_data]).sort_index()
            self.view_data = selected_data.reset_index(['domain', 'problem'])
            
            view = pn.widgets.Tabulator(value=self.view_data, show_index=False, disabled = True, pagination=None)
            view.add_filter(pn.bind(self.filter_by_active_domains,active_domains=self.active_domains))
            view.style.apply(func=self.style_table_by_row, axis=1)
            view.on_click(self.on_click_callback)
            return view
        else:
            return pn.pane.Markdown("### Hello")

    def param_view(self):
        return pn.Param(self.param)
