import json
import numpy as np
import pandas as pd
from io import StringIO

class Attribute():
    def __init__(self, name, default_min_wins = None, default_aggregator = None):
        self.name = name
        self.min_wins = self.default_min_wins =  default_min_wins
        self.aggregator = self.default_aggregator = default_aggregator

    def set_min_wins(self, min_wins):
        self.min_wins = min_wins

    def reset_min_wins(self):
        self.min_wins = self.default_min_wins

    def set_aggregator(self, aggregator):
        self.aggregator = aggregator

    def reset_aggregator(self):
        self.aggregator = self.default_aggregator

    def __str__(self):
        return f"{self.name} (min {'wins' if self.min_wins else 'loses' }, {self.aggregator} aggregator)"

PREDEFINED_ATTRIBUTES = {
  "cost" : (True, "sum"),
  "coverage" : (False, "sum"),
  "dead_ends" : (False, "sum"),
  "evaluated" : (True, "gmean"),
  "evaluations" : (True, "gmean"),
  "evaluations_until_last_jump" : (True, "gmean"),
  "expansions" : (True, "gmean"),
  "expansions_until_last_jump" : (True, "gmean"),
  "generated" : (True, "gmean"),
  "generated_until_last_jump" : (True, "gmean"),
  "initial_h_value" : (False, "sum"),
  "ipc-sat-score" : (False, "sum"),
  "ipc-sat-score-no-planning-domains" : (False, "sum"),
  "memory" : (True, "sum"),
  "plan_length" : (True, "sum"),
  "planner_memory" : (True, "sum"),
  "planner_time" : (True, "gmean"),
  "planner_wall_clock_time" : (True, "gmean"),
  "raw_memory" : (True, "sum"),
  "score_evaluations" : (False, "sum"),
  "score_expansions" : (False, "sum"),
  "score_generated" : (False, "sum"),
  "score_memory" : (False, "sum"),
  "score_search_time" : (False, "sum"),
  "score_total_time" : (False, "sum"),
  "search_time" : (True, "gmean"),
  "total_time" : (True, "gmean"),
  "translator_time_done" : (True, "gmean")
}


class ExperimentData():
    def __init__(self, properties_file=StringIO("")):
        try:
            self.data = pd.read_json(properties_file, orient="index")
            self.attributes = [x for x in self.data.columns if x not in ["algorithm", "domain", "problem"]]
            self.numeric_attributes = [x for x in self.attributes if pd.api.types.is_numeric_dtype(self.data.dtypes[x])]
            self.algorithms = list(self.data.algorithm.unique())
            self.domains = list(self.data.domain.unique())

            # pivot such that the columns are a combination of algorithm-attribute, and then stack such that the attribute becomes part of the index
            self.data = self.data.pivot(index=["domain","problem"], columns="algorithm", values=self.attributes).stack(0, dropna = False)
            # pivot does not set a name for the newly created index column
            self.data.index.names = ["domain","problem","attribute"]
            # reorder and sort such that attribute is the first index column
            self.data = self.data.reorder_levels(["attribute","domain","problem"])
            self.data = self.data.sort_index()
            # build a dicitonary that stores for every domain a list of problem names
            self.problems = dict()
            self.num_problems = 0
            for domain in self.domains:
                self.problems[domain] = [x for x in self.data.loc[(self.attributes[0],domain)].index.get_level_values('problem')]
                self.num_problems  += len(self.problems[domain])

            self.compute_ipc_score()

            # generate Attribute classes for each attribute
            self.attribute_info = dict()
            for attribute in self.attributes:
                a = None
                if attribute in PREDEFINED_ATTRIBUTES:
                    a = Attribute(attribute, PREDEFINED_ATTRIBUTES[attribute][0], PREDEFINED_ATTRIBUTES[attribute][1])
                elif attribute in self.numeric_attributes:
                    min_wins = True if "memory" in attribute or "time" in attribute else False
                    a = Attribute(attribute, min_wins, "sum")
                else:
                    a = Attribute(attribute, None, None)
                assert(a)
                self.attribute_info[attribute] = a

        except Exception as ex:
            self.algorithms = []
            self.domains = []
            self.problems = dict()
            self.attributes = []
            self.numeric_attributes = []
            self.data = pd.DataFrame(index= pd.MultiIndex.from_tuples([],names = ["attribute","domain","problem"]))


    def compute_ipc_score(self):
        if "cost" not in self.data.index.get_level_values(0):
            return
        upper_bounds = pd.read_json("upper_bounds.json", orient="index")
        upper_bounds = upper_bounds.set_index(["domain","problem"])
        costs = self.data.loc["cost"]

        for with_upper in [True, False]:
            tmp_data = costs.copy()
            if with_upper:
                tmp_data["upper_bounds"] = upper_bounds
            min_costs = tmp_data.min(axis=1)

            score_data = (1/costs).fillna(0).multiply(min_costs, axis=0)
            score_data["attribute"] = "ipc-sat-score" if with_upper else "ipc-sat-score-no-planning-domains"
            score_data.set_index(["attribute", score_data.index], inplace=True)
            self.data = pd.concat([self.data, score_data])

        self.attributes = sorted(self.attributes + ["ipc-sat-score", "ipc-sat-score-no-planning-domains"])
        self.numeric_attributes = sorted(self.numeric_attributes + ["ipc-sat-score", "ipc-sat-score-no-planning-domains"])
        self.data = self.data.sort_values("attribute")


    def set_attribute_customizations(self, min_wins, aggregators):
        for name, a in self.attribute_info.items():
            if name not in min_wins.keys():
                a.reset_min_wins()
            else:
                a.set_min_wins(min_wins[name])

            if a.name not in aggregators.keys():
                a.reset_aggregator()
            else:
                a.set_aggregator(aggregators[name])
