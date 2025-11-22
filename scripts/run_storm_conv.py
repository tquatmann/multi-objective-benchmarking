from internal.benchmark import *

settings = Settings()
all = [ b for b in get_all_benchmarks(settings, set_mdpmc_dir(os.path.join(settings.benchmark_dir(), "index.json"))) if b.is_multi_tradeoff() and b.is_prism() ]
print("Found {} multi-tradeoff PRISM benchmarks.".format(len(all)))
models = OrderedDict()
for benchmark in all:
    print("\t" + benchmark.get_identifier())
    models.setdefault(benchmark.get_directory(), []).append(benchmark)
    if not os.path.exists(os.path.join(benchmark.get_directory(), benchmark.get_prism_program_filename())):
        print("Error: PRISM file not found for benchmark '{}' at '{}'.".format(benchmark.get_identifier(), os.path.join(benchmark.get_directory(), benchmark.get_prism_program_filename())))
        exit(1)


for modelpath in sorted(models):
    # print("Converting model: {}".format(modelpath))
    jsonpath = os.path.join(modelpath, "index.json")
    index = load_json(jsonpath)
    for i in range(len(index["files"])):
        janifile = index["files"][i]["file"]
        prismfiles =  index["files"][i]["original-file"]
        stormconvargs = f"--prism {prismfiles[0]} --prop {prismfiles[1]} --tojani {janifile}"
        conversion = OrderedDict()
        conversion["tool"] = "Storm-conv"
        conversion["version"] = "1.11.1 (dev)"
        conversion["url"] = "https://www.stormchecker.org"
        conversion["command"] = "storm-conv " + stormconvargs
        index["files"][i]["conversion"] = conversion
        print("cd {}".format(modelpath))
        print(get_mdpmc_dir() + "/bin/storm-conv " + stormconvargs)
    save_json(index, jsonpath)
