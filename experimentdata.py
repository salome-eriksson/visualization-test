import json
import numpy as np
import pandas as pd


class ExperimentData():
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
  
    def __init__(self, properties_file=""):
        try:
            # TODO: this might break in the future since read_json cannot handle passing json directly (although I don't do that?)
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
            for domain in self.domains:
                self.problems[domain] = [x for x in self.data.loc[(self.attributes[0],domain)].index.get_level_values('problem')]

            self.compute_ipc_score()
            
        except Exception as ex:
            self.algorithms = []
            self.domains = []
            self.problems = dict()
            self.attributes = []
            self.numeric_attributes = []
            self.data = pd.DataFrame(index= pd.MultiIndex.from_tuples([],names = ["attribute","domain","problem"]))
