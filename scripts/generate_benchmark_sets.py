from internal.benchmark import *
from internal.utility import *
from internal import benchmarksets
import os
import sys
from internal.processlogs import *

def is_considered(benchmark):
    if not any([benchmark.is_multi_tradeoff()]): return False
    # if benchmark.get_model_short_name() in ["repudiation_malicious", "repudiation_honest"]: return False # not supported by storm
    return True

def save_set(benchmarks, setname):
    print("Saving set '{}' with {} benchmarks".format(setname, len(benchmarks)))
    save_json([ benchmark if isinstance(benchmark, str) else benchmark.get_identifier() for benchmark in benchmarks], os.path.join(sys.path[0], "data", setname + ".json"))



if __name__ == "__main__":
    print("Benchmarking tool.")
    print("This script determines the considered benchmark sets.")
    print("Usages:")
    print("python3 {} path/to/first/logfiles/ reads from log file directories and determines benchmark sets '".format(sys.argv[0]))
    print("")
    if (len(sys.argv) == 2 and sys.argv[1] in ["-h", "-help", "--help"]):
        exit(1)

    settings = Settings()

    # logdirs = sys.argv[1:]
    # if len(logdirs) == 0:
    #     print("No log directories given. Exiting.")
    #     exit(1)
    #
    # print("Selected log dir(s): {}".format(", ".join(logdirs)))
    # print("")
    # groups_tools_configs = get_all_groups_tools_configs(logdirs) # group names are derived from the directory names
    # exec_data = gather_execution_data(settings, logdirs, groups_tools_configs)  # Group -> Tool -> Config -> Benchmark -> [Data array]
    #
    # # get benchmarks with long build time for either mcsta or storm
    # long_build_time_ids = set()
    # for g,t,c in groups_tools_configs:
    #     if "exact" in c: continue
    #     if t not in exec_data[g]: continue
    #     if c not in exec_data[g][t]: continue
    #     for b in exec_data[g][t][c]:
    #         if len(exec_data[g][t][c][b]) == 0: continue
    #         res_data = exec_data[g][t][c][b][0]
    #         buildtime = None
    #         if "model-building-time" in res_data:
    #             buildtime = res_data["model-building-time"]
    #         if buildtime is None and t == storm.get_name(): # no build time in mcsta might also mean timeout during model checking
    #             long_build_time_ids.add(b)
    #         elif buildtime is not None and buildtime > 300.0:
    #             long_build_time_ids.add(b)
    # save_set(sorted(long_build_time_ids), "long-build-time")

    # get all supported benchmarks
    all = [ b for b in get_all_benchmarks(settings, set_mdpmc_dir(os.path.join(settings.benchmark_dir(), "index.json"))) if is_considered(b)]
    # ... but ignore those with long build times
    # all = [ b for b in all if b.get_identifier() not in long_build_time_ids]

    # all_jani = [ b for b in all if b.has_janifile()]
    #
    # premise = [ b for b in all if is_premise(b)]
    # gridworld = [ b for b in all if is_gridworld(b)]
    # qvbs = [ b for b in all if is_qvbs(b)]
    # mec_only = [ b for b in all if is_mec_only(b)]

    quickcheck = [ get_benchmark_from_id(settings, "firewire.false-3-800.multi_pos")]

    # assert that we indeed have all benchmarks
    # all_classified_ids = [b.get_identifier() for b in premise + gridworld + qvbs + mec_only]
    # unused_ids = [b.get_identifier() for b in all if b.get_identifier() not in all_classified_ids]
    # if len(all) != len(all_classified_ids):
    #     print("Not all benchmarks classified. Unused IDs:\n\t\"{}\"".format("\",\n\t\"".join(unused_ids)))
    #     print("{} benchmarks found, {} benchmarks classified, {} missing".format(len(all), len(all_classified_ids), len(all) - len(all_classified_ids)))

    save_set(all, "all")
    save_set(quickcheck, "quickcheck")


