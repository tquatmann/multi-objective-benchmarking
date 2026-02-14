Artifact for Paper: Tools and Algorithms for Sound Multi-Objective Probabilistic Model Checking
===

by Arnd Hartmanns, Tim Quatmann, Mark van Wijk

# Abstract

The artifact contains the two multi-objective probabilistic model checking tools mcsta (part of The Modest Toolset) and Storm using a multi-platform Docker image for convenient installation.
Benchmark models and benchmarking scripts are provided to reproduce all experiments from the paper.
Representative subsets of experiments are included to assess reproducibility within a reasonable time frame.

> **The artifact is available at [Zenodo](https://doi.org/10.5281/zenodo.18604532).**

# License

Mcsta is part of The Modest Toolset, which is licensed under the license located at `tools/mcsta/License.txt`.
Storm is licensed under the license located at `tools/storm/LICENSE.txt`.
All other contents  are licensed under the [CC-BY 4.0](http://creativecommons.org/licenses/by/4.0/) license.

# Requirements

- We assume a Linux or MacOS host system (both x86 and ARM are supported). Windows might be possible, but it has not been tested and likely requires some manual adaptations of our scripts.
- Docker needs to be installed. The `Use containerd for pulling and storing images` option should be enabled in the Docker settings to support the provided multi-platform image. Further information below.

# Installation and Smoke Test

The artifact is based on a single Docker image containing pre-built binaries of the two tools `mcsta` and `Storm` in the same version as exercised in the paper.

## Prerequisites

- Install [Docker](https://docs.docker.com/get-started/get-docker/). The artifact has been tested with Docker Desktop version `29.2.0`.
- In the Docker settings, ensure that the `Use containerd for pulling and storing images` option is enabled. This is necessary to support the provided [multi-platform image](https://docs.docker.com/build/building/multi-platform/).
- Download the file `artifact.zip` from [Zenodo](https://doi.org/10.5281/zenodo.18604532) and unzip it at a convenient location. Throughout this document, `$ARTIFACT_DIR` refers to the path leading to the unzipped directory, i.e., a copy of this Readme is located at `$ARTIFACT_DIR/README.md`.

## Install and Test Storm

Execute `$ARTIFACT_DIR/run_docker.sh`.
This will load the `mopmctools` Docker image (if it is not already loaded) and run the container.
When successful, something similar to the following is shown:

```
Directory of script is $ARTIFACT_DIR
Docker version 29.2.0, build 0b9d198
Detected x86 architecture. Using modest for x86.
Loading Docker image.
Loaded image: mopmctools:latest

Running mopmctools Docker container.
Type 'exit' to exit from docker...
The Modest Toolset (www.modestchecker.net), version v3.1.420-gdeeaa8e34+deeaa8e349db7c966267a21eddf603aeb3d612f8.
Storm 1.11.1 (dev)
root@2c99f5c0a63f:/opt/artifact#
```

One can now run a quick check (inside the container):

```
cd quickcheck
./run.sh
```

This invokes `mcsta` and `storm` on a single benchmark instance in all five configurations from Fig. 6 of the paper. The produced log files can be found and inspected in `$ARTIFACT_DIR/quickcheck/logs/`.
The log files (and the output of the `run.sh` script) should contain the expected model checking result for all five runs, which for `mcsta` is:

```
+ multi
WSO instances:       2
  Time:                0.0 s
  Under Approximation: ∩{-1x + -0y <= -1, -0x + -1y <= -135.25}
  Over Approximation:  ∩{-1x + -0y <= -1, -0x + -1y <= -135.25}
```

and for `Storm` is:

```
Result (for initial states): 
Underapproximation of achievable values: Polytope with 2 Halfspaces:
   (        -1,          0) * x <= -1
   (         0,         -1) * x <= -135.25
```


# Reproducing the Paper Experiments

## Subsets
Running the experiments as in the paper (i.e., 261 instances on 25 different tool invocations with a 2700 second time limit) takes approximately 500-600 hours.
To evaluate reproducibility within a reasonable timespan, we provide 4 different subsets with different time limits:

- `subset-small`: Only selects those benchmark instances where (in our experiments) one of the tools was able to answer the query within x=5 seconds.
  Imposes a time limit of y=7 seconds for each run.
  Considers only 3 (instead of 6) different values for epsilon and gamma (cf. Figures 7 and 8).
  Running this set should take less than 1 hour.
- `subset-medium`: As above with x=30 seconds and y=40 seconds.
  Running this set takes approximately 4 hours.
- `subset-large`: As above with x=300 seconds and y=400 seconds.
  Running this set takes approximately 30 hours.
- `all`: All benchmark instances in all configurations as in the paper. Imposes a time limit of 2700 seconds for each run.

## Running the Experiments

To run, e.g., the `subset-medium` set, start the Docker using `$ARTIFACT_DIR/run_docker.sh` as described above and execute

```
cd experiments
python3 ../scripts/run.py subset-medium.json
```

When finished, the produced log files can be postprocessed using

```
python3 ../scripts/postprocess.py logs subset-medium
```

This command produces a subfolder `subset-medium`, which contains:

- `table/table.html`: A browsable HTML table allowing to conveniently inspect the raw data (run times, log files)
- `table/plots.tex`: A LaTeX document that can be compiled with `pdflatex plots.tex` (not included in the Docker) to reproduce Figures 6 to 8 from the paper.


# Reviewing the Experimental Results from the Paper

The directory `$ARTIFACT_DIR/paper_results/` contains the logfiles and derived data as reported in the paper.


# Custom Queries Multi-Objective PMC Queries

## Model and Query Specification in JANI

To check custom multi-objective queries with `mcsta` and `storm`, a model and property description in [JANI](https://www.jani-spec.org/) is required.

A JANI file can, e.g., be obtained from a [PRISM Model](https://www.prismmodelchecker.org/manual/)
and a multi-objective query using PRISM-style syntax. Such a query may have the following syntax:

```
"name": multi(R{"rounds"}min=? [ F "done" ], R{"time"}min=? [ F "done" ], Pmax=? [ F "success"]);
```

- `name` is the name of the query.
- `R{"rounds"}min=? [ F "done" ]` is the first objective that minimizes the expected total reward for the reward model `"rounds"` until reaching the state label`"done"`.
- `R{"time"}min=? [ F "done" ]` is the second objective that minimizes the expected total reward for the reward model `"time"` until reaching the state label`"done"`.
- `Pmax=? [ F "success"]` is the third objective that maximizes the probability to eventually reach the state label`"success"`.

Given a PRISM model file `model.prism` and a PRISM property file`mo_query.props`, a JANI model `model.jani` can be generated by running (inside the Docker):

```
/opt/storm/build/bin/storm-conv --prism model.prism --prop mo_query.props --tojani model.jani
```

Example models and queries can be found in `$ARTIFACT_DIR/qcomp/benchmarks/`.


## Running mcsta and Storm

Start the Docker: `$ARTIFACT_DIR/run_storm.sh`.
In the following, we assume `/opt/artifact` to be the current working directory (within the Docker).
From here, mcsta can be run via `./bin/Modest mcsta`.
Storm can be executed via `./bin/storm`.


### mcsta

The following command invokes mcsta on a JANI model, sets the model constant `delay=3`, and checks the property `multi`

```
./bin/modest mcsta ./qcomp/benchmarks/mdp/firewire_abst/firewire_abst.jani --props multi -E delay=3 
```

Run `./bin/modest mcsta --help` to get more info on available command line switches.
We list the most relevant options for this artifact:

- Model and Property input:
  * `--props name` selects property from JANI file with name `name`.
  * `-E X=1,Y=2` specifies open constants in the model file.
  * `--unsafe`  generates faster code for state-space exploration by omitting some runtime checks.
  * `-S Memory` writes the model into memory (instead of disk).
- Model Checking
  * `--alg ValueIteration` use value iteration as the single-objective solver
  * `--alg IntervalIteration` use interval iteration as the single-objective solver
  * `--mo-epsilon 1e-3` sets the value for epsilon to 10^-3
  * `--mo-gamma 0.5` sets the value for gamma to 0.5
  * `--lp-solver HiGHS` uses HiGHS as LP solver, which is faster than the default.
- Additional output
  * `-D` collects diagnostic information during model checking.


### Storm

The following command invokes Storm on a JANI model, sets the model constant `delay=3`, and checks the property `multi`

```
./bin/storm --jani ./qcomp/benchmarks/mdp/firewire_abst/firewire_abst.jani --janiproperty multi --constants delay=3
```

Run `./storm/build/bin/storm --help` or `./storm/build/bin/storm --help all` to get more info on available command line switches. We list the most relevant options for this artifact:

- Model and Property input:
  * `--prism file.prism` reads the input model from `file.prism` in the PRISM modelling language.
  * `--prop file.props name` reads the property specification from `file.props` (using PRISM-like syntax) and selects the query with the name `name`. If `name` is omitted, all queries in the file are selected.
  * `--jani file.jani` reads the input model from `file.jani` in the JANI language.
  * `--janiproperty name` selects property from JANI file with name `name`.
  * `--constants X=1,Y=2` specifies open constants in the model file or property file.
- Model checking:
  * `--multiobjective:precision 1e-3` sets the precision of the Pareto front approximation (epsilon).
  * `--multiobjective:approxtradeoff 0.75` sets the tradeoff for Pareto front approximation (gamma)
  * `--sound` use Interval Iteration (instead of Value Iteration) as the single-objective solver.
  * `--exact` use Policy Iteration over rationals (instead of Value Iteration) as the single-objective solver.
- Additional output:
  * `-tm` prints time and memory consumption of the computation.
  * `--statistics` prints more information regarding the input query and analysis statistics.


# Tool Details

The directory `$ARTIFACT_DIR/tools/mcsta` contains pre-built binaries for `mcsta`, which is part of [The Modest Toolset](https://www.modestchecker.net)

The directory `$ARTIFACT_DIR/tools/storm/` contains the source code of our implementation in [Storm](https://stormchecker.org).
Most relevant C++ source code files are in `src/storm/modelchecker/multiobjective/`

Running the script `ARTIFACT_DIR/tools/build_docker.sh` (re-)builds the Docker image and saves it as `mopmctools_docker.tar.gz`.
