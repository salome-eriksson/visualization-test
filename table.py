#! /usr/bin/env python3

import math
import numpy as np
import param
import pandas as pd
import panel as pn
from scipy.stats import gmean

from report import Report
from experimentdata import ExperimentData

pn.extension('tabulator')


class Tablereport(Report):
    attribute = param.Selector()
    active_domains = param.List(precedence=-1)
    #TODO: fix gmean
    aggregator = param.Selector(["sum", "mean"])
    view_data = pd.DataFrame()
    
    def __init__(self, **params):
        super().__init__(**params)
        
    def style_table_by_row(self, row):
        pass
    
    def compute_view_data(self):
        pass

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
        
    def aggregate_over_domain(self):
        aggregated_data = self.view_data.groupby(level=0).agg(self.aggregator)
        aggregated_data['problem'] = ""
        aggregated_data = aggregated_data.set_index('problem',append=True)
        self.view_data = pd.concat([aggregated_data,self.view_data]).sort_index().reset_index(['domain', 'problem'])


    def set_experiment_data_dependent_parameters(self):
        self.param.attribute.objects = self.experiment_data.numeric_attributes
        self.attribute = self.experiment_data.numeric_attributes[0]
  
    def data_view(self):
        if not self.experiment_data.data.empty:
            self.compute_view_data()
            if self.view_data.empty:
                return
            self.aggregate_over_domain()
            
            view = pn.widgets.Tabulator(value=self.view_data, show_index=False, disabled = True, pagination=None)
            view.add_filter(pn.bind(self.filter_by_active_domains,active_domains=self.active_domains))
            view.style.apply(func=self.style_table_by_row, axis=1)
            view.on_click(self.on_click_callback)
            return view
        else:
            return pn.pane.Markdown("### Hello")

    def param_view(self):
        return pn.Param(self.param)
