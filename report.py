import param
import panel as pn

from experimentdata import ExperimentData

class Report(param.Parameterized):
  
    def __init__(self, experiment_data = ExperimentData(), **params):
        super().__init__(**params)
        self.update_experiment_data(experiment_data)
        
        
    def update_experiment_data(self, new_data):
        self.experiment_data = new_data
        param_updates = self.set_experiment_data_dependent_parameters()
        self.param.update(param_updates)

    # Returns a dictionary of parameters and values they should be set to 
    # This dicitionary is batch updated in update_experiment_data.
    def set_experiment_data_dependent_parameters(self):
        return dict()

    def param_view(self):
        return pn.Param(self.param)

    def data_view(self):
        pass

    def deactivate(self):
        pass

    def get_params_as_dict(self):
        d = { name : val for name, val in self.param.get_param_values()
            if val != self.param.params()[name].default }
        d.pop("name")
        return d

    def set_params_from_dict(self,params):
        pass
