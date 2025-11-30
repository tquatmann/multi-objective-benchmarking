from .benchmark import Benchmark
from .invocation import Invocation
from .execution import *
from .configuration import *

def get_name():
    """ should return the name of the tool """
    return "Storm"

# This token can be used in a configuration command and will be replaced by some (integer) seed value (allowing to determinize random executions)
RANDOM_SEED_TOKEN = "<%SEED%>"

def test_installation(settings, configuration = None):
    """
    Performs a quick check to test wether the installation works. 
    Returns an error message if something went wrong and 'None' otherwise.
    """
    storm_executable = set_mdpmc_dir(os.path.join(settings.storm_binary_dir(), "storm"))
    if not os.path.exists(storm_executable):
         return "Binary '{}' does not exist.".format(storm_executable)    
    command_line = storm_executable + " {}".format("" if configuration is None else configuration.command)
    command_line = command_line.replace(RANDOM_SEED_TOKEN, str(get_seed(0)))
    try:
        test_out, test_time, test_code = execute_command_line(command_line, 10)
        if test_code != 0:
            return "Error while executing:\n\t{}\nNon-zero return code: '{}'.".format(command_line, test_code)
    except KeyboardInterrupt:
        return "Error: Execution interrupted."
    except Exception:
        return "Error while executing\n\t{}\n".format(command_line)

    
def is_benchmark_supported(benchmark : Benchmark, configuration : Configuration):
    """ Auxiliary function that returns True if the provided benchmark is not supported by Storm and no known external conversion tool can help."""
    # Storm does not support CTMCs with infinite state-spaces
    if benchmark.is_prism_inf() and benchmark.is_ctmc():
        return False
    if "prism" in configuration.identifier and not (benchmark.is_prism() or benchmark.is_prism_ma()):
        return False
    return True


def get_configurations():
    cfgs = []
    # vi
    cfgs.append(Configuration(id="topovi-abs-e3-g5", note="(unsound) topological VI with epsilon=10^-3, absolute precision, and gamma=0.5", command="--multiobjective:precision 1e-3 abs"))
    cfgs.append(Configuration(id="prism-topovi-abs-e3-g5", note="prefer prism models, (unsound) topological VI with epsilon=10^-3, absolute precision, and gamma=0.5", command="--multiobjective:precision 1e-3 abs"))
    # ii
    cfgs.append(Configuration(id="topoii-abs-e3-g5", note="(sound) topological II with epsilon=10^-3, absolute precision, and gamma=0.5", command="--multiobjective:precision 1e-3 abs --sound"))
    cfgs.append(Configuration(id="ii-abs-e3-g5", note="(sound) II with epsilon=10^-3, absolute precision, and gamma=0.5", command="--multiobjective:precision 1e-3 abs --sound --minmax:method ii --eqsolver native --native:method ii"))
    # different gammas
    cfgs.append(Configuration(id="topoii-abs-e3-g2", note="(sound) topological II with epsilon=10^-3, absolute precision, and gamma=0.2", command="--multiobjective:precision 1e-3 abs --sound --multiobjective:approxtradeoff 0.2"))
    cfgs.append(Configuration(id="topoii-abs-e3-g8", note="(sound) topological II with epsilon=10^-3, absolute precision, and gamma=0.8", command="--multiobjective:precision 1e-3 abs --sound --multiobjective:approxtradeoff 0.8"))
    # different precisions
    cfgs.append(Configuration(id="topoii-abs-e2-g5", note="(sound) topological II with epsilon=10^-2  absolute precision, and gamma=0.5", command="--multiobjective:precision 1e-2 abs --sound"))
    cfgs.append(Configuration(id="topoii-abs-e4-g5", note="(sound) topological II with epsilon=10^-4, absolute precision, and gamma=0.5", command="--multiobjective:precision 1e-4 abs --sound"))
    cfgs.append(Configuration(id="topoii-abs-e5-g5", note="(sound) topological II with epsilon=10^-5, absolute precision, and gamma=0.5", command="--multiobjective:precision 1e-5 abs --sound"))
    return cfgs


def get_invocation(settings, benchmark : Benchmark, configuration : Configuration, run_id : int):
    """
    Returns an invocation that invokes the tool for the given benchmark and the given storm configuration.
    It can be assumed that the current directory is the directory from which execute_invocations.py is executed.
    """
    general_arguments = "--timemem --verbose" # Prints some timing and memory information
    
    invocation = Invocation()
    invocation.tool = get_name()
    invocation.configuration_id = configuration.identifier
    invocation.note = configuration.note
    invocation.benchmark_id = benchmark.get_identifier()
    invocation.run_id = run_id
    
    if is_benchmark_supported(benchmark, configuration):
        bdir = benchmark.get_portable_directory()
        storm_executable = os.path.join(settings.storm_binary_dir(), "storm")

        if ("prism" in configuration.identifier and benchmark.is_prism() or benchmark.is_prism_ma()) and not benchmark.is_pta():
            benchmark_arguments = "--prism {} --prop {} {}".format(os.path.join(bdir, benchmark.get_prism_program_filename()), os.path.join(bdir, benchmark.get_prism_property_filename()), benchmark.get_property_name())
            if benchmark.get_open_parameter_def_string() != "":
                benchmark_arguments += " --constants {}".format(benchmark.get_open_parameter_def_string())
            if benchmark.is_ctmc():
                benchmark_arguments += " --prismcompat"
                invocation.note += " Use `--prismcompat` to ensure compatibility with prism benchmark."
        elif benchmark.is_drn():
            benchmark_arguments = "--explicit-drn {} --prop {} {}".format(os.path.join(bdir, benchmark.get_drn_filename()), os.path.join(bdir, benchmark.get_drn_property_filename()), benchmark.get_property_name())
            assert(benchmark.get_open_parameter_def_string() == "")
        else:
            # For jani input, it might be the case that preprocessing is necessary using moconv
            janifile = benchmark.get_janifilename()
            par_defs = benchmark.get_open_parameter_def_string()
            moconv_options = []
            if "nondet-selection" in benchmark.get_jani_features():
                moconv_options.append("--remove-disc-nondet")
                invocation.note += " Used moconv to handle currently unsupported jani feature 'nondet-selection'."
            if benchmark.is_pta():
                if benchmark.get_model_short_name() in ["repudiation_honest", "repudiation_malicious", "csma-pta", "csma_abst-pta"]:
                    invocation.note += " Unsupported PTA Benchmark."
                else:
                    moconv_options.append("--digital-clocks")
                    if benchmark.load_jani_file()["type"] == "sta":
                        moconv_options.append(" --unroll-distrs")
                    invocation.note += " Used moconv to convert the PTA to an MDP using digital-clocks semantics."
            if len(moconv_options) != 0:
                janifile_split = os.path.splitext(janifile)
                moconvoutfilename = "converted_{}.{}{}".format(janifile_split[0], par_defs, janifile_split[1])
                moconvoutfile = os.path.join(bdir, moconvoutfilename)
                if par_defs != "":
                    moconv_options.append(" --experiment " + par_defs)
                    par_defs = ""
                if not os.path.isfile(set_mdpmc_dir(moconvoutfile)):
                    moconv_command = "moconv {} {} --output {} --overwrite\n".format(os.path.join(bdir, janifile), " ".join(moconv_options), moconvoutfile)
                    with open("moconv.sh", 'a') as moconvscript :
                        moconvscript.write(moconv_command)
                    print("Required moconv call appended to file 'moconv.sh'")
                janifile = moconvoutfilename
            benchmark_arguments = "--jani {} --janiproperty {}".format(os.path.join(bdir, janifile), benchmark.get_property_name())
            if par_defs != "":
                benchmark_arguments += " --constants " + par_defs
        cfg_cmd = configuration.command.replace(RANDOM_SEED_TOKEN, str(get_seed(run_id)))
        invocation.add_command(storm_executable + " " + benchmark_arguments + " " + cfg_cmd + " " + general_arguments)
    else:
        invocation.note += " Benchmark not supported by Storm."    
    return invocation



def get_result(log, benchmark : Benchmark):
    """
    Parses the tool result
    """

    pos = log.find("Model checking property \"{}\":".format(benchmark.get_property_name()))
    if pos < 0:
        return None
    pos = log.find("Result (for initial states): ", pos)
    if pos < 0:
        return None
    pos = pos + len("Result (for initial states): ")
    end_pos = log.find("Time for model checkin", pos)
    result = log[pos:end_pos].strip()
    pos_appr = result.find("(approx. ")
    if pos_appr >= 0:
        result = result[:pos_appr]
    return result
    
def get_MC_Time(logfile):
    """
    Tries to parse the model checking time
    """
    pos = logfile.find("Time for model checking: ")
    if pos >= 0:
        pos += len("Time for model checking: ")
        pos2 = logfile.find("s.", pos)
        num = logfile[pos:pos2]
        return float(num)
    return None

def is_bisimulation_used(logfile):
    """
    Tries to parse the bisimulation usage
    """
    return "-bisim " in logfile or "--bisimulation" in logfile

def get_preprocessing_time(logfile):
    """
    Tries to parse the model checking time
    """
    pos = logfile.find("Time for model preprocessing: ")
    if pos >= 0:
        pos += len("Time for model preprocessing: ")
        pos2 = logfile.find("s.", pos)
        num = logfile[pos:pos2]
        return float(num)
    return None

def get_Solve_Time(logfile):
  """
  Tries to parse the solving time of the underlying solution method (model checking time without prob0/1, ... preprocessing)
  """
  pos = logfile.find("Time for model solving: ")
  if pos >= 0:
      pos += len("Time for model solving: ")
      pos2 = logfile.find("s.", pos)
      num = logfile[pos:pos2]
      return float(num)
  return None
    
def get_Build_Time(logfile):
    """
    Tries to parse the model building time
    """
    pos = logfile.find("Time for model construction: ")
    if pos >= 0:
        pos += len("Time for model construction: ")
        pos2 = logfile.find("s.", pos)
        num = logfile[pos:pos2]
        return float(num)
    return None

def get_nontriv_mec_percentage(logfile):
    """
    Tries to parse the percentage of MEC states
    """
    pos1 = logfile.find("are trivial, i.e., consist of a single state. ")
    if pos1 >= 0:
        pos2 = logfile.find("%) are on a non-trivial mec.", pos1)
        pos1 = logfile.rfind("(", pos1, pos2) + 1
        num = logfile[pos1:pos2]
        return float(num)
    return None


def get_Acyclic(logfile):
    """
    Tries to find information whether or not the model is acyclic. Returns None if the information was not found
    """
    if "##Acyclic" in logfile:
        return True
    elif "##Cyclic" in logfile:
        return False
    else:
        return None
    
      
def get_NonTriv_Scc_States(logfile):
    """
    Tries to parse the number of non-trivial scc states from the logfile
    """
    pos = logfile.find("Number of states in non-trivial SCC: ")
    if pos >= 0:
        pos += len("Number of states in non-trivial SCC: ")
        pos2 = logfile.find(".", pos)
        num = logfile[pos:pos2]
        return int(num)
    return None

def is_not_supported(logfile):
    """
    Returns true if the logfile contains error messages that mean that the input is not supported.
    """
    # if one of the following error messages occurs, we are sure that the model is not supported.
    known_messages = []
    known_messages.append("The model type Markov Automaton is not supported by the dd engine.")
    known_messages.append("The model type CTMC is not supported by the dd engine.")
    known_messages.append("Cannot build symbolic model from JANI model whose system composition that refers to the automaton ")
    known_messages.append("Cannot build symbolic model from JANI model whose system composition refers to the automaton ")
    known_messages.append("The symbolic JANI model builder currently does not support assignment levels.")
    known_messages.append("repudiation") # Unsupported PTA benchmark
    known_messages.append("csma_abst") # Unsupported PTA benchmark
    known_messages.append("csma-pta") # Unsupported PTA benchmark
    known_messages.append("rectangle-tireworld.30.jani.gz") # too large jani benchmark
    for m in known_messages:
        if m in logfile:
            return True
            
    return False


def is_expected_error(logfile):
    """
    Returns true if the logfile contains a known error message that is to be expected.
    """
    known_messages = []
    for m in known_messages:
        if m in logfile:
            return True
    return False

def is_memout(logfile):
    """
    Returns true if the logfile indicates an out of memory situation.
    Assumes that a result could not be parsed successfully.
    """
    known_messages = []
    known_messages.append("Maximum memory exceeded.")
    known_messages.append("BDD Unique table full")
    known_messages.append("ERROR: The program received signal 11")
    known_messages.append("Unable to optimize Gurobi model (Out of memory, error code 10001).")
    for m in known_messages:
        if m in logfile:
            return True
    # if there is no error message and no result is produced, we assume out of memory.
    return "ERROR" not in logfile
