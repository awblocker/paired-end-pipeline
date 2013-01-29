#!python

# Load libraries
import sys, getopt
import libPipeline

# Set constants
helpMsg ='''
SYNOPSIS
    parseBowtieOutput
    parseBowtieOutput [OPTIONS] [FILE]
    #
DESCRIPTION
    parseBowtieOutput.py

    Parses Bowtie alignments into paired-end read summaries.
    Prints results to stdout.

OPTIONS
    -h/--help           Print help message and exit
'''

if __name__ == "__main__":
    # Parse arguments
    options, args = getopt.getopt(sys.argv[1:], 'h', ["help"])
    
    for opt, value in options:
        if opt in ("-h", "--help"):
            print >> sys.stderr, helpMsg
            sys.exit(2)
        else:
            print >> sys.stderr, "Error -- option %s not recognized" % opt
            sys.exit(1)
    
    # Parse arguments & options
    if len(args) > 0:
        alignmentFilename = args[0]
        try:
            alignmentFile = open(alignmentFilename, 'rb')
        except:
            print >> sys.stderr, "Error -- could not open %s" % args[0]
            sys.exit(1)
    else:
        alignmentFile = sys.stdin
    
    libPipeline.processBowtieOutput(alignmentFile, sys.stdout)