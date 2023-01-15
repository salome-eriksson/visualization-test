To setup the notebook, execute the following commands:

python3 -m venv .venv \
source .venv/bin/activate \
pip install notebook \
pip install ipywidgets \
jupyter nbextension enable --py widgetsnbextension \
jupyter notebook
