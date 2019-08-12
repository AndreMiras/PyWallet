VENV_NAME=venv
ACTIVATE_PATH=$(VENV_NAME)/bin/activate
PIP=`. $(ACTIVATE_PATH); which pip`
TOX=`which tox`
GARDEN=$(VENV_NAME)/bin/garden
PYTHON=$(VENV_NAME)/bin/python
SYSTEM_DEPENDENCIES=virtualenv build-essential libpython3.6-dev \
    libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
	cmake python-numpy tox wget curl libssl-dev libzbar-dev \
    xclip xsel
OS=$(shell lsb_release -si)
TMPDIR ?= /tmp
DOWNLOAD_DIR = $(TMPDIR)/downloads
KM_REPOSITORY=https://raw.githubusercontent.com/AndreMiras/km
KM_BRANCH=develop
OPENCV_MAKEFILE_NAME=Makefile.opencv
OPENCV_MAKEFILE_URL=$(KM_REPOSITORY)/$(KM_BRANCH)/attachments/$(OPENCV_MAKEFILE_NAME)


all: system_dependencies virtualenv

$(VENV_NAME):
	test -d $(VENV_NAME) || virtualenv -p python3 $(VENV_NAME)
	. $(VENV_NAME)/bin/activate
	$(PIP) install Cython==0.26.1
	$(PIP) install -r requirements/requirements.txt
	$(GARDEN) install qrcode
	$(GARDEN) install xcamera

virtualenv: $(VENV_NAME)

system_dependencies:
ifeq ($(OS), Ubuntu)
	sudo apt install --yes --no-install-recommends $(SYSTEM_DEPENDENCIES)
endif

$(DOWNLOAD_DIR):
	mkdir --parents $(DOWNLOAD_DIR)

opencv_build: $(DOWNLOAD_DIR)
	curl --location --progress-bar $(OPENCV_MAKEFILE_URL) \
		--output $(DOWNLOAD_DIR)/$(OPENCV_MAKEFILE_NAME)
	make --file $(DOWNLOAD_DIR)/$(OPENCV_MAKEFILE_NAME) VENV_NAME=$(VENV_NAME)

opencv_deploy: opencv_build virtualenv
	make --file $(DOWNLOAD_DIR)/$(OPENCV_MAKEFILE_NAME) opencv_deploy VENV_NAME=$(VENV_NAME)

opencv: opencv_deploy

clean:
	rm -rf $(VENV_NAME) .tox/ $(OPENCV_BASENAME)

test:
	$(TOX)

uitest:
	. $(ACTIVATE_PATH) && \
	$(PYTHON) -m kivyunittest --folder src/tests/ui/ --pythonpath src/
