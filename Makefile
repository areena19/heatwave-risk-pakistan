.PHONY: data verify dq warehouse

data:
	python -m src.fetch.open_meteo
	python -m src.fetch.nasa_power
	python -m src.fetch.verify

verify:
	python -m src.fetch.verify

dq:
	python -m src.dq_agent.agent

warehouse:
	python -m src.clean.clean
	python -m src.dq_agent.agent
	python -m src.features.daily
	python -m src.features.lags
	python -m src.warehouse.build