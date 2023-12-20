import param
import panel as pn

from experimentdata import ExperimentData

class Report(param.Parameterized):
  
    def __init__(self, **params):
        print("Report init")
        super().__init__(**params)  
        self.experiment_data = None
        print("Report init end")

    def update_experiment_data(self, new_data):
        print("Report update experiment data") 
        self.experiment_data = new_data
        self.set_experiment_data_dependent_parameters()
        print("Report update experiment data end")

    def set_experiment_data_dependent_parameters(self):
        pass

    def param_view(self):
        print("Report param view (return)")
        return pn.Param(self.param)

    def data_view(self):
        print("Report data view (return)")
        return pn.pane.Markdown("### Report")
