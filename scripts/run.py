from internal.benchmark import *
from internal.utility import *
from internal import benchmarksets
from internal import storm
from internal import mcsta
from internal.invocation import *
from internal.input import *

import traceback



def create_invocations(settings):    
    tools = input_selection("Tools", OrderedDict([(storm.get_name(), ["Run Storm Benchmarks."]), (mcsta.get_name(), ["Run mcsta Benchmarks"])]))
    selected_configurations = OrderedDict()
    if (storm.get_name() in tools):
        selected_configurations[storm.get_name()] = []
        # Get and test directory of storm binary
        input_storm_binary_dir(settings)
        test_result = storm.test_installation(settings)
        if test_result is not None:
            print(test_result)
            input("Press Return to continue or CTRL+C to abort.")
        # Get and test configurations
        storm_cfgs = storm.get_configurations()
        storm_cfgs = [cfg for cfg in storm_cfgs if "{}.{}".format(storm.get_name(), cfg.identifier) not in settings.get_ignored_tools_configs_for_inv_generation()]
        if len(storm_cfgs) == 0:
            input("No Storm configurations available. Press Return to continue.")
        else:
            selected_config_identifiers = input_selection("Storm configurations", OrderedDict([(config.identifier, [config.note, "default" if config.command == "" else config.command]) for config in storm_cfgs]))
            print("Selected {} Storm configurations.".format(len(selected_config_identifiers)))
        for config in storm_cfgs:
            if config.identifier in selected_config_identifiers:
                test_result = storm.test_installation(settings, config)
                if test_result is not None:
                    print("Error when testing configuration '{}':".format(config.identifier))
                    print(test_result)
                    input("Press Return to continue or CTRL+C to abort.")
                selected_configurations[storm.get_name()].append(config)
        
    if (mcsta.get_name() in tools):
        selected_configurations[mcsta.get_name()] = []
        # Get and test directory of mcsta binary
        input_mcsta_binary_dir(settings)
        test_result = mcsta.test_installation(settings)
        if test_result is not None:
            print(test_result)
            input("Press Return to continue or CTRL+C to abort.")
        # Get and test configurations
        mcsta_cfgs = mcsta.get_configurations()
        mcsta_cfgs = [cfg for cfg in mcsta_cfgs if "{}.{}".format(mcsta.get_name(), cfg.identifier) not in settings.get_ignored_tools_configs_for_inv_generation()]
        if len(mcsta_cfgs) == 0:
            input("No mcsta configurations available. Press Return to continue.")
        else:
            selected_config_identifiers = input_selection("mcsta configurations", OrderedDict([(config.identifier, [config.note, "default" if config.command == "" else config.command]) for config in mcsta_cfgs]))
            print("Selected {} mcsta configurations.".format(len(selected_config_identifiers)))
        for config in mcsta_cfgs:
            if config.identifier in selected_config_identifiers:
                test_result = mcsta.test_installation(settings, config)
                if test_result is not None:
                    print("Error when testing configuration '{}':".format(config.identifier))
                    print(test_result)
                    input("Press Return to continue or CTRL+C to abort.")
                selected_configurations[mcsta.get_name()].append(config)

    # Select benchmark sets
    selected_benchmark_sets = input_selection("benchmark sets", benchmarksets.description)
    selected_benchmark_ids = set()
    for setname in selected_benchmark_sets:
        selected_benchmark_ids.update(benchmarksets.data[setname])
    selected_benchmarks = OrderedDict([(mt, []) for mt in ["dtmc", "ctmc", "mdp", "pta", "ma"]])
    for benchmark_id in selected_benchmark_ids:
        benchmark = get_benchmark_from_id(settings, benchmark_id)
        selected_benchmarks[benchmark.get_model_type()].append(benchmark)    
    print("Loaded {} benchmarks from selection '{}'".format(len(selected_benchmark_ids), selected_benchmark_sets))
    
    # model type selection
    model_types = OrderedDict()
    model_types["dtmc"] = ["Discrete Time Markov Chains", "({} benchmarks)".format(len(selected_benchmarks["dtmc"]))]
    model_types["ctmc"] = ["Continuous Time Markov Chains", "({} benchmarks)".format(len(selected_benchmarks["ctmc"]))]
    model_types["mdp"] = ["Markov Decision Processes", "({} benchmarks + {} PTAs via moconv)".format(len(selected_benchmarks["mdp"]), len(selected_benchmarks["pta"]))]
    model_types["ma"] = ["Markov Automata", "({} benchmarks)".format(len(selected_benchmarks["ma"]))]
    selected_benchmarks["mdp"] += selected_benchmarks["pta"]
    selected_model_types = input_selection("models", model_types)
    
    # property type selection
    selected_benchmarks_per_property = OrderedDict()
    for model_type in selected_model_types:
        for benchmark in selected_benchmarks[model_type]:
            if benchmark.get_property_type() in selected_benchmarks_per_property:
                selected_benchmarks_per_property[benchmark.get_property_type()].append(benchmark)
            else:
                selected_benchmarks_per_property[benchmark.get_property_type()] = [benchmark]
    property_types = OrderedDict()
    for property_type in selected_benchmarks_per_property:
        property_types[str(len(property_types) + 1)] = [property_type, " ({} benchmarks)".format(len(selected_benchmarks_per_property[property_type]))]
    selected_property_types = input_selection("properties", property_types)
    selected_benchmarks = []
    for property_type_number in selected_property_types:
        property_type_str = property_types[property_type_number][0] # e.g. 'mdp (7)'
        for benchmark in selected_benchmarks_per_property[property_type_str]:
            selected_benchmarks.append(benchmark)

    num_runs = input_number_of_runs()
    num_configurations = sum([len(cfgs) for cfgs in selected_configurations.values()])
    num_invocations = len(selected_benchmarks) * num_configurations * num_runs
    print("Selected {} benchmarks and {} configurations {}yielding {} invocations in total.".format(len(selected_benchmarks), num_configurations, "" if num_invocations == 1 else " and {} repetitions ".format(num_runs), num_invocations))
    
    input_time_limit(settings)
    input_logs_dir(settings)
    # Creating invocations
    invocations = []
    progressbar = Progressbar(num_invocations, "Generating invocations")
    i = 0
    unsupported = []
    for benchmark in selected_benchmarks:
        for tool in selected_configurations:    
            for configuration in selected_configurations[tool]:
                for run_id in range(1, num_runs + 1):
                    i += 1
                    progressbar.print_progress(i)
                    if tool == storm.get_name():
                        invocation = storm.get_invocation(settings, benchmark, configuration, run_id)
                    elif tool == mcsta.get_name():
                        invocation = mcsta.get_invocation(settings, benchmark, configuration, run_id)
                    else:
                        raise AssertionError("tool {} unknown.".format(tool))
                    if len(invocation.commands) == 0:
                        unsupported.append(invocation.get_identifier() + ": " + invocation.note)
                    else:
                        invocation.time_limit = settings.time_limit()
                        invocations.append(invocation)
    print("")
    if len(unsupported) > 0:
        print("{} invocations are not supported:".format(len(unsupported)))
        for inv in unsupported:
            print("\t" + inv)
    return invocations

def check_invocations(settings, invocations):
    ensure_directory(settings.logs_dir())
    invocation_number = 0
    if len(invocations) > 1:
        progressbar = Progressbar(len(invocations), "Checking invocations")
    else:
        sys.stdout.write("Checking invocation ... ")
        sys.stdout.flush()
    invocation_identifiers = set()
    result = True
    for invocation in invocations:
        invocation_number = invocation_number + 1
        if len(invocations) > 1:
            progressbar.print_progress(invocation_number)
        try:
            # check whether there are no commands
            if len(invocation.commands) == 0:
                continue
            benchmark = get_benchmark_from_id(settings, invocation.benchmark_id)
            # ensure that the actual benchmark files exist
            for filename in benchmark.get_all_filenames():
                if not os.path.isfile(os.path.join(benchmark.get_directory(), filename)):
                    raise AssertionError(
                        "The file '{}' does not exist.".format(os.path.join(benchmark.get_directory(), filename)))
            # ensure that the invocation identifier (consisting of benchmark and configuration id) can be a filename and are unique
            if not is_valid_filename(invocation.get_identifier(), "/"):
                raise AssertionError("Invocation identifier '{}' is either not a valid filename or contains a '.'.".format(invocation.get_identifier()))
            if invocation.get_identifier() in invocation_identifiers:
                raise AssertionError("Invocation identifier '{}' already exists.".format(invocation.get_identifier()))
            invocation_identifiers.add(invocation.get_identifier())
        except Exception:
            print("Error when checking invocation #{}: {}".format(invocation_number - 1, invocation.get_identifier()))
            traceback.print_exc()
            result = False
    print("")
    return result
    
def run_invocations(settings, invocations):
    invocation_number = 0
    if len(invocations) > 1:
        progressbar = Progressbar(len(invocations), "Executing invocations")
    else:
        sys.stdout.write("Executing invocation ... ")
        sys.stdout.flush()
    try:
        for invocation in invocations:
            invocation_number = invocation_number + 1
            benchmark = get_benchmark_from_id(settings, invocation.benchmark_id)
            if len(invocations) > 1:
                progressbar.print_progress(invocation_number)
            # execute the invocation
            execution = invocation.execute()
            execution_result = execution.to_json()
            logfile_name = invocation.get_identifier() + ".log"
            execution_result["log"] = logfile_name
            # save logfile
            with open(os.path.join(settings.logs_dir(), logfile_name), 'w', encoding="utf-8") as logfile:
                logfile.write(execution.concatenate_logs())
            # save execution results in json format
            save_json(execution_result, os.path.join(settings.logs_dir(), invocation.get_identifier() + ".json"))
    except KeyboardInterrupt as e:
        print("\nInterrupt while processing invocation #{}: {}".format(invocation_number - 1, invocation.get_identifier()))
    except Exception:
        print("ERROR while processing invocation #{}: {}".format(invocation_number - 1, invocation.get_identifier()))
        traceback.print_exc()
    
if __name__ == "__main__":
    print("MDP benchmarking tool.")
    print("This script selects and executes benchmarks.")
    print("Usages:")
    print("python3 {}                            Creates an invocations file.".format(sys.argv[0]))
    print("python3 {} <filename>                 Executes benchmarks from a previously created invocations file located at <filename>.".format(sys.argv[0]))
    print("python3 {} <filename> <i>             Executes the <i>th invocation (0 based) from a previously created invocations file located at <filename>.".format(sys.argv[0]))
    print("python3 {} merge <file1> <file2> ...  Merges previously created (and disjoint) invocation files located at <file1>, <file2>, ....".format(sys.argv[0]))
    print("")
    if (len(sys.argv) == 2 and sys.argv[1] in ["-h", "-help", "--help"]) or (len(sys.argv) > 3 and sys.argv[1] != "merge"):
        print("ERROR: Invalid arguments.)")
        exit(1)
    
    settings = Settings()
    
    if len(sys.argv) == 1 or sys.argv[1] == "merge":
        # generate new invocations or merge existing once
        if len(sys.argv) == 1:
            input("No invocations file loaded. Press Return to create one now or CTRL+C to abort.")
            invocations = create_invocations(settings)
            invocations_json = [inv.to_json() for inv in invocations]
        else:
            invocations_json = []
            for filename in sys.argv[2:]:
                if not os.path.isfile(filename):  raise AssertionError("Invocations input file {} does not exist".format(filename))
                invocations_json += load_json(filename)
            invocations = [Invocation(inv) for inv in invocations_json]
            print("Loaded {} invocations from {} files".format(len(invocations_json), len(sys.argv) - 2))
        # save invocations
        while True:
            response = input("Enter a filename to store the invocations for later usage or press Return to continue: ")
            if response == "": break
            if (is_valid_filename(response)):
                if os.path.isfile(response): 
                    if input("File {} exists. Overwrite? (type 'y' or 'n'): ".format(response)) != "y":
                        continue
                invocations_json = [inv.to_json() for inv in invocations]
                save_json(invocations_json, response)
                print("Saved invocations to file '{}'.".format(response))
                print("To load these invocations at a later time, you may run\n\tpython3 {} {}".format(sys.argv[0], response))
                break
            else:
                print("Invalid file name {}".format(response))
        if not check_invocations(settings, invocations):
            input("Checking invocations failed. Press Return to continue at your own risk or CTRL+C to abort.")
        while True:
            response = input("Type 'run' to run the generated invocations or press Return to quit: ")
            if response == "run": run_invocations(settings, invocations)
            if response in ["", "run"]: break
            print("Unrecognized response '{}'".format(response))
    else:
        # run invocations (either all of them or a specific one)
        if not os.path.isfile(sys.argv[1]):
            raise AssertionError("Invocations file {} does not exist".format(sys.argv[1]))
        invocations_json = load_json(sys.argv[1])
        invocations = [Invocation(inv) for inv in invocations_json]
        print("Loaded {} invocations.".format(len(invocations)))
        if len(sys.argv) == 3:
            if not is_number(sys.argv[2]): raise AssertionError("Expected a number for second argument but got '{}' instead.".format(sys.argv[2]))
            selected_index = int(sys.argv[2])
            if selected_index not in range(0,len(invocations)): raise AssertionError("Second argument is out of range: got '{}' but index has to be at least 0 at less than {}".format(selected_index, len(invocations)))
            invocations = [invocations[selected_index]]    
            print("Selected invocation #{}: {}".format(selected_index, invocations[0].get_identifier()))
        check_invocations(settings, invocations)
        run_invocations(settings, invocations)
    
    
    

    
    