import param
import panel as pn

from experimentdata import ExperimentData

class Report(param.Parameterized):
    def __init__(self, experiment_data, **params):
        super().__init__(**params) 
        self.experiment_data = experiment_data

    def update_experiment_data(self, experiment_data):
        self.experiment_data = experiment_data

    def param_view(self):
        return pn.Param()

    def data_view(self):
        return hv.HLine(1).opts(color="red", line_width=2)

    def view(self):
        return pn.Row(param_view, data_view)
