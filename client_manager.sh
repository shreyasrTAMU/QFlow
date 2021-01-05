#!/bin/bash
#python nuc_selenium.py "$1"
#trap "exit" INT
for i in $(eval echo {1..$1}); do (python nuc_selenium.py $i ) &  done