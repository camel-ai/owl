lint:
	@black . -l 115 -t py311
	@mypy . --strict