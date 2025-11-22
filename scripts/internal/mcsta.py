from .benchmark import Benchmark
from .invocation import Invocation
from .execution import *
from .configuration import *

def get_name():
    """ should return the name of the tool"""
    return "mcsta"
    
    
def get_configurations():
    """ Returns the list of all tool configurations to benchmark """
    
    cfgs = []

    cfgs.append(Configuration(id="ii-abs-e3-g5", note="Interval iteration with epsilon=10^-3, absolute precision, and gamma=0.5", command="--mo-epsilon 1e-3 --mo-gamma 0.5 --lp-solver HiGHS"))
    cfgs.append(Configuration(id="ii-rel-e3-g5", note="Interval iteration with epsilon=10^-3, absolute precision, and gamma=0.5", command="--mo-epsilon 1e-3 --mo-gamma 0.5 --relative-mo-epsilon --lp-solver HiGHS"))
    # cfgs.append(Configuration(id="gurobi-vi-rel-e3-g5", note="(unsound) VI with epsilon=10^-3, absolute precision, and gamma=0.5", command="--alg ValueIteration --mo-epsilon 1e-3 --mo-gamma 0.5 --relative-mo-epsilon --lp-solver Gurobi"))

    return cfgs
    

def test_installation(settings, configuration = None):
    """
    Performs a quick check to test wether the installation works. 
    Returns an error message if something went wrong and 'None' otherwise.
    """
    mcsta_executable = set_mdpmc_dir(os.path.join(settings.mcsta_binary_dir(), "modest"))
    if not os.path.exists(mcsta_executable):
         return "Binary '{}' does not exist.".format(mcsta_executable)    
    command_line = mcsta_executable + " mcsta {}".format("" if configuration is None else configuration.command)
    try:
        test_out, test_time, test_code = execute_command_line(command_line, 10)
        if test_code != 0:
            return "Error while executing:\n\t{}\nNon-zero return code: '{}'.".format(command_line, test_code)
    except KeyboardInterrupt:
        return "Error: Execution interrupted."
    except Exception:
        return "Error while executing\n\t{}\n".format(command_line)

    
def is_benchmark_supported(benchmark : Benchmark, configuration : Configuration):
    """ Auxiliary function that returns True if the provided benchmark is  supported by mcsta."""
    return benchmark.has_janifile()


def get_invocation(settings, benchmark : Benchmark, configuration : Configuration, run_id : int):
    """
    Returns an invocation that invokes the tool for the given benchmark and the given storm configuration.
    It can be assumed that the current directory is the directory from which execute_invocations.py is executed.
    """
    general_arguments = "--unsafe -D -S Memory"
    
    invocation = Invocation()
    invocation.tool = get_name()
    invocation.configuration_id = configuration.identifier
    invocation.note = configuration.note
    invocation.benchmark_id = benchmark.get_identifier()
    invocation.run_id = run_id

    if is_benchmark_supported(benchmark, configuration):
        bdir = benchmark.get_portable_directory()
        mcsta_executable = os.path.join(settings.mcsta_binary_dir(), "modest")    
    
        janifile = benchmark.get_janifilename()
        par_defs = benchmark.get_open_parameter_def_string()
        benchmark_arguments = "mcsta {} --props {}".format(os.path.join(bdir, janifile), benchmark.get_property_name())
        if par_defs != "":
            benchmark_arguments += " -E " + par_defs
        
        # We set the precision to the required one (if given). Otherwise, we keep the default value.
        #if settings.goal_precision() is not None:
        #        general_arguments += " --width {}".format(float(settings.goal_precision()))
                
        invocation.add_command(mcsta_executable + " " + benchmark_arguments + " " + general_arguments + " " + configuration.command)
    else:
        invocation.note += " Benchmark not supported by mcsta."    
    return invocation



def get_result(log, benchmark : Benchmark):
    """
    Parses the tool result
    The returned value should be either 'true', 'false', a decimal number, or a fraction.
    """

    pos = log.find("+ Property {}".format(benchmark.get_property_name()))
    if pos < 0:
        return None
    result = log[pos:]
    # pos = log.find("Bounds:", pos)
    # if pos < 0:
    #     return None
    # pos = log.find("[", pos)
    # if pos < 0:
    #     return None
    # pos += len("[")
    # end_pos = log.find(",", pos)
    # if end_pos < 0:
    #     return None
    # result = log[pos:end_pos]
    return result
    
def get_MC_Time(log):
    """
    Tries to parse the model checking time (i.e. whatever happens after model building)
    """
    pos = log.find("+ Property")
    if pos < 0:
        return None
    pos = log.find("Time:", pos)
    if pos < 0:
        return None
    pos += len("Time:")
    end_pos = log.find(" s", pos)
    if end_pos < 0:
        return None
    num = log[pos:end_pos] # note that mcsta has rounded this to a multiple of 0.1 s
    return float(num)

    
def get_Solve_Time(log):
    """
    Tries to parse the solving time of the underlying solution method (model checking time without prob0/1, ... preprocessing)
    """
    vi = "+ Value iteration"
    lp = "+ Linear programming"
    if vi in log:
        method = vi
    elif lp in log:
        method = lp
    else:
        return None
    
    pos = log.find(method)
    if pos < 0:
        return None
    pos = log.find("Time:", pos)
    if pos < 0:
        return None
    pos += len("Time:")
    end_pos = log.find(" s", pos)
    if end_pos < 0:
        return None
    num = log[pos:end_pos] # note that mcsta has rounded this to a multiple of 0.1 s
    return float(num)
    
def get_Build_Time(log):
    """
    Tries to parse the model building time
    """
    pos = log.find("+ State space exploration")
    if pos < 0:
        return None

    pos_expl = log.find("Time (exploration):", pos)
    if pos_expl < 0:
        return None
    pos_expl += len("Time (exploration):")
    end_pos_expl = log.find(" s", pos_expl)
    if end_pos_expl < 0:
        return None

    pos_merge = log.find("Time (merging):", pos)
    if pos_merge < 0:
        return None
    pos_merge += len("Time (merging):")
    end_pos_merge = log.find(" s", pos_merge)
    if end_pos_merge < 0:
        return None

    num_expl = float(log[pos_expl:end_pos_expl]) # note that mcsta has rounded this to a multiple of 0.1 s
    num_merge = float(log[pos_merge:end_pos_merge]) # note that mcsta has rounded this to a multiple of 0.1 s
    return num_expl + num_merge

def is_not_supported(logfile):
    """
    Returns true if the logfile contains error messages that mean that the input is not supported.
    """
    # if one of the following error messages occurs, we are sure that the model is not supported.
    known_messages = []
    #known_messages.append("The model type Markov Automaton is not supported by the dd engine.")
    for m in known_messages:
        if m in logfile:
            return True
    
    return False


def is_expected_error(logfile):
    """
    Returns true if the logfile contains a known error message that is to be expected. This is to detect "weird" errors when processing the logfiles
    """
    known_messages = []
    # known_messages.append("The linear program is infeasible.")
    # known_messages.append("The linear programming solver encountered a numerical failure.")
    # known_messages.append("The linear program is unbounded.")
    # known_messages.append("The linear programming solver did not find an optimal solution.")
    # known_messages.append("The linear program is infeasible or unbounded.")
    # known_messages.append("The linear programming solver encountered an accuracy error.")
    # known_messages.append("The linear program is degenerative.")
    # known_messages.append("Could not load native")
    # known_messages.append("Found invalid native")
    # known_messages.append("Could not initialise native")
    # known_messages.append("Error solving the linear program.")
    # known_messages.append("Error while using linear programming")
    # known_messages.append("library encountered an error.")
    # known_messages.append("The linear programming solver terminated before finding an optimal solution.")
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
    known_messages.append("The linear programming solver ran out of memory.")
    known_messages.append("Out of memory")
    # known_messages.append("ERROR: The program received signal 11")
    for m in known_messages:
        if m in logfile:
            return True
    # if there is no error message and no result is produced, we assume out of memory.
    return ": error:" not in logfile and "Error:" not in logfile
