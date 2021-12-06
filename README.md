# Simulation-Based-Optimisation

SBO done using [Argo Workflow](https://github.com/projectmesa/mesa) as a Task Scheduler

Optimization is done by iteratively collecting outputs from simulations and performing analysis on the outputs. After each simulation iteration, the next set of inputs is determined by our optimizer [PyMOO](https://github.com/anyoptimization/pymoo). These set of steps continue iteratively until convergence or a threshold of steps is met.

## Examples

An example is provided in the 'argo' folder. Here, we simulate the population fluctuations of wolves and sheep as implemented in [MESA](https://github.com/projectmesa/mesa). We try to optimise for using the smallest amount of wolves and fertilizer to keep the sheep population within a set constraint.

`argo submit -n argo --watch argo/optimiser.yaml`
