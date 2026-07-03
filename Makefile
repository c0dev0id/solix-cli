VENV    := .venv
PYTHON  := $(VENV)/bin/python3
PIP     := $(VENV)/bin/pip

.PHONY: all venv update clean

all: venv

$(VENV)/bin/python3:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install aiohttp aiofiles cryptography "paho-mqtt>=2.1.0" python-dotenv
	$(PIP) install -e vendor/anker-solix-api

venv: $(VENV)/bin/python3

update:
	git submodule update --remote vendor/anker-solix-api
	$(PIP) install -e vendor/anker-solix-api

clean:
	rm -rf $(VENV)
