# Simulation-Based-Optimisation Engine

A POC of SBO acclerated by running multiple simulations concurrently using containerisation. Optimization is performed by the [PyMOO](https://github.com/anyoptimization/pymoo) library. 

Optimization is done by iteratively collecting outputs from the containerised simulations and performing analysis on the outputs. After each simulation iteration, the next set of inputs is determined by an optimisation algorithm such as the NSGA-II. These set of steps continue iteratively until convergence or a threshold of steps is met.

## Examples
An example is provided in the main_server, main_standalone files folder. Here, we optimise the outputs of a wafer frabication plant based on a simulation created by Klayton. There are three types of wafers being produced and three different inputs that affect the amount of wafers manufactured. The examples attempt to optimise all three types of wafers using the NSGA-II algorithm.

This example has the following arguments

- Number of workers - how many containers are concurrently running
- Number of generations - maximum number of generations
- Population size - population size how many inputs are considered in one generation
- Choice -- Kuberenetes or Argo Workflows as the simulation handler

Run standalone simulations with 10 workers, max generation of 10 and a population size of 100 using the Kubernetes as the pod creator.

`python3 main_standalone.py --workers 10 --n_gen 10 --pop_size 100 --choice kubernetes`

## Purpose

- Showcase how SBO throughput may be improved through the use of cloud computing, specifically containerisation and container orchestration
- Show how these techniques maybe applied to simulations that use files for communications or through an API