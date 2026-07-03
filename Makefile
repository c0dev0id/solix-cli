VENV    := .venv
PYTHON  := $(VENV)/bin/python3
PIP     := $(VENV)/bin/pip

INSTALL_DIR := $(HOME)/python/solix-cli
MAN_DIR     := $(INSTALL_DIR)/share/man/man1

.PHONY: all venv install update clean

all: venv

$(VENV)/bin/python3:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -e vendor/anker-solix-api
	$(PIP) install -e .

venv: $(VENV)/bin/python3

install: $(VENV)/bin/python3
	python3 -m pip install --prefix=$(INSTALL_DIR) vendor/anker-solix-api .
	mkdir -p $(MAN_DIR)
	install -m 644 solix-cli.1 $(MAN_DIR)/solix-cli.1

update:
	git submodule update --remote vendor/anker-solix-api
	$(PIP) install -e vendor/anker-solix-api

clean:
	rm -rf $(VENV) build/ src/*.egg-info
