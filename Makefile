.PHONY: test demo demo-scenes demo-freeze demo-soak demo-offline demo-backup demo-rc1 demo-reset bench bench-models review-package verify

test:
	PYTHONPATH=src python3 -m pytest -q
	ruff check src tests benchmark/adapters
	ruff format --check src tests benchmark/adapters

demo:
	PYTHONPATH=src python3 -m nma.cli demo --approve-safe-repairs

demo-scenes:
	PYTHONPATH=src python3 -m nma.cli demo-scenes

demo-freeze:
	PYTHONPATH=src python3 -m nma.cli demo-freeze

demo-soak:
	PYTHONPATH=src python3 -m nma.cli demo-soak

demo-offline:
	PYTHONPATH=src python3 -m nma.cli demo-offline

demo-backup:
	PYTHONPATH=src python3 -m nma.cli demo-backup

demo-rc1:
	PYTHONPATH=src python3 -m nma.cli demo-rc1

demo-reset:
	PYTHONPATH=src python3 -m nma.cli demo-scenes --reset

bench:
	PYTHONPATH=src python3 -m nma.bench --root .

bench-models:
	test -n "$(EXTERNAL_CONFIG)"
	PYTHONPATH=src python3 -m nma.bench --root . --external-config "$(EXTERNAL_CONFIG)"

review-package:
	python3 scripts/build_review_package.py

verify: test demo bench
