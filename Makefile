.PHONY: install build-kb services test evals api ui dashboard docker-up

install:
	pip install -r requirements.txt --break-system-packages

build-kb:
	python scripts/build_kb.py

services:
	@echo "Starting mock network + ticketing APIs on :8001 and :8002 ..."
	PYTHONPATH=. python -m uvicorn services.network_monitoring_api:app --port 8001 & \
	PYTHONPATH=. python -m uvicorn services.ticketing_api:app --port 8002

test:
	PYTHONPATH=. pytest tests/ -v

evals:
	PYTHONPATH=. python evals/run_evals.py

api:
	PYTHONPATH=. python -m uvicorn orchestrator.main:app --port 8000 --reload

ui:
	PYTHONPATH=. python ui/app.py

dashboard:
	PYTHONPATH=. streamlit run dashboard/observability_dashboard.py

docker-up:
	docker compose up --build
