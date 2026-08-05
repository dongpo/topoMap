.PHONY: test demo demo-scenes demo-freeze demo-soak demo-reset bench bench-models verify

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

demo-reset:
	PYTHONPATH=src python3 -m nma.cli demo-scenes --reset

bench:
	PYTHONPATH=src python3 -m nma.bench --root .

bench-models:
	test -n "$(EXTERNAL_CONFIG)"
	PYTHONPATH=src python3 -m nma.bench --root . --external-config "$(EXTERNAL_CONFIG)"

verify: test demo bench
