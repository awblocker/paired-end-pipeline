#!python

# Load libraries
import numpy as np
import sys, csv
import getopt
import libPipeline

HELP_MSG = '''
SYNOPSIS
    readsToChromCounts
    readsToChromCounts [OPTIONS] [FILE]
    #
DESCRIPTION
    readsToChromCounts.py

    Parses Bowtie alignments into paired-end read summaries.
    Prints results to stdout.

OPTIONS
    -h/--help           Print help message and exit
'''

if __name__ == "__main__":
    # Set defaults
    randomize = False
    seed      = 20081025
    
    # Parse arguments
    options, args = getopt.getopt( sys.argv[1:], "hr",
                                   ["help","randomize","seed="])
    
    for opt, value in options:
        if opt in ('-h', "--help"):
            sys.stderr.write(HELP_MSG)
            sys.exit(2)
        elif opt in ('-r', "--randomize"):
            randomize = True
        elif opt in ("--seed",):
            seed = int(value)
        else:
            print >> sys.stderr, "Error: unknown option %s" % opt
            sys.exit(1)
            
    if len(args) > 0:
        dataFilename = args[0]
        dataFile = args[0]
        try:
            dataFile = open(dataFilename, 'rb')
        except:
            print >> sys.stderr, "Error -- could not open %s" % args[0]
            sys.exit(1)
    else:
        dataFile = sys.stdin
    
    np.random.seed(seed)
    
    # Tabulate read centers per base pair
    libPipeline.readsToCounts(dataFile, sys.stdout, randomize)
    
    sys.exit(0)
