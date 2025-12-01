import os
import sys
import time
import math
import csv
import json
import shutil

from decimal import *
from fractions import *

from collections import OrderedDict
from .configuration import Configuration

sys.set_int_max_str_digits(100000) # needed to parse large integer literals in json files

def load_json(path : str):
    with open(path, 'r', encoding='utf-8-sig') as json_file:
        return json.load(json_file, object_pairs_hook=OrderedDict)

def save_json(json_data, path : str):
    with open(path, 'w') as json_file:
        json.dump(json_data, json_file, ensure_ascii=False, indent='\t')

def load_csv(path : str, delim='\t'):
    with open(path, 'r') as csv_file:
        return list(csv.reader(csv_file, delimiter=delim))

def save_csv(csv_data, path : str, delim='\t'):
    with open(path, 'w') as csv_file:
        writer = csv.writer(csv_file, delimiter=delim)
        writer.writerows(csv_data)

def get_mdpmc_dir():
    if os.environ.get('MDPMC_DIR') is None:
        return os.path.realpath(os.path.join(sys.path[0], ".."))
    else:
        return os.environ.get('MDPMC_DIR')

def set_mdpmc_dir(s : str):
    return s.replace("$MDPMC_DIR", get_mdpmc_dir())

def ensure_directory(path : str):
    if not os.path.exists(path):
        os.makedirs(path)

def is_valid_filename(name : str, invalid_chars = None):
    if invalid_chars is not None:
        for c in invalid_chars:
            if c in name:
                return False
    try:
        if os.path.isfile(name):
            return True
        open(name, 'a').close()
        os.remove(name)
    except IOError:
        return False
    return True

def remove_directory_contents(directory, exluded = []):
    for name in os.listdir(directory):
        if name not in exluded:
            try:
                path = os.path.join(directory, name)
                remove_file_or_dir(path)
            except Exception:
                print("Unable to remove '{}'".format(path))

def remove_file_or_dir(name):
    if os.path.isdir(name):
        shutil.rmtree(name)
    else:
        os.remove(name)

def is_bool(expr):
    if isinstance(expr, bool):
        return True
    try:
        return expr.lower() in ["true", "false"]
    except:
        return False

def is_inf(expr):
    try:
        return math.isinf(Decimal(expr))
    except Exception:
        return False

def is_number(expr):
    if is_bool(expr):
        return False
    if is_inf(expr):
        return True
    try:
        Fraction(expr)
    except Exception:
        return False
    return True

def is_interval(expr):
    try:
        if is_number(expr["lower"]) and is_number(expr["upper"]):
            return True
    except (InvalidOperation, KeyError, TypeError):
        pass
    return False

def is_number_or_interval(expr):
    if is_number(expr) or is_interval(expr):
        return True
    try:
        return is_number(try_to_number(expr["num"]) / try_to_number(expr["den"]))
    except Exception:
        return False
   

def try_to_number(expr):
    if is_number(expr):
        if isinstance(expr,int):
            return Fraction(expr)
        elif is_inf(expr):
            return Decimal(expr)
        else:
            return Fraction(expr)
    try:
        return try_to_number(expr["num"]) / try_to_number(expr["den"])
    except Exception:
        return expr

def try_to_bool_or_number(expr):
    if is_bool(expr):
        if (isinstance(expr, str)):
            if expr.lower() == "true":
                return True
            elif expr.lower() == "false":
                return False
        return bool(expr)
    return try_to_number(expr)

def get_decimal_representation(number):
    if is_number(number):
        return Decimal(number)
    else:
        return Decimal(number["num"]) / Decimal(number["den"])

def try_to_float(expr):
    # expr might be too large for float
    try:
        return float(expr)
    except Exception:
        return expr

def get_absolute_error(reference_value, result_value):
    return get_error(False, reference_value, result_value)

def get_relative_error(reference_value, result_value):
    return get_error(True, reference_value, result_value)

def get_error(relative : bool, reference_value, result_value):
    result_value = try_to_number(result_value)
    if is_interval(reference_value):
        u = try_to_number(reference_value["upper"])
        l = try_to_number(reference_value["lower"])
        if is_inf(result_value) and not is_inf(u):
            return math.inf
        elif result_value < l:
            return get_error(relative, l, result_value)
        elif result_value > u:
            return get_error(relative, u, result_value)
        else:
            return Fraction(0)
    reference_value = try_to_number(reference_value)
    if relative and reference_value == 0:
        if result_value == 0:
            return Fraction(0)
        else:
            return math.inf
    elif is_inf(reference_value) and is_inf(result_value):
        return Fraction(0)
    elif is_inf(reference_value) or is_inf(result_value):
        return math.inf

    diff = abs(reference_value - result_value)
    if relative:
        return diff / reference_value
    else:
        return diff

def is_result_correct(settings, reference, result):
    if is_number_or_interval(reference) != is_number(result):
        return False
    if is_number_or_interval(reference):
        if is_interval(reference):
            upper_ref = try_to_number(reference["upper"])
        else:
            upper_ref = try_to_number(reference)
        if try_to_number(result) <  1e-8 and upper_ref < 1e-8:
            return True
        return get_error(settings.is_relative_precision(), reference, result) <= settings.goal_precision()
    else:
        return reference == result

def get_seed(index : int) -> int:
    return index ^ ((index<<6) + (index>>2))

class Progressbar(object):
    def __init__(self, max_value, label="Progress", width=50, delay=0.5):
        self.progress = 0
        self.max_value = max_value
        self.label = label
        self.width = width
        self.delay = delay
        self.last_time_printed = time.time()
        sys.stdout.write("\n")
        self.print_progress(0)

    def print_progress(self, value):
        now = time.time()
        if now - self.last_time_printed >= self.delay or value == self.max_value or value == 0:
            if (self.max_value == 0):
                progress = self.width
            else:
                progress = (value * self.width) // self.max_value
            sys.stdout.write("\r{}: [{}{}] {}/{} ".format(self.label, '#'*progress, ' '*(self.width-progress), value, self.max_value))
            sys.stdout.flush()
            self.last_time_printed = now
            return True
        return False
            

class Settings(object):
    def __init__(self):
        self.settings_filename = "settings.json"
        self.json_data = OrderedDict()
        if os.path.isfile(self.settings_filename):
            self.json_data = load_json(self.settings_filename)
        if self.set_defaults():
            self.save()

    def set_defaults(self):
        
        set_an_option = False
        if not "benchmarks-directory" in self.json_data:
            self.json_data["benchmarks-directory"] = "$MDPMC_DIR/qcomp/benchmarks/"
            set_an_option = True
        if not "logs-directory-name" in self.json_data:
            self.json_data["logs-directory-name"] = "logs/"
            set_an_option = True
        if not "results-file-scatter" in self.json_data:
            self.json_data["results-file-scatter"] = "scatter.csv"
            set_an_option = True
        if not "results-file-scatter2" in self.json_data:
            self.json_data["results-file-scatter2"] = "scatteriters.csv"
            set_an_option = True
        if not "results-file-quantile" in self.json_data:
            self.json_data["results-file-quantile"] = "quantile.csv"
            set_an_option = True
        if not "results-file-stats" in self.json_data:
            self.json_data["results-file-stats"] = "stats.json"
            set_an_option = True
        if not "results-dir-table" in self.json_data:
            self.json_data["results-dir-table"] = "table/"
            set_an_option = True
        if not "time-limit" in self.json_data:
            self.json_data["time-limit"] = 2700 # 45 minutes
            set_an_option = True
        if not "goal-precision" in self.json_data:
            self.json_data["goal-precision"] = 1e-3
            set_an_option = True
        if not "relative-precision" in self.json_data:
            self.json_data["relative-precision"] = True
            set_an_option = True
        if not "storm-binary-dir" in self.json_data:
            self.json_data["storm-binary-dir"] = "$MDPMC_DIR/bin/"
            set_an_option = True
        if not "mcsta-binary-dir" in self.json_data:
            self.json_data["mcsta-binary-dir"] = "$MDPMC_DIR/bin/"
            set_an_option = True
        return set_an_option

    def benchmark_dir(self):
        """ Retrieves the directory of the QComp Benchmarks. """
        return self.json_data["benchmarks-directory"]
        
    def logs_dir(self):
        """ Retrieves the directory in which the tool logs are stored. """
        return self.json_data["logs-directory-name"]
        
    def results_file_scatter(self):
        """ Retrieves the filename to which the tool execution results for scatter plots are stored. """
        return self.json_data["results-file-scatter"]

    def results_file_scatter2(self):
        """ Retrieves the filename to which the tool execution results for scatter plots are stored. """
        return self.json_data["results-file-scatter2"]

    def results_file_quantile(self):
        """ Retrieves the filename to which the tool execution results for quantile plots are stored. """
        return self.json_data["results-file-quantile"]

    def results_file_stats(self):
        """ Retrieves the filename to which the tool execution results for latex plots are stored. """
        return self.json_data["results-file-stats"]

    def results_dir_table(self):
        """ Retrieves the directory to which the tool execution result table is stored. """
        return self.json_data["results-dir-table"]

    def time_limit(self):
        """ Retrieves the time limit for tool executions (in seconds). """
        return int(self.json_data["time-limit"])

    def goal_precision(self):
        """ Retrieves the precision the tools have to achieved for numerical results. """
        if self.json_data["goal-precision"] == False:
            return None
        else:
            return Fraction(self.json_data["goal-precision"])
    def is_relative_precision(self):
        """ Retrieves whether the precision is with respect to the relative error. """
        return bool(self.json_data["relative-precision"])
    
    def storm_binary_dir(self):
        """ Retrieves the directory in which the storm binaries are."""
        return self.json_data["storm-binary-dir"]

    def mcsta_binary_dir(self):
        """ Retrieves the directory in which the mcsta binaries are."""
        return self.json_data["mcsta-binary-dir"]
    
    def filtered_paths(self):
        """ returns a list of paths (e.g. home directory) that should be filtered from commands in logfiles
            Note: for portability reasons, this is not stored in the settings.json file by default (but can be entered by hand)"""
        if not "filtered-paths" in self.json_data:
            return [os.path.realpath(sys.path[0]) + "/", os.path.expanduser("~") + "/"]
        return self.json_data["filtered-paths"]

    def get_ignored_tools_configs_for_inv_generation(self):
        """ returns a list of tools that should be ignored when generating the invocations """
        if not "ignored-tools-configs-for-inv-generation" in self.json_data:
            return []
        return self.json_data["ignored-tools-configs-for-inv-generation"]

    def save(self):
        save_json(self.json_data, self.settings_filename)
        print("Settings saved to {}.".format(os.path.realpath(self.settings_filename)))
