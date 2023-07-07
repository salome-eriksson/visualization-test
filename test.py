#! /usr/bin/env python3

# ~ from experimentviewer import ExperimentViewer
from scatter import Scatterplot
import panel as pn
# ~ from experimentdata import ExperimentData

# ~ reports = [
    # properties_file: path to the properties file, can be local or url
    # xattribute and yattribute: which run attribute should be plotted. Must be contained in the properties file and must be numerical
    # relative: plot y value relative to x value
    # xscale and yscale : either "log" or "linear"
    # groupby: which points should be grouped to the same legend entry. Must be "name" or "domain"
    # fill_alpha: opaquness of the mark fill (borders will be solid either way). Must be between 0 and 1
    # marker_size: size of the marks. I don't know in which unit this is measured, maybe pixels
    # xsize and ysize: size of the plot. I assume this is in pixels.
    # xalg_string and yalg_string: Will pair up algorithms by taking string "<a>xalg<b>" as x algorithm and "<a>yalg<b>" as yalg
    #   (where <a> and <b> are random strings). So for example you can use "base" and "v1" to compare revisions.
    # algorithm_pairs: list of tuples (xalg, yalg, name). xalg and yalg are algorithm names in config,
    #   and name is how the entry should be called in the plot legend.
    # ~ Scatterplot(properties_file = "https://ai.dmi.unibas.ch/_tmp_files/simon/properties",
                # ~ xattribute = "search_time", yattribute = "search_time", 
                # ~ relative = True, xscale = "log", yscale = "linear",  grouby = "name",
                # ~ fill_alpha = 0.2, marker_size = 100, xsize = 1000, ysize = 1000,
                # ~ xalg_string = "base", yalg_string = "v2",
                # ~ algorithm_pairs = [("issue1045-base-lm-exhaust", "issue1045-v2-lm-exhaust", "lm-exhaust")])
# ~ ]
# ~ viewer = ExperimentViewer(reports = reports)
# ~ viewer.show()

plot = Scatterplot()
view = pn.Row(plot.param_view, plot.data_view)
# ~ pn.state.location.sync(plot, {'marker_size': 'marker_size'})
pn.state.location.sync(plot,
    {
        'properties_file': 'properties_file',
        'xattribute' : 'xattribute',
        'yattribute' : 'yattribute',
        'relative': 'relative',
        'xscale': 'xscale',
        'yscale': 'yscale',
        'groupby': 'groupby',
        'fill_alpha': 'fill_alpha',
        'marker_size' : 'marker_size',
        'xsize' : 'xsize',
        'ysize' : 'ysize',
        'replace_zero' : 'replace_zero',
        'autoscale' : 'autoscale',
        'xmin' : 'xmin',
        'ymin' : 'ymin',
        'xmax' : 'xmax',
        'ymax' : 'ymax',
        'algorithm_selector' : 'algorithm_selector'
        # ~ 'algorithm_selector' : 'algorithm_selector'
    })
view.servable()
