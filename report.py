import param
import panel as pn

from experimentdata import ExperimentData

class Report(param.Parameterized):
  
    def __init__(self, experiment_data = ExperimentData(), **params):
        print("Report init")
        super().__init__(**params)
        self.update_experiment_data(experiment_data)
        print("Report init end")
        
        
    def update_experiment_data(self, new_data):
        print("Report update experiment data") 
        self.experiment_data = new_data
        param_updates = self.set_experiment_data_dependent_parameters()
        self.param.update(param_updates)
        print("Report update experiment data end")

    # Returns a dictionary of parameters and values they should be set to 
    # This dicitionary is batch updated in update_experiment_data.
    def set_experiment_data_dependent_parameters(self):
        return dict()

    def param_view(self):
        print("Report param view (return)")
        return pn.Param(self.param)

    def data_view(self):
        print("Report data view (return)")
        return pn.pane.Markdown("### Report")

    def deactivate(self):
        pass
