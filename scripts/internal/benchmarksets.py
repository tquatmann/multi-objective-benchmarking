from .utility import *

data = OrderedDict()
description = OrderedDict()

def load_benchmark_set(name : str, descr: str):
    filename = os.path.join(sys.path[0], "data/{}.json".format(name))
    bench_list = []
    if os.path.isfile(filename):
        bench_list = load_json(os.path.join(sys.path[0], "data/{}.json".format(name)))
    else:
        print("Warning: Benchmark set '{}' not found at '{}'.".format(name, filename))
    data[name] = bench_list
    description[name] = [descr, "({} benchmarks)".format(len(data[name]))]

def reload_benchmark_sets():
     load_benchmark_set("all", "All multi-objective benchmarks")
    # load_benchmark_set("qvbs", "All QVBS MDP/MA/PTA Benchmarks with reach-prob or exp-rew formula that storm and mcsta build in 3 minutes")
    # load_benchmark_set("gridworld", "gridworld benchmarks (not in qvbs)")
    # load_benchmark_set("mec-only", "benchmarks that contain mecs that (neither gridworld nor qvbs)")
    # load_benchmark_set("premise", "Runtime Monitoring Benchmarks (in explicit format)")
    #
    # load_benchmark_set("quickcheck", "A single QVBS instance to quickly check if the installation was successful.")
    # load_benchmark_set("community24", "The community set")
    # load_benchmark_set("hard-for-vi", "Benchmarks that are considered hard for value iteration")
    # load_benchmark_set("mec-subset", "benchmarks that are known to contain mecs")

reload_benchmark_sets()