#!python

# Load libraries
import sys
import getopt
import libPipeline

# Define constants
helpMsg = '''
SYNOPSIS
    convertToFASTQ
    convertToFASTQ [OPTIONS] [FILE]
    #
DESCRIPTION
    convertToFASTQ.py

    Converts Illumina-formatted data (one read per row) to FASTQ.
    Prints result to stdout.

OPTIONS
    -h/--help           Print help message and exit
'''


if __name__ == '__main__':
    # Parse arguments
    options, args = getopt.getopt(sys.argv[1:], 'h', ["help"])
    
    for opt, value in options:
        if opt in ("-h", "--help"):
            print >> sys.stderr, helpMsg
            sys.exit(2)
        else:
            print >> sys.stderr, "Error -- option %s not recognized" % opt
            sys.exit(1)
    
    if len(args) > 0:
        try:
            dataFile = open(args[0], "rb")
        except:
            print >> sys.stderr, "Error -- could not open %s" % args[0]
            sys.exit(1)
    else:
        dataFile = sys.stdin
    
    # Run conversion and output results to stdout
    libPipeline.convertIlluminaToFASTQ(dataFile, sys.stdout)
    
    sys.exit(0)
    