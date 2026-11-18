PYTHON=python

data:
	$(PYTHON) src/fetch_data.py
	$(PYTHON) src/validate_data.py

analyse:
	$(PYTHON) src/build_indicators.py

figures:
	$(PYTHON) src/visualize.py

test:
	pytest -q

all: data analyse figures test

streamlit:
	streamlit run streamlit_app.py
