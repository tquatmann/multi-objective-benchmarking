from .benchmark import *
from .utility import *
from . import storm
from . import  mcsta
import sys
import os

def process_tool_result(result, notes, settings, benchmark, execution_json):
    if result is not None:
        execution_json["result"] = str(result)  # convert to str to not loose precision
        result = try_to_bool_or_number(result)
        if result is not None and "exact" in execution_json["configuration-id"]:
            benchmark.store_reference_result(str(result), "{}.{}".format(execution_json["tool"],execution_json["configuration-id"]))
        if benchmark.has_reference_result():
            execution_json["result-correct"] = is_result_correct(settings, benchmark.get_reference_result(), result)
            if is_number(result) and is_number_or_interval(benchmark.get_reference_result()):
                execution_json["absolute-error"] = try_to_float(get_absolute_error(benchmark.get_reference_result(), result))
                execution_json["relative-error"] = try_to_float(get_relative_error(benchmark.get_reference_result(), result))
                if not execution_json["result-correct"]:
                    # Prepare a message
                    if settings.is_relative_precision():
                        error_kind = "a relative"
                        error_value = execution_json["relative-error"]
                    else:
                        error_kind = "an absolute"
                        error_value = execution_json["absolute-error"]
                    if is_number(result) and not (isinstance(result,float) or isinstance(result,int)):
                        execution_result_str = "'{}' (approx. {})".format(result, try_to_float(result))
                    else:
                        execution_result_str = "'{}'".format(result)
                    if is_number(benchmark.get_reference_result()) and not (isinstance(benchmark.get_reference_result(), float) or isinstance(benchmark.get_reference_result(), int)):
                        ref_result_str = "'{}' (approx. {})".format(benchmark.get_reference_result(), try_to_float(benchmark.get_reference_result()))
                    elif (isinstance(benchmark.get_reference_result(), dict) or isinstance(benchmark.get_reference_result(), OrderedDict)) and "lower" in benchmark.get_reference_result() and "upper" in benchmark.get_reference_result():
                        ref_result_str = "[{},{}]".format(try_to_float(benchmark.get_reference_result()["lower"]), try_to_float(benchmark.get_reference_result()["upper"]))
                    else:
                        ref_result_str = "'{}'".format(benchmark.get_reference_result())
                    notes.append("The tool result {} is tagged as incorrect. The reference result is {} which means {} error of '{}' which is larger than the goal precision '{}'.".format(execution_result_str, ref_result_str, error_kind, error_value, try_to_float(settings.goal_precision())))
            elif not execution_json["result-correct"]:
                notes.append("Result '{}' is tagged as incorrect because it is different from the reference result '{}'.".format(result, benchmark.get_reference_result()))
        else:
            notes.append("Correctness of result is not checked because no reference result is available.")
    else:
        has_timeout = "timeout" in execution_json and execution_json["timeout"]
        has_error = "execution-error" in execution_json and execution_json["execution-error"]
        if not has_timeout and not has_error:
            notes.append("Unable to obtain tool result.")
            execution_json["execution-error"] = True

def parse_tool_output(settings, execution_json):
    with open(execution_json["log"], 'r') as logfile:
        log = logfile.read()

    benchmark = get_benchmark_from_id(settings, execution_json["benchmark-id"])
    
    notes = []
    if execution_json["tool"] == storm.get_name():
        execution_json["supported"] = not storm.is_not_supported(log)
        build_time = storm.get_Build_Time(log)
        if build_time is not None: execution_json["model-building-time"] = build_time
        nontriv_mec = storm.get_nontriv_mec_percentage(log)
        if nontriv_mec is not None: execution_json["nontrivial-mec-percentage"] = nontriv_mec
        preprocessing_time = storm.get_preprocessing_time(log)
        if preprocessing_time is not None: execution_json["preprocessing-time"] = preprocessing_time
        execution_json["bisimulation"] = storm.is_bisimulation_used(log)
        result = None
        mctime = storm.get_MC_Time(log)
        if mctime is not None:
            if True: # old: float(mctime) <= 1800
                execution_json["model-checking-time"] = mctime
                result = storm.get_result(log, benchmark)
                solve_time = storm.get_Solve_Time(log)
                if solve_time is not None: execution_json["model-solving-time"] = solve_time
            else:
                execution_json["timeout"] = True
            execution_json["memout"] = False
            execution_json["expected-error"] = False
        else:
            execution_json["memout"] = storm.is_memout(log)
            execution_json["expected-error"] = storm.is_expected_error(log)
    elif execution_json["tool"] == "mcsta":
        execution_json["supported"] = not mcsta.is_not_supported(log)
        build_time = mcsta.get_Build_Time(log)
        if build_time is not None: execution_json["model-building-time"] = build_time
        result = None
        mctime = mcsta.get_MC_Time(log, benchmark)
        if mctime is not None:
            if True: # old: float(mctime) <= 1800
                execution_json["model-checking-time"] = mctime
                result = mcsta.get_result(log, benchmark)
                solve_time = mcsta.get_Solve_Time(log)
                if solve_time is not None: execution_json["model-solving-time"] = solve_time
            else:
                execution_json["timeout"] = True
            execution_json["memout"] = False
            execution_json["expected-error"] = False
        else:
            execution_json["memout"] = mcsta.is_memout(log)
            execution_json["expected-error"] = mcsta.is_expected_error(log)
    else:
        print("Error: Unknown tool '{}'".format(execution_json["tool"]))
    
    process_tool_result(result, notes, settings, benchmark, execution_json)
    execution_json["notes"] = notes    

def get_group_name_from_logdir(logdir):
    if os.path.basename(logdir) == "":
        return os.path.dirname(logdir)
    else:
        return os.path.basename(logdir)

def get_all_groups_tools_configs(logdirs):
    tc = [("Storm", c.identifier) for c in storm.get_configurations()] + [("mcsta", c.identifier) for c in mcsta.get_configurations()]
    group_names = [get_group_name_from_logdir(logdir) for logdir in logdirs]
    if len(set(group_names)) != len(group_names):
        raise AssertionError("log file directory names must be unique. Got {}".format(group_names))
    return [(group, t, c) for group in group_names for t,c in tc]

def gather_execution_data(settings, logdirs, groups_tools_configs):
    exec_data = OrderedDict() # Group -> Tool -> Config -> Benchmark -> [Data Array]
    for g,t,c in groups_tools_configs:
        if g not in exec_data: exec_data[g] = OrderedDict()
        if t not in exec_data[g]: exec_data[g][t] = OrderedDict()
        exec_data[g][t][c] = OrderedDict()
    for logdir_input in logdirs:
        logdir = os.path.expanduser(logdir_input)
        assert os.path.isdir(logdir), f"Error: directory '{logdir}' does not exist."
        group = get_group_name_from_logdir(logdir)
        print("\nGathering execution data for logfiles in group '{}' directory: {} ...".format(group, logdir))
        json_files = [ f for f in os.listdir(logdir) if f.endswith(".json") and os.path.isfile(os.path.join(logdir, f)) ]
        progress = Progressbar(len(json_files))   
        i = 0
        for execution_json in [ load_json(os.path.join(logdir, f)) for f in json_files ]:
            progress.print_progress(i)
            i += 1
            tool = execution_json["tool"]
            config = execution_json["configuration-id"]
            benchmark = execution_json["benchmark-id"]
            if benchmark not in exec_data[group][tool][config]:
                exec_data[group][tool][config][benchmark] = []
            execution_json["log"] = os.path.join(logdir, execution_json["log"])
            parse_tool_output(settings, execution_json)
            exec_data[group][tool][config][benchmark].append(execution_json)
    print("\n")
    return exec_data
