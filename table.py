#! /usr/bin/env python3

from copy import deepcopy
import math
import numpy as np
import param
import pandas as pd
from collections import defaultdict
import panel as pn
from scipy import stats

from report import Report
from experimentdata import ExperimentData
from problemtable import ProblemTablereport

# TODO: is replacing 0 with something like 0.0001 a valid approach for gmean?
# TODO: fix warnings for gmean

class Tablereport(Report):    
    DEFAULT_MIN_WINS = defaultdict(lambda:None,{
        "cost" : True,
        "coverage": False,
        "dead_ends": False,
        "evaluated": True,
        "evaluations": True,
        "evaluations_until_last_jump": True,
        "expansions": True,
        "expansions_until_last_jump": True,
        "generated": True,
        "generated_until_last_jump": True,
        "initial_h_value": False,
        "ipc-sat-score": False,
        "ipc-sat-score-no-planning-domains": False,
        "memory": True,
        "plan_length": False,
        "planner_memory": True,
        "planner_time": True,
        "planner_wall_clock_time": True,
        "raw_memory": True,
        "score_evaluations": False,
        "score_expansions": False,
        "score_generated": False,
        "score_memory": False,
        "score_search_time": False,
        "score_total_time": False,
        "search_time": True,
        "total_time": True,
        "translator_time_done": True
    })
    
    DEFAULT_AGGREGATORS = defaultdict(lambda:"sum",{
        "cost" : "sum",
        "coverage": "sum",
        "evaulated": "gmean",
        "evaluations": "gmean",
        "evaluations_until_last_jump": "gmean",
        "expansions": "gmean",
        "expansions_until_last_jump": "gmean",
        "generated": "gmean",
        "generated_until_last_jump": "gmean",
        # TODO: do we need finite sum?
        "initial_h_value": "sum",
        "ipc-sat-score": "sum",
        "ipc-sat-score-no-planning-domains": "sum",
        "memory": "sum",
        "planner_memory": "sum",
        "planner_time": "gmean",
        "planner_wall_clock_time": "gmean",
        "raw_memory": "sum",
        "score_evaluations": "sum",
        "score_expansions": "sum",
        "score_generated": "sum",
        "score_memory": "sum",
        "score_search_time": "sum",
        "score_total_time": "sum",
        "search_time": "gmean",
        "total_time": "gmean",
        "translator_time_done": "gmean"
    })

    attributes = param.ListSelector()
    custom_min_wins = param.Dict(precedence=10)
    custom_aggregators = param.Dict(precedence=10)
    
    
    def __init__(self, **params):
        print("TableReport init")
        self.placeholder = pn.Column(height=0, width=0) # used for the popup ProblemTableReport
        self.dummy = pn.widgets.Checkbox() # used for triggering the filter function
        self.unfolded = dict() # which attributes/domains for each attribute are unfolded in the table
        self.computed = dict() # per attribute: used aggregator, are domain aggregatos up to date
        self.exp_data_dropna = pd.DataFrame() # same as self.experiment_data.data.dropna()
        self.table_data = pd.DataFrame() # experiment data with aggregates, should be used as base data
        self.view_data = pd.DataFrame()

        # TODO: fix with proper initialization order such that we don't have invalid between param combinations
        super().__init__(**params)

        # TODO: currently added to absolutetable.py, figure out how to add it here and use in subclasses.
        # ~ self.param_view = pn.Param(self.param,  widgets= {"attributes": {"type": pn.widgets.CrossSelector, "definition_order" : False, "width" : 500}})

        # ajaxLoader false is set to reduce blinking (https://github.com/olifolkerd/tabulator/issues/1027)
        # TODO: reenable sorting (fix custom sorting functions that can handle NaN)
        self.view = pn.widgets.Tabulator(value=self.view_data, disabled = True, show_index = False, 
                                    pagination="remote", page_size=10000, frozen_columns=['Index'], 
                                    sizing_mode='stretch_both', configuration={"ajaxLoader":"False"}, sortable=False)
        self.view.add_filter(pn.bind(self.filter, dummy=self.dummy))
        self.view.style.apply(func=self.style_table_by_row, axis=1)
        self.view.on_click(self.on_click_callback)
        self.full_view = pn.Column(self.view, self.placeholder)
        print("TableReport init end")


    def set_experiment_data_dependent_parameters(self):
        print("Tablereport set_experiment_data_dependent_parameters")
        param_updates = super().set_experiment_data_dependent_parameters()
        
        # Reset fields.
        self.exp_data_dropna = self.experiment_data.data.dropna()
        self.table_data = pd.DataFrame()
        self.view_data = pd.DataFrame()
        self.unfolded = dict()
        self.computed = { attribute : {"aggregator": None, "domains_outdated" : True} for attribute in self.experiment_data.numeric_attributes }
        self.computed["__columns"] = self.experiment_data.algorithms
        self.param.attributes.objects = self.experiment_data.attributes
        param_updates["attributes"] =  self.experiment_data.attributes
        param_updates["custom_min_wins"] = dict()
        param_updates["custom_aggregators"] = dict()
        
        # Build the rows for the aggregated values such that we later just overwrite values rather than concatenate.
        mi = pd.MultiIndex.from_product([self.experiment_data.attributes, ["--", *self.experiment_data.domains], ["--"]],
                                        names = ["attribute", "domain", "problem"])
        aggregated_data_skeleton = pd.DataFrame(data = "", index = mi, columns = self.experiment_data.algorithms)
        # Combine experiment data and aggregated data skeleton.
        self.table_data = pd.concat([self.experiment_data.data, aggregated_data_skeleton]).sort_index()

        # Add Index column (solely used in the visualization).
        pseudoindex = [x[0] if x[1]=="--" else (x[1] if x[2] == "--" else x[2]) for x in self.table_data.index]
        self.table_data.insert(0, "Index", pseudoindex)
        
        print("Tablereport set_experiment_data_dependent_parameters end")
        return param_updates


    def compute_view_data(self):
        return self.table_data
    
    def get_current_columns(self):
        return self.experiment_data.algorithms


    def style_table_by_row(self, row):
        # Give aggregates a different background color, and indent Index col text if it's a domain or problem.
        style = [""] * len(row)
        if row.name[1] == "--":
            style = [x + "background-color: #b1b1b1;" for x in style]
        elif row.name[2] == "--":
            style = [x + "background-color: #d1d1d1;" for x in style]
            style[0] = style[0] + "text-indent:25px;"
        else:
            style[0] = "text-indent:50px;"
        return style


    def filter(self, df, dummy):
        print("filter")
        if df.empty:
            return df
        
        indices = [(a,"--","--") for a in self.attributes]
        for a, doms in self.unfolded.items():
            if a not in self.attributes:
                continue
            indices += [(a,d,"--") for d in self.experiment_data.domains]
            for d in doms:
                indices += [(a,d,p) for p in self.experiment_data.problems[d]]
        indices.sort()
        print("filter end")
        return df.loc[indices]


    def on_click_callback(self, e):
        print("on click callback")
        row = self.view_data.iloc[e.row]
        attribute, domain, problem = row.name[0:3]
        
        # clicked on concrete problem -> open problem wise report
        if problem != "--":
            probreport = ProblemTablereport(
                experiment_data = self.experiment_data, sizing_mode = "fixed",
                domain = domain, problem = problem)
            floatpanel = pn.layout.FloatPanel(
                probreport.data_view, name=f"{domain} - {problem}", contained=False, 
                height=500, width=500, config = {"setStatus" : "maximized", "closeOnEscape" : True})
            self.placeholder.append(floatpanel)
            print("on click problemreport end")
            return

        # clicked on domain aggregate -> (un)fold that domain for that attribute
        if domain != "--":
            if domain in self.unfolded[attribute]:
                self.unfolded[attribute].remove(domain)
            else:
                self.unfolded[attribute].append(domain)
                
        # clicked on attribute aggregate -> (un)fold that attribute
        else:
            if attribute in self.unfolded:
                self.unfolded.pop(attribute)
            else:
                self.unfolded[attribute] = []
                if attribute in self.experiment_data.numeric_attributes:
                    self.aggregate_domains_for_attribute(attribute)
                    self.view.value = self.compute_view_data()
                    self.view.selection = []
                    self.view.selection = [e.row]
                    print("on click attribute unfold end")
                    return
        
        # Changing the value of dummy forces the filter to be reapplied.
        # Setting the selection tells the tabulator to display that row. This
        # order of assignments leads to the least blinking/jumping.
        self.view.selection = []
        self.dummy.value = not self.dummy.value
        self.view.selection = [e.row]
        print("on click end")


    def aggregate_where_necessary(self):
        current_columns = self.get_current_columns()
        columns_outdated = current_columns != self.computed["__columns"]
        
        # If the columns used for aggreagtion are outdated, recompute dropna to only consider current columns.
        if columns_outdated:
            unique_columns = list(dict.fromkeys(current_columns))
            if not unique_columns:
                return
            self.exp_data_dropna = self.experiment_data.data[unique_columns].dropna()
            self.computed["__columns"] = current_columns
      
        cols_without_index = self.table_data.columns[1:]
        for attribute in self.experiment_data.numeric_attributes:
            aggregator = self.custom_aggregators[attribute] if attribute in self.custom_aggregators else self.DEFAULT_AGGREGATORS[attribute]
            if not columns_outdated and aggregator == self.computed[attribute]["aggregator"]:
                continue

            self.table_data.loc[(attribute, "--", "--"),"Index"] = f"{attribute} ({aggregator})"
            
            # Compute the overall aggregate.
            new_vals = None
            attribute_data = None
            if attribute not in self.exp_data_dropna.index:
                new_aggregates = np.NaN
            else:
                attribute_data = self.exp_data_dropna.loc[attribute].apply(pd.to_numeric, errors='coerce')
                # Since gmean is not a built-in function we need to set the variable to the actual function here.
                if aggregator == "gmean":
                    aggregator = stats.gmean
                    attribute_data = attribute_data.replace(0,0.000001)
                new_aggregates = attribute_data.agg(aggregator)
            self.table_data.loc[(attribute, "--", "--"),cols_without_index] = new_aggregates
            
            
            self.computed[attribute]["domains_outdated"] = True
            if attribute in self.unfolded:
                self.aggregate_domains_for_attribute(attribute, attribute_data)

    
    def aggregate_domains_for_attribute(self, attribute, attribute_data = None):
        print(f"aggregating {attribute}")

        # Represents the slice of all domain aggregate rows, but without the Index column.
        rows, cols = (attribute, slice(self.experiment_data.domains[0], self.experiment_data.domains[-1]), "--"), self.table_data.columns[1:]
        # This can happen if there are no problems where all columns have a value for the attribute.
        if attribute not in self.exp_data_dropna.index:
            self.table_data.loc[rows,cols] = np.NaN
            return

        if attribute_data is None:
            attribute_data = self.exp_data_dropna.loc[attribute].apply(pd.to_numeric, errors='coerce')
        aggregator = self.custom_aggregators[attribute] if attribute in self.custom_aggregators else self.DEFAULT_AGGREGATORS[attribute]
        # Since gmean is not a built-in function we need to set the variable to the actual function here.
        if aggregator == "gmean":
                aggregator = stats.gmean
                attribute_data.replace(0,0.000001, inplace=True)

        # Clear the slice and apply combine_first (this way, the newly aggregated data is taken wherever it exists).
        self.table_data.loc[rows,cols] = np.NaN
        self.table_data.loc[rows,cols] = self.table_data.loc[rows,cols].combine_first(attribute_data.groupby(level=0).agg(aggregator))
        
        self.computed[attribute]["domains_outdated"] = False


    def data_view(self):
        print("TableReport data_view")
        
        self.aggregate_where_necessary()
        self.view_data = self.compute_view_data()
        self.view.value = self.view_data
        print("TableReport data_view end")        
        return self.full_view


    def param_view(self):
        print("TableReport param_view (end)")
        return self.param_view


    def deactivate(self):
        print("TableReport on defocus")
        self.placeholder.clear()
        print("TableReport on defocus end")


    def get_param_config(self):
        all_attributes = self.param.attributes.objects
        attributes_string = "default"
        if self.attributes != all_attributes:
            attribute_indices = [str(all_attributes.index(attr)) for attr in self.attributes]
            attributes_string = ",".join(attribute_indices)
        
        min_wins_string_parts = []
        for key, value in self.custom_min_wins.items():
            key_string = key
            if key in all_attributes:
                key_string = str(all_attributes.index(key))
            value_string = "1" if value else "0"
            min_wins_string_parts.append(f"{key_string}:{value_string}")
        min_wins_string = ",".join(min_wins_string_parts)
        
        aggregators_string_parts = []
        aggregators_vals = {"sum" : "s", "mean" : "m", "gmean" : "g"}
        for key, value in self.custom_aggregators.items():
            key_string = key
            if key in all_attributes:
                key_string = str(all_attributes.index(key))
            value_string = aggregators_vals[value] if value in aggregators_vals.keys() else value
            aggregators_string_parts.append(f"{key_string}:{value_string}")
        aggregators_string = ",".join(aggregators_string_parts)
        
        return f"{attributes_string};{min_wins_string};{aggregators_string}"


    def get_params_from_string(self, config_string):
        ret = dict()
        all_attributes = self.experiment_data.attributes
        if len(config_string) != 3:
            return ret

        if config_string[0] != "default":
            attributes_parts = config_string[0].split(",")
            ret["attributes"] = [all_attributes[int(x)] for x in attributes_parts]
            
        if config_string[1] != "":
            min_wins = dict()
            for part in config_string[1].split(","):
                p = part.split(":")
                min_wins[all_attributes[int(p[0])]] = bool(int(p[1]))
            ret["custom_min_wins"] = min_wins

        if config_string[2] != "":
            aggregators_vals = {"s" : "sum", "m" : "mean", "g" : "gmean"}
            aggs = dict()
            for part in config_string[2].split(","):
                p = part.split(":")
                val = aggregators_vals.get(p[1], p[1])
                aggs[all_attributes[int(p[0])]] = val
            ret["custom_aggregators"] = aggs
                
        return ret
