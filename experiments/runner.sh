#!/bin/bash

# This script is used to run the application with different parameters
# and to collect the results.

# The first parameter is the number of workers to use.
# The second parameter is the number of generations.
# The third parameter is the population size per generation.

# read parameters from input file.
# The input file is a csv file with the following format:
# <number of workers>,<number of generations>,<population size per generation>

# The output file is a csv file with the following format:
# <number of workers>,<number of generations>,<population size per generation>,<time>

# The output file is named output.csv


inputs="argo_input.csv"
outputs="argo_output.csv"

# activate the virtual environment
. ../venv/bin/activate

# parse input file
while IFS=, read -r workers generations population
do
    echo "Running with $workers workers, $generations generations and $population population size per generation"
    # run the application
    time=$(python3 ../parallelisation.py --workers $workers --n_gen $generations --pop_size $population --choice kubernetes)
    # write the results to the output file
    echo "$workers,$generations,$population,$time" >> $outputs
done < $inputs

deactivate