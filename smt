#!/usr/bin/python3

import argparse
from engine import (
    render,
    _loaded_fonts
)
print("SMT 0.0.0")
print("Copyright (c) Amir Teymuri, 2021 - 2022")
parser = argparse.ArgumentParser()
parser.add_argument("score", help="smt score files to render")
args = parser.parse_args()
print(args.score)
