.PHONY: all install initdb collect analyze-threats analyze-privacy report clean
all: help
install:
	pip install -r requirements.txt
initdb:
	python src/fls_analyzer/db_handler.py
collect:
	python scripts/1_collect_links.py
analyze-threats:
	python scripts/2_analyze_threats.py
analyze-privacy:
	python scripts/3_analyze_privacy.py
report:
	python scripts/4_generate_figures.py

# Clean up generated files
clean:
	rm -f data/fls_data.db
	rm -rf figures/*
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	echo "Cleaned generated files."