.PHONY: test demo demo-scenes demo-freeze demo-soak demo-offline demo-backup demo-rc1 demo-reset agentic-freeze bench bench-models review-package public-assets-rc verify

test:
	PYTHONPATH=src python3 -m pytest -q
	ruff check src tests benchmark/adapters scripts
	ruff format --check src tests benchmark/adapters scripts

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

agentic-freeze:
	PYTHONPATH=src python3 scripts/check_agentic_v03_freeze.py

bench:
	PYTHONPATH=src python3 -m nma.bench --root .

bench-models:
	test -n "$(EXTERNAL_CONFIG)"
	PYTHONPATH=src python3 -m nma.bench --root . --external-config "$(EXTERNAL_CONFIG)"

review-package:
	python3 scripts/build_review_package.py

public-assets-rc:
	PYTHONPATH=src python3 scripts/check_public_assets_rc.py --verify-install

verify: test demo bench
