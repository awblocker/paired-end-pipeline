#!python

# Load libraries
import sys, getopt

import pysam

import libPipeline

# Set constants
helpMsg ='''
SYNOPSIS
parseSAMOutput
parseSAMOutput [OPTIONS] SAMFILE
#
DESCRIPTION
parseSAMOutput.py

    Parses SAM alignments into paired-end read summaries.
    Prints results to stdout.

    If SAMFILE has a .sam or .SAM file extension, it is converted to BAM and all
    transformations (sorting, rmdup) are run via samtools.

    If SAMFILE has a .bam or .BAM file extension, conversion to BAM is skipped
    and all transformations are run via samtools.

    If SAMFILE has a .sorted.bam file extension (in any case), then sorting is
    skipped.

    If SAMFILE has a .unique.bam file extension, all samtools processing is
    skipped, including rmdup.

OPTIONS
--rmdup             Remove duplicate reads (reduces PCR effects)
-h/--help           Print help message and exit
'''

if __name__ == "__main__":
  # Set defaults
  rmdup = False

  # Parse arguments
  options, args = getopt.getopt(sys.argv[1:], 'h', ["help", "rmdup"])

  for opt, value in options:
    if opt in ("-h", "--help"):
      print >> sys.stderr, helpMsg
      sys.exit(2)
    elif opt == "--rmdup":
      rmdup = True
    else:
      print >> sys.stderr, "Error -- option %s not recognized" % opt
      sys.exit(1)

  # Parse arguments & options
  if len(args) > 0:
    alignmentPath = args[0]
  else:
    print >> sys.stderr, "Error -- need path to SAM file"
    sys.exit(1)

  libPipeline.processSAMOutput(alignmentPath, sys.stdout, rmdup=rmdup)

