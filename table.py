from bokeh.models.widgets.tables import HTMLTemplateFormatter
from copy import deepcopy
import math
import numpy as np
import param
import pandas as pd
from collections import defaultdict
import panel as pn
from scipy import stats

from prpopupreport import PRPopupReport
from experimentdata import ExperimentData
from problemtable import ProblemTablereport

# TODO: is replacing 0 with something like 0.0001 a valid approach for gmean?
# TODO: fix warnings for gmean

class Tablereport(PRPopupReport):
    attributes = param.ListSelector()
    domains = param.ListSelector()
    precision = param.Integer(default=3)

    stylesheet = """
        .tabulator-row.tabulator-selected .tabulator-cell{
            background-color: #9abcea !important;
        }

        .tabulator-row:hover {
            background-color: #bbbbbb !important;
        }

        .tabulator .tabulator-row.tabulator-selectable:hover .tabulator-cell{
            background-color: #769bcc !important;
        }
    """

    def __init__(self, experiment_data = ExperimentData(), **params):
        super().__init__(experiment_data, **params)

        self.unfolded = dict() # which attributes/domains for each attribute are unfolded in the table
        self.computed = dict() # per attribute: used aggregator, are domain aggregatos up to date
        self.exp_data_dropna = pd.DataFrame() # same as self.experiment_data.data.dropna()
        self.table = pd.DataFrame() # experiment data with aggregates, should be used as base data
        self.previous_precision = -1 # used to find out if we need to reapply formatters

        # ajaxLoader false is set to reduce blinking (https://github.com/olifolkerd/tabulator/issues/1027)
        self.data_view = pn.widgets.Tabulator(
            value=self.table, disabled = True, show_index = False,
            pagination="remote", page_size=10000, frozen_columns=['Index'],
            sizing_mode='stretch_both', configuration={"ajaxLoader":"False"},
            sortable=False, stylesheets=[Tablereport.stylesheet]
        )
        self.data_view.add_filter(self.filter)
        self.data_view.style.apply(func=self.style_table_by_row, axis=1)
        self.data_view.on_click(self.on_click_callback)

        self.param_view = pn.Column(
            pn.Param(self.param.precision),
            pn.pane.HTML("Attributes", styles={'font-size': '10pt', 'font-family': 'Arial', 'padding-left': '10px'}),
            pn.widgets.CrossSelector.from_param(self.param.attributes, definition_order = False, width = 475, styles={'padding-left': '10px'}),
            pn.pane.HTML("Domains", styles={'font-size': '10pt', 'font-family': 'Arial', 'padding-left': '10px'}),
            pn.widgets.CrossSelector.from_param(self.param.domains, definition_order = False, width = 475, styles={'padding-left': '10px'}),
            width=500
        )

    def set_experiment_data_dependent_parameters(self):
        param_updates = super().set_experiment_data_dependent_parameters()

        # Reset fields.
        self.exp_data_dropna = self.experiment_data.data.dropna()
        self.table = pd.DataFrame()
        self.unfolded = dict()
        self.computed = { attribute : {"aggregator": None, "domains_outdated" : True} for attribute in self.experiment_data.numeric_attributes }
        self.computed["__columns"] = []
        self.computed["__domains"] = []
        self.previous_precision = -1

        self.param.attributes.objects = self.experiment_data.attributes
        self.param.attributes.default = self.experiment_data.attributes
        self.param.domains.objects = self.experiment_data.domains
        self.param.domains.default = self.experiment_data.domains
        param_updates["attributes"] =  self.experiment_data.attributes
        param_updates["domains"] = self.experiment_data.domains

        # Build the rows for the aggregated values such that we later just overwrite values rather than concatenate.
        mi = pd.MultiIndex.from_product([self.experiment_data.attributes, ["--", *self.experiment_data.domains], ["--"]],
                                        names = ["attribute", "domain", "problem"])
        aggregated_data_skeleton = pd.DataFrame(data = "", index = mi, columns = self.experiment_data.algorithms)
        # Combine experiment data and aggregated data skeleton.
        self.table = pd.concat([self.experiment_data.data, aggregated_data_skeleton]).sort_index()

        # Add Index column (solely used in the visualization).
        pseudoindex = [x[0] if x[1]=="--" else (x[1] if x[2] == "--" else x[2]) for x in self.table.index]
        self.table.insert(0, "Index", pseudoindex)

        return param_updates


    def get_view_table(self):
        return self.table


    def get_current_columns(self):
        return self.experiment_data.algorithms


    def style_table_by_row(self, row):
        # Give aggregates a different style, and indent Index col text if it's a domain or problem.
        style = [""] * len(row)
        if row.name[1] == "--":
            style = [x + "font-weight: bold; background-color: #E6E6E6;" for x in style]
        elif row.name[2] == "--":
            style = [x + "font-weight: bold; background-color: #F6F6F6;" for x in style]
            style[0] = style[0] + "text-indent:25px;"
        else:
            style[0] = "text-indent:50px;"
        return style


    def filter(self, df):
        if df.empty:
            return df

        indices = [(a,"--","--") for a in self.attributes]
        for a, doms in self.unfolded.items():
            if a not in self.attributes:
                continue
            indices += [(a,d,"--") for d in self.domains]
            for d in doms:
                if d not in self.domains:
                    continue
                indices += [(a,d,p) for p in self.experiment_data.problems[d]]
        indices.sort()
        max_length = max([len(x) for x in df.loc[indices]['Index']])
        self.data_view.widths = {'Index': 10+max_length*7}
        return df.loc[indices]


    def on_click_callback(self, e):
        row = self.table.iloc[e.row]
        attribute, domain, problem = row.name[0:3]

        # clicked on concrete problem -> open problem wise report
        if problem != "--":
            self.add_problem_report_popup(domain, problem, self.get_current_columns())
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

        self.view_data()
        # Setting the selection makes the redrawn table jump to that row.
        # TODO: unfortunately this results in blinking, can we do better?
        self.data_view.selection = []
        self.data_view.selection = [e.row]


    def aggregate_where_necessary(self):
        current_columns = self.get_current_columns()
        columns_outdated = current_columns != self.computed["__columns"]
        domains_outdated = self.domains != self.computed["__domains"]
        self.computed["__columns"] = current_columns
        self.computed["__domains"] = self.domains

        # If the columns used for aggregation are outdated, recompute dropna to only consider current columns.
        if columns_outdated:
            unique_columns = list(dict.fromkeys(current_columns))
            if not unique_columns:
                return
            self.exp_data_dropna = self.experiment_data.data[unique_columns].dropna()

        cols_without_index = self.table.columns[1:]
        for attribute in self.experiment_data.numeric_attributes:
            aggregator = self.experiment_data.attribute_info[attribute].aggregator
            if not columns_outdated and not domains_outdated and aggregator == self.computed[attribute]["aggregator"]:
                continue
            self.computed[attribute]["aggregator"] = aggregator

            # Compute the overall aggregate.
            attribute_data = None
            index_string = f"{attribute} ({aggregator}, "
            num_problems = 0
            if attribute not in self.exp_data_dropna.index:
                new_aggregates = np.NaN
            else:
                attribute_data = self.exp_data_dropna.loc[attribute]
                attribute_data = attribute_data.loc[attribute_data.index.get_level_values('domain').isin(self.domains)]
                attribute_data = attribute_data.apply(pd.to_numeric, errors='coerce')
                num_problems = len(attribute_data.index)
                # Since gmean is not a built-in function we need to set the variable to the actual function here.
                if aggregator == "gmean":
                    aggregator = stats.gmean
                    attribute_data = attribute_data.replace(0,0.000001)
                new_aggregates = attribute_data.agg(aggregator)
            self.table.loc[(attribute, "--", "--"),cols_without_index] = new_aggregates

            self.table.loc[(attribute, "--", "--"),"Index"] = index_string + f"{num_problems}/{self.experiment_data.num_problems})"

            self.computed[attribute]["domains_outdated"] = True
            if attribute in self.unfolded:
                self.aggregate_domains_for_attribute(attribute, attribute_data)


    def aggregate_domains_for_attribute(self, attribute, attribute_data = None):
        # Represents the slice of all domain aggregate rows, but without the Index column.
        rows, cols = (attribute, slice(self.experiment_data.domains[0], self.experiment_data.domains[-1]), "--"), self.table.columns[1:]
        # This can happen if there are no problems where all columns have a value for the attribute.
        if attribute not in self.exp_data_dropna.index:
            self.table.loc[rows,cols] = np.NaN
            return

        if attribute_data is None:
            attribute_data = self.exp_data_dropna.loc[attribute].apply(pd.to_numeric, errors='coerce')
        aggregator = self.experiment_data.attribute_info[attribute].aggregator
        # Since gmean is not a built-in function we need to set the variable to the actual function here.
        if aggregator == "gmean":
                aggregator = stats.gmean
                attribute_data.replace(0,0.000001, inplace=True)

        # Clear the slice and apply combine_first (this way, the newly aggregated data is taken wherever it exists).
        self.table.loc[rows,cols] = np.NaN
        self.table.loc[rows,cols] = self.table.loc[rows,cols].combine_first(attribute_data.groupby(level=0).agg(aggregator))

        for domain in self.experiment_data.domains:
            num_problems = len(self.experiment_data.problems[domain])
            num_aggregated = 0 if domain not in attribute_data.index.get_level_values(0) else len(attribute_data.loc[domain].index)
            self.table.loc[(attribute, domain, "--"),'Index'] = f"{domain} ({num_aggregated}/{num_problems})"

        self.computed[attribute]["domains_outdated"] = False


    def update_data_view(self):
        self.aggregate_where_necessary()
        new_table = self.get_view_table()

        # we need to define formatters before setting the new table as new value
        if self.precision != self.previous_precision:
            self.previous_precision = self.precision
            template = f"""
              <%= function formatnumber() {{
                f_val = parseFloat(value);
                if (!isNaN(f_val)) {{
                  if (Number.isInteger(f_val)) {{
                    return '<div style="text-align:right">' + f_val + "</div>";
                  }} else {{
                    return '<div style="text-align:right">' + f_val.toFixed({self.precision}) + "</div>";
                  }}
                }} else {{
                  return  value;
                }}
              }}() %>
            """
            self.data_view.formatters = {x: HTMLTemplateFormatter(template=template) for x in new_table.columns}

        self.data_view.value = new_table



    def get_params_as_dict(self):
        params = super().get_params_as_dict()

        # shorten the attributes parameter by using indices instead of the attribute names
        if "attributes" in params:
            params["attributes"] = [self.param.attributes.objects.index(a) for a in params["attributes"]]
        if "domains" in params:
            params["domains"] = [self.param.domains.objects.index(d) for d in params["domains"]]
        return params


    def set_params_from_dict(self, params):
        if "attributes" in params:
            params["attributes"] = [self.param.attributes.objects[x] for x in params["attributes"]]
        if "domains" in params:
            params["domains"] = [self.param.domains.objects[x] for x in params["domains"]]

