#!/usr/bin/env bash

BIN_DIR="./bin"
CONDA_DIR="$BIN_DIR/miniconda"
CONDA_BIN_DIR="$CONDA_DIR/bin"

# Make bin folder
mkdir -p $BIN_DIR

# Install Anaconda
curl https://repo.continuum.io/miniconda/Miniconda3-latest-MacOSX-x86_64.sh -o $BIN_DIR/Miniconda3-latest-MacOSX-x86_64.sh
bash $BIN_DIR/Miniconda3-latest-MacOSX-x86_64.sh -p $CONDA_DIR -b

# Install ffmpeg (with OpenSSL support)
# wget https://github.com/nareix/ffmpeg-static-builds/releases/download/3.1.3/ffmpeg-release-64bit-static.tar.xz
wget https://www.johnvansickle.com/ffmpeg/old-releases/ffmpeg-3.3.4-64bit-static.tar.xz
tar xf ffmpeg-release-64bit-static.tar.xz
# mv ffmpeg-3.1.3-64bit-static $BIN_DIR/ffmpeg 
mv ffmpeg-3.3.4-64bit-static $BIN_DIR/ffmpeg

# Install conda dependencies
$CONDA_BIN_DIR/conda install -c conda-forge -y sox
$CONDA_BIN_DIR/conda install -c yaafe -y libflac
$CONDA_BIN_DIR/pip install --upgrade -r ./requirements.txt
