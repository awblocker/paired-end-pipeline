'''
Created on Apr 8, 2011

@author: awblocker
'''

# Load libraries
import re
import sys
import StringIO
import csv
import os
import time

import numpy as np
import pysam

# Define constants
ILLUMINA_REGEXP_PAIRED = re.compile(r"(.*#0/[12]):([^:]*):([^:]*)")
FASTQ_PATTERN = r"@\1\n\2\n+\1\n\3"

BOWTIE_FIELDS = ( "name", "strand", "refseq", "offset", "readseq",
                 "readqual", "nvalid", "mismatches" )
BOWTIE_DELIM = '\t'

ID_RE = re.compile(r"(.+)#.+")

OUTPUT_FIELDS = ("chromosome", "strand", "start", "end", "center", "length",
                 "nvalid")
HEADER = BOWTIE_DELIM.join(OUTPUT_FIELDS) + os.linesep

OUTPUT_FORMAT = BOWTIE_DELIM.join(("%s", "%s", "%d", "%d", "%.1f", "%d", "%d"))
OUTPUT_FORMAT += os.linesep

CHROM_RE = re.compile(r"[0-9]+")
CHROM_DELIM = ','

XM_RE = re.compile(r"XM:i:([0-9]+)")

CHROM_LENGTHS = (230208,813178,316617,1531919,576869,270148,1090947,562643,
                 439885,745741,666454,1078175,924429,784334,1091289,948062)
NCHROM = len(CHROM_LENGTHS)

def convertIlluminaToFASTQ(dataFile, outFile):
  '''Function to convert file from Illumina to FASTQ format'''
  for line in dataFile:
    match = ILLUMINA_REGEXP_PAIRED.match(line)
    if match:
      out = ILLUMINA_REGEXP_PAIRED.sub(FASTQ_PATTERN, line)
      outFile.write(out)

    return 0

def processBowtieOutput(alignmentFile, outFile, pairedEnd=True):
  '''Function to convert Bowtie output (standard format, not SAM) to read
  summaries. Takes alignment file and output file-like object as argument.
  Returns completion code.'''
  # Print header
  outFile.write(HEADER)

  # Setup DictReader to pull structured lines from Bowtie output file
  alignmentReader = csv.DictReader( alignmentFile, fieldnames=BOWTIE_FIELDS,
                                   delimiter=BOWTIE_DELIM )

  # Initialize alignments
  align2 = None
  align1 = alignmentReader.next()

  # Initialize ID values
  idMatch = ID_RE.match( align1['name'] )
  if idMatch is None:
    id1 = align1['name']
  else:
    id1 = idMatch.group(1)

  # If not paired-end, write first summary
  if not pairedEnd:
    output = combineAlignments(align1)
    outFile.write( OUTPUT_FORMAT % output )

  # Iterate through lines of file
  for line in alignmentReader:
    # Get next alignment from input
    align2 = align1
    id2 = id1
    align1 = line

    # Extract new ID
    idMatch = ID_RE.match( align1['name'] )
    if idMatch is None:
      id1 = align1['name']
    else:
      id1 = idMatch.group(1)

    # Check if IDs match (paired-end)
    if pairedEnd:
      if id1 == id2:
        # If they do, combine the two alignments & print result
        output = combineAlignments( align1, align2 )
        outFile.write( OUTPUT_FORMAT % output )
      else:
        output = combineAlignments(align1)
        outFile.write( OUTPUT_FORMAT % output )

  alignmentFile.close()

  return 0

def combineAlignments( *args ):
  '''Function to combine paired-end alignments into single summary of read.
  Takes parsed alignment dictionaries as inputs, returns read summary tuple.'''
  limits = []
  chromList = []
  nvalidList = []
  for align in args:
    # Find limits of reads
    start = int(align['offset'])
    readLen = len(align['readseq'])
    limits.append( (start, start+readLen) )

    # Extract chromosome ID
    match = CHROM_RE.search(align['refseq'])
    if match is None:
      chromList.append( align['refseq'] )
    else:
      chromList.append( align['refseq'][match.start():match.end()] )

    # Get number of valid alignments
    nvalidList.append( int(align['nvalid']) )

    # Combine limits
    limits = np.array(limits)
    start = limits.min()
    end = limits.max()+1
    length = limits.ptp()
    center = start + length/2.0

    # Combine chromosomes
    chromSet = set(chromList)
    chrom = CHROM_DELIM.join(chromSet)

    # Combine nvalid information
    nvalid = np.array( nvalidList ).sum()

    # Build tuple of return values
    retval = (chrom, '+', start, end, center, length, nvalid)

    return retval

def processSAMOutput(alignmentPath, outFile, pairedEnd=True, rmdup=False):
  '''Function to convert SAM output to read summaries. Takes alignment file and
  output file-like object as argument. Returns completion code.'''

  # Strip file extension from path
  file_name, file_ext = os.path.splitext(alignmentPath)

  # Make into sorted BAM file
  if file_ext.lower() != '.bam':
    os.system('samtools view -bS -o %s %s' %
              (file_name + '.bam', alignmentPath))
    alignmentPath = file_name + '.bam'

  os.system('samtools sort %s %s.sorted' % 
            (alignmentPath, file_name))
  sortedPath = file_name + '.sorted.bam'

  # Remove duplicates if requested
  if rmdup:
    os.system('samtools rmdup %s %s',
              (sortedPath, fileName + 'unique.bam'))
    inputPath = fileName + 'unique.bam'
  else:
    inputPath = sortedPath

  # Print header
  outFile.write(HEADER)

  # Iterate over alignments in SAM file
  time_start = time.time()
  with pysam.Samfile(inputPath, 'rb') as f:
    for alignedRead in f:
      if alignedRead.is_proper_pair and alignedRead.tlen > 0:
        rname = f.getrname(alignedRead.tid)
        match = CHROM_RE.search(rname)
        if match:
          chrom = int(match.group(0))
        else:
          chrom = rname

        start = alignedRead.pos
        length = alignedRead.tlen
        end = start + length - 1
        center = start + (length - 1) / 2.

        nvalid = [tag[1] for tag in alignedRead.tags if tag[0] == 'XM']
        if len(nvalid) == 0:
          nvalid = 0
        else:
          nvalid = nvalid[0]

        output = (chrom, '+', start, end, center, length, nvalid)
        outFile.write(OUTPUT_FORMAT % output)
  
  time_end = time.time()
  print >> sys.stderr, 'Processing time: %f seconds' % (time_end - time_start)

  return 0

def readsToCounts(dataFile, outFile, randomize=True):
  '''
  Function to convert read information to chromosome-level counts.
  Outputs comma-separated counts, one chromosome per line.
  '''
  # Setup data structure for read counts
  reads = []
  for i in xrange(NCHROM):
    reads.append( np.zeros(CHROM_LENGTHS[i], dtype=np.float64) )

    # Setup reader object to parse data file into structure format
    dataReader = csv.DictReader(dataFile, delimiter=BOWTIE_DELIM)

    chromSet = set()
    for line in dataReader:
      # Discard mitochondrial reads
      try:
        chromIndex = int(line['chromosome'])-1
      except:
        continue
      chromSet.add(chromIndex)
      #
      # Extract start and length information
      start = int(line['start'])
      length = int(line['length'])
      center = start + float(length)/2
      #
      # Allocate read center to one or two positions
      if center==np.floor(center): reads[chromIndex][center] += 1.0
      else:
        if randomize:
          reads[chromIndex][np.floor(center)+np.random.randint(1)] += 1.0
        else:
          reads[chromIndex][np.floor(center):np.ceil(center)] += 0.5

    # sys.stderr.write(str(chromSet) + '\n')

    # Write results
    for chrom in reads:
      np.savetxt( outFile, chrom[np.newaxis,:],
                 fmt='%.1f', delimiter=',' )

def getReadLengthDist(dataFile, outFile, offset=0):
  # Setup reader object to parse data file into structure format
  dataReader = csv.DictReader(dataFile, delimiter=BOWTIE_DELIM)

  # Read data and calculate read lengths
  dist = []

  for line in dataReader:
    # Discard mitochondrial reads
    try:
      chromIndex = int(line['chromosome'])-1
    except:
      continue

      readLength = int(line['length'])

      if len(dist) <= readLength:
        dist.extend([0]*(readLength-len(dist)+1))
        dist[readLength] += 1
      else:
        dist[readLength] += 1

    dist = np.array(dist)
    nonzero = np.where(dist > 0)[0]
    nonzero = np.arange(nonzero.min(), nonzero.max()+1, dtype='i')

    # Format & write output
    readLengths = np.vstack( (nonzero, dist[nonzero]) ).T
    np.savetxt(outFile, readLengths, fmt='%d')

