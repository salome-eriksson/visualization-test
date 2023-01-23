Needed packages: holoviews hvplot
(It also needs pandas param and panel but it seems these get installed as
dependencies)

To run an empty report simply run main.py. You can also predefine a report, an
example that also explains the different parameters can be found in test.py.


To setup the notebook, execute the following commands:

python3 -m venv .venv \
source .venv/bin/activate \
pip install notebook \
pip install ipywidgets \
jupyter nbextension enable --py widgetsnbextension \
jupyter notebook
