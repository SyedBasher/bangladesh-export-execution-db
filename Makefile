.PHONY: v01 v02 v03 v04 full test
v01:
	python scripts/build_all.py
v02:
	python scripts/build_v02.py
v03:
	python scripts/build_v03.py
v04:
	python scripts/build_v04.py
full: v01 v02 v03
	python scripts/write_manifest.py
test:
	PYTHONPATH=src pytest -q
