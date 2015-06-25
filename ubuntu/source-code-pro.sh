#!/bin/bash
mkdir /tmp/adodefont
cd /tmp/adodefont
wget https://github.com/adobe-fonts/source-code-pro/archive/1.017R.zip
unzip 1.017R.zip
mkdir -p $HOME/.fonts
cp source-code-pro-1.017R/OTF/*.otf $HOME/.fonts
fc-cache -f -v
