import json
import math
import pandas as pd
import hvplot.pandas
import holoviews as hv
from functools import reduce
from bokeh.io import output_notebook
from ipywidgets import interact, fixed, Dropdown, Checkbox, ToggleButtons, Text

from bokeh.plotting import figure

hv.extension('bokeh')

class PlotData:
    def __init__(self, filename):
        self.data = pd.read_json(filename, orient="index")
        self.data = self.data.set_index(["algorithm","domain","problem"])

        self.algorithms = list(set(self.data.index.get_level_values(0)))
        self.domains = list(set(self.data.index.get_level_values(1)))
        self.attributes = self.data.columns.values.tolist()
        self.numeric_attributes = [x for x in self.attributes if pd.api.types.is_numeric_dtype(self.data.dtypes[x])]

        self.data = self.data.unstack(level=-3)
        self.data.columns = self.data.columns.get_level_values(1) + "_" + self.data.columns.get_level_values(0)


    def get_version_config_pairs(self, v1, v2):
        ret = []
        v1 = v1+"-"
        v2 = v2+"-"
        for alg in self.algorithms:
            if v1 in alg:
                v2alg = alg.replace(v1,v2)
                name = alg.replace(v1,"")
                assert(v2alg in self.algorithms)
                ret.append((alg,v2alg, name))
        return ret
        
    def get_all_configs(self):
        return [(x,x,x) for x in self.algorithms]
        
        
MARKERS = ["+", "x", "*", "y"]
COLORS = ["red", "blue", "teal", "orange", "purple", "lime", "gray"]

def generate_scatterplot(properties, xalg = "", yalg = "",
                xattribute = "search_time", yattribute = "search_time", 
                relative = False, xscale = "log", yscale = "log"):
    config_pairs = []
    logx = True if xscale == "log" else False
    logy = True if yscale == "log" else False
    xlabel = "{} {}".format(xattribute, xalg)
    ylabel = "{} {}".format(yattribute, yalg)
    
    if xalg == "":
        config_pairs = [(x,x,x) for x in properties.algorithms]
    else:
        for alg in properties.algorithms:
            if xalg in alg:
                if yalg == "":
                    config_pairs.append((alg,alg,alg))
                else:
                    alg2 = alg.replace(xalg, yalg)
                    assert(alg2 in properties.algorithms)
                    config_pairs.append((alg, alg2, alg.replace(xalg, "").replace("--","-")))

    plots = []
    counter = 0
    for xalg,yalg,name in config_pairs:
        xcolumn = "{}_{}".format(xalg, xattribute)
        ycolumn = "{}_{}".format(yalg, yattribute)
        transformation = dict()
        if relative:
            transformation[ycolumn] = hv.dim(ycolumn)/hv.dim(xcolumn)
        plots.append(properties.data.hvplot.scatter(x=xcolumn, y=ycolumn,
            label=name, xlabel=xlabel, ylabel=ylabel, logx=logx, logy=logy,
            frame_width = 600, frame_height = 600, marker = MARKERS[counter%len(MARKERS)], color = COLORS[counter%len(COLORS)],
            size=75, alpha=0.75, transforms=transformation, hover_cols=['domain', 'problem']))
        counter = counter+1
    return reduce((lambda x, y: x * y), plots)

def generate_interactive_scatterplot(properties, xalg, yalg,
                xattribute, yattribute, 
                relative, xscale, yscale):
    output_notebook()    
    interact(generate_scatterplot,
             properties=fixed(properties),
             xalg = Text(value=xalg),
             yalg = Text(value=yalg),
             xattribute = Dropdown(options=properties.numeric_attributes, value=xattribute, description = "x Attribute"),
             yattribute = Dropdown(options=properties.numeric_attributes, value=yattribute, description = "y Attribute"),
             relative = Checkbox(value=relative, description = "relative"),
             xscale = ToggleButtons(options=["log", "linear"], value=xscale, description = "x scale"),
             yscale = ToggleButtons(options=["log", "linear"], value=yscale, sescription = "y scale"))
