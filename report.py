import param
import panel as pn

from experimentdata import ExperimentData

class Report(param.Parameterized):
    experiment_data_cache = dict()
    properties_file = param.String()
  
    def __init__(self, **params):
        # ~ print("Report init")
        super().__init__(**params)
        if self.properties_file not in Report.experiment_data_cache:
            Report.experiment_data_cache[self.properties_file] = ExperimentData(self.properties_file)            
        self.experiment_data = Report.experiment_data_cache[self.properties_file]
        # ~ print("Report init end")

    @param.depends('properties_file', watch=True)
    def update_experiment_data(self):
        # ~ print("Report update experiment data")
        new_file = self.properties_file
        if new_file not in Report.experiment_data_cache:
            Report.experiment_data_cache[new_file] = ExperimentData(new_file)            
        self.experiment_data = Report.experiment_data_cache[new_file]
        self.set_experiment_data_dependent_parameters()
        # ~ print("Report update experiment data end")

    def set_experiment_data_dependent_parameters():
        pass

    def param_view(self):
        print("Report param view (return)")
        return pn.Param(self.param)

    def data_view(self):
        print("Report data view (return)")
        return pn.pane.Markdown("### Report")
