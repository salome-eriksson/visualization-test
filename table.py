#! /usr/bin/env python3

import math
import numpy as np
import param
import pandas as pd
import panel as pn
from scipy import stats

from report import Report
from experimentdata import ExperimentData
from problemtable import ProblemTablereport

pn.extension('tabulator')
pn.extension('floatpanel')

class Tablereport(Report):
    attribute = param.Selector()
    active_domains = param.List(precedence=-1)
    aggregate_only_over_common = param.Boolean(True)
    ignore_axiom_domains = param.Boolean(True)
    #TODO: fix gmean
    aggregator = param.Selector(["sum", "mean", stats.gmean])
    view_data = pd.DataFrame()

    min_wins_by_attribute = {
      "coverage": False,
      "cost" : True,
      "dead_ends" : False,
      "evaluations" : True,
      "expansions" : True,
      "expansions_until_last_jump" : True,
      "generated" : True,
      "initial_h_value" : True,
      "memory": True,
      "plan_length" : True,
      "planner_time": True,
      "score_evaluations": False,
      "score_expansions" : False,
      "score_generated" : False,
      "score_memory" : False,
      "score_search_time" : False,
      "score_total_time" : False,
      "search_time": True,
      "steps": True,
      "total_time": True
    }
    axiom_domains = [
      "assembly",
      "miconic-fulladl",
      "openstacks",
      "openstacks-sat08-adl",
      "optical-telegraphs",
      "philosophers",
      "psr-large",
      "psr-middle",
      "trucks"
    ]
    
    def __init__(self, **params):
        super().__init__(**params)
        self.placeholder = pn.Column(height=0, width=0)
        
    def style_table_by_row(self, row):
        pass
    
    def compute_view_data(self):
        pass

    def filter_by_active_domains(self, df, active_domains):
        return df[df["domain"].isin(active_domains) | df["problem"].isin([""])]

    def on_click_callback(self, e):
        domain = self.view_data.iloc[e.row]["domain"]
        problem = self.view_data.iloc[e.row]["problem"]
        if domain not in self.experiment_data.domains:
            return
            
        if problem != "":
            probreport = ProblemTablereport(experiment_data = self.experiment_data, domain = domain, problem = problem)
            floatpanel = pn.layout.FloatPanel(probreport.data_view, name=f"{domain} - {problem}", contained=False, position='left-top', height=500)
            self.placeholder[:] = [floatpanel]
            return
                        
        tmp = [x for x in self.active_domains]
        if domain in tmp:
            tmp.remove(domain)
        else:
            tmp.append(domain)
        self.active_domains = tmp
        
    def aggregate_over_domain(self):
        temp_data = self.view_data
        if (self.aggregate_only_over_common):
            temp_data = temp_data.dropna()
        if (self.aggregator == stats.gmean):
            temp_data = temp_data.replace(0,0.00000000000000000001)
        overall = temp_data.agg(self.aggregator)
        aggregated_data = temp_data.groupby(level=0).agg(self.aggregator)
        aggregated_data.loc[len(aggregated_data)] = overall
        aggregated_data['problem'] = ""
        aggregated_data = aggregated_data.set_index('problem',append=True)
        self.view_data = pd.concat([aggregated_data,self.view_data]).sort_index().reset_index(['domain', 'problem'])


    def set_experiment_data_dependent_parameters(self):
        self.param.attribute.objects = self.experiment_data.numeric_attributes
        self.attribute = self.experiment_data.numeric_attributes[0]
  
    def data_view(self):
        if self.experiment_data.data.empty or not self.compute_view_data():
            return pn.pane.Markdown("### Hello")

        if self.ignore_axiom_domains:
            for dom in set(self.axiom_domains) & set(self.experiment_data.domains):
                self.view_data.drop(dom, level=0, inplace=True)
        
        self.aggregate_over_domain()
            
        view = pn.widgets.Tabulator(value=self.view_data, show_index=False, disabled = True, pagination=None)
        view.add_filter(pn.bind(self.filter_by_active_domains,active_domains=self.active_domains))
        view.style.apply(func=self.style_table_by_row, axis=1)
        view.on_click(self.on_click_callback)
        return view

    def param_view(self):
        return pn.Column(pn.Param(self.param), self.placeholder)
