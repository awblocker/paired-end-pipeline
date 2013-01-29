#!/bin/bash

# Assumes data is already FASTQ formatted with Solexa > v1.3 quality
# $1 is index prefix, $2 is first FASTQ file, and $3 is second FASTQ for
# paired-end reads

MIN_LENGTH=100
MAX_LENGTH=300
MAX_MISMATCHES=2
#
N_THREADS=12

time bowtie --solexa1.3-quals -q \
    -n $MAX_MISMATCHES --best -M 1 \
    -I $MIN_LENGTH -X $MAX_LENGTH \
    --threads $N_THREADS \
    -S \
    $1 \
    -1 $2 -2 $3

