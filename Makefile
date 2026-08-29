.PHONY: test test-current test-historical lint format-check demo demo-scenes demo-freeze demo-soak demo-offline demo-backup demo-rc1 demo-reset agentic-freeze bench bench-models review-package public-assets-rc ama-cloud-test ama-cloud-deploy verify

test: test-current

test-current:
	PYTHONPATH=src python3 -m pytest -q -m "not historical_freeze"

test-historical:
	PYTHONPATH=src python3 -m pytest -q -m historical_freeze

lint:
	python3 scripts/run_maintained_ruff.py check

format-check:
	python3 scripts/run_maintained_ruff.py format

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

ama-cloud-test:
	PYTHONPATH=src python3 -m pytest -q tests/test_ama_live_01.py tests/test_ama_cloud_01.py

ama-cloud-deploy:
	test -n "$(GOOGLE_CLOUD_PROJECT)"
	./scripts/deploy_ama_cloud_run.sh "$(GOOGLE_CLOUD_PROJECT)" "$(or $(GOOGLE_CLOUD_REGION),asia-southeast1)"

verify: lint format-check test-current demo bench
