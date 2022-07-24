import sys
import os

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
SMT_DIR = os.path.dirname(TEST_DIR)
if SMT_DIR not in sys.path:
    sys.path.append(SMT_DIR)

from os.path import (basename, splitext, dirname)
from subprocess import run
from engine import render


def genass_or_cmp(item_list, test_fn_name, test_file_path, asset):
    """boilerplate code for each test function!
    """
    test_file_name = splitext(test_file_path)[0].split("/")[-1]
    svg_file_name = f"{test_file_name}-{test_fn_name}"
    svg_asset_path = dirname(test_file_path)+"/"+svg_file_name+".svg" # single source of truth
    svg_test_path = f"/tmp/{svg_file_name}.svg"
    if asset: # only generate assets
        print()
        if test_fn_name in asset.split("+") and input(f"sure to write asset in {svg_asset_path}? ").lower() in ("y", "yes"):
            render(*item_list, path=svg_asset_path)
    else:                       # run the tests
        render(*item_list, path=svg_test_path)
        assert not run(["cmp", svg_test_path, svg_asset_path],
                       capture_output=True).returncode
