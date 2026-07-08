# RDT-Thesis3 reproducibility targets (§10.4). `make help` for the list.
.PHONY: help env test screen figures provenance reproduce campaign clean

help:
	@echo "RDT-Thesis3 make targets:"
	@echo "  make env         install pinned CPU environment (requirements.txt)"
	@echo "  make test        run the test suite (33 gates)"
	@echo "  make screen      rebuild the GBT screen deterministically from recipe"
	@echo "  make provenance  run the provenance sync gate"
	@echo "  make figures     regenerate F1-F9 from present data sources"
	@echo "  make reproduce   screen + provenance + figures (one command)"
	@echo "  make campaign    full 2,000-run H4/H5 campaign (12 workers, ~7 min)"
	@echo "  make gpu         install GPU stack for the N2 experiments"

env:
	pip install -r requirements.txt

gpu:
	pip install -r requirements-gpu.txt

test:
	python -m pytest tests/ -q

screen:
	python scripts/reproduce.py --screen

provenance:
	python scripts/check_provenance.py

figures:
	python scripts/make_figures.py

reproduce:
	python scripts/reproduce.py --all

campaign:
	python scripts/campaign.py --cats D1,D3,D4,D8 --n 500 --workers 12
	python scripts/campaign_a1_ttr.py --cats D1,D3,D4,D8 --n 500 --workers 12
	python scripts/analysis_prereg.py
	python scripts/analysis_h5_paired.py

clean:
	rm -rf figures/*.png figures/*.pdf data/campaign data/campaign_a1 data/campaign_cap*
