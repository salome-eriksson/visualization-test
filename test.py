#! /usr/bin/env python3

from experimentviewer import ExperimentViewer
from scatter import Scatterplot
from experimentdata import ExperimentData

expdata = ExperimentData("properties")
reports = [
    Scatterplot(experiment_data = expdata, xalg_string="noverify", yalg_string="verify",
                xattribute="search_time", yattribute="search_time", relative=True,
                algorithm_pairs = {"c1": ("lmcut", "mas")})
]
viewer = ExperimentViewer(properties_file="properties", reports = reports)
viewer.show()
