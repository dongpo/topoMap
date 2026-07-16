.PHONY: test demo bench bench-models verify

test:
	PYTHONPATH=src python3 -m pytest -q
	ruff check src tests benchmark/adapters
	ruff format --check src tests benchmark/adapters

demo:
	PYTHONPATH=src python3 -m nma.cli demo --approve-safe-repairs

bench:
	PYTHONPATH=src python3 -m nma.bench --root .

bench-models:
	test -n "$(EXTERNAL_CONFIG)"
	PYTHONPATH=src python3 -m nma.bench --root . --external-config "$(EXTERNAL_CONFIG)"

verify: test demo bench
