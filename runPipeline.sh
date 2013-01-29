#!/bin/bash

# Script to run entire pipeline on given input files
# Detects if files are already FASTQ by checking extensions
# Detects single- vs. paired-end by checking number of inputs

# Arguments are: PREFIX FILE1 [FILE2]

# Check if single- or paired-end data
SINGLE_END=0
if [ $# -lt 3 ]
then
    SINGLE_END=1
fi

# Iterate over files, converting to FASTQ as needed
RAW_FILES=( $@ )
FASTQ_FILES=( )
for (( i=1; i < $#; i++ ))
do
    FILE=${RAW_FILES[i]}
    BASE=${FILE%.*}
    EXT=${FILE##*.}

    # Check if file is already FASTQ
    if [ \( $EXT = "fq" \) -o \( $EXT = "fastq" \) ]
    then
        FASTQ_FILES[i]=FILE
        continue
    fi

    # If not, convert it to FASTQ
    FASTQ_FILES[i]=${BASE}.fastq
    convertToFASTQ.py $FILE > ${FASTQ_FILES[i]}
done

# Run Bowtie on FASTQ files

if [ $SINGLE_END = "0" ]

else

fi

