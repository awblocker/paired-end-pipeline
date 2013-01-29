#!python

# Import packages
import libPipeline
import sys
import getopt

helpMsg = '''
SYNOPSIS
    buildReadLengthDist
    buildReadLengthDist [OPTIONS] [FILE]
    #
DESCRIPTION
    buildReadLengthDist.py

    Builds distribution of read lengths from file of raw paired-end data.
    Prints distribution in two-column format to stdout.
    First column is length, second is number of reads with that length.

OPTIONS
    -o/--offset=        Offset (number of base pairs read per end);
                        defaults to 35bp
    -h/--help           Print help message and exit
'''

if __name__=="__main__":
    # Set default parameters
    offset = 0
    
    # Parse arguments
    options, args = getopt.getopt(sys.argv[1:], "o:h",
                                  ["offset=","help"])
    #
    for opt, value in options:
        if opt in ('-h', "--help"):
            print >> sys.stderr, helpMsg
            sys.exit(2)
        elif opt in ('-o', "--offset"):
            offset = int(value)
        else:
            print >> sys.stderr, "Error -- option %s not recognized" % opt
            sys.exit(1)
    #
    if len(args) < 1:
        dataFile = sys.stdin
    else:
        rawDataFilename = args[0]
        try:
            dataFile = open(rawDataFilename, "rb")
        except:
            print >> sys.stderr, "Error -- could not open %s" % rawDataFilename
            sys.exit(1)
    
    # Build distribution and write to stdout
    libPipeline.getReadLengthDist(dataFile, sys.stdout, offset)
    
    sys.exit(0)
