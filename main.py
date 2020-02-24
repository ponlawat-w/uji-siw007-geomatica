import sys
import os
import pci
from pci.api import datasource
from pci.pcimod import pcimod

##### Constants #####
INPUT_MARK = 'INPUT '
KCLUS_RESULT = 'KClusResult'
FMO_RESULT = 'FMOResult'
SIEVE_RESULT = 'SieveResult'
PCT_NAME = 'KPCT'
PCT_DESCRIPTION = 'KMeansPCT'

##### Global Variables #####
dataset = None
auxiliaryData = None

##### Functions #####

def qprint(msg):
  print(msg, end = '', flush = True)

def qprintl(msg):
  print(msg, flush = True)

def terminate():
  qprintl('\n(T__T) Programme terminated with exceptions (TT^TT)\n')
  quit()

def listAllChannels():
  global dataset, auxiliaryData
  qprintl('Channels in dataset:')
  for i in range(1, dataset.chan_count + 1):
    qprintl('  Channel {}: {}'.format(i, auxiliaryData.get_chan_description(i)))

def setChannelDescription(number, description, prefix = ''):
  global dataset, auxiliaryData
  auxiliaryData.set_chan_description(prefix + description, number)
  dataset.aux_data = auxiliaryData

def inputChannelsProvided():
  return len(sys.argv) > 3

def getInputChannels():
  if (inputChannelsProvided()):
    return list(map(int, sys.argv[3].split(',')))
  else:
    qprint('Please provide input channels (split with comma): ')
    return list(map(int, input().split(',')))

def getInputChannelsByMark():
  global dataset, auxiliaryData
  inputChannels = []
  for i in range(1, dataset.chan_count + 1):
    if (auxiliaryData.get_chan_description(i).startswith(INPUT_MARK)):
      inputChannels.append(i)
  return inputChannels

def markInputChannels(inputChannels):
  global auxiliaryData
  for i in inputChannels:
    setChannelDescription(i, auxiliaryData.get_chan_description(i), INPUT_MARK)

def unmarkInputChannels():
  global dataset, auxiliaryData
  for i in range(1, dataset.chan_count + 1):
    channelDescription = auxiliaryData.get_chan_description(i)
    if (channelDescription.startswith(INPUT_MARK)):
      setChannelDescription(i, channelDescription[len(INPUT_MARK):])

def getChannelNumber(channelName):
  global dataset, auxiliaryData
  # Scan for channel name
  for i in range(1, dataset.chan_count + 1):
    if (auxiliaryData.get_chan_description(i).startswith(channelName)):
      return i
  # Scan for empty channel
  for i in range(1, dataset.chan_count + 1):
    if (auxiliaryData.get_chan_description(i) == 'Contents Not Specified'):
      qprintl('Use empty channel #{} for {}'.format(i, channelName))
      setChannelDescription(i, channelName)
      return i
  qprint('Creating a new channel for {}...'.format(channelName))
  pcimod(
    file = dataset.name,
    pciop = 'ADD',
    pcival = [1, 0, 0, 0]
  )
  dataset = datasource.open_dataset(dataset.name, datasource.eAM_WRITE)
  auxiliaryData = dataset.aux_data
  qprintl('OK')
  return getChannelNumber(channelName)

def updateChannelName(channel, channelName):
  global dataset, auxiliaryData
  auxiliaryData = dataset.aux_data
  currentDescription = auxiliaryData.get_chan_description(channel)
  if (currentDescription != channelName):
    auxiliaryData.set_chan_description('{} - {}'.format(channelName, currentDescription), channel)
    dataset.aux_data = auxiliaryData

def getOutputFiles():
  outputPath = sys.argv[2]
  if (outputPath.lower().endswith('.shp')):
    outputPath = outputPath[:-4]
  return [
    outputPath + '.shp',
    outputPath + '.dbf',
    outputPath + '.prj',
    outputPath + '.shp.pox',
    outputPath + '.shx'
  ]

##### Program #####

if (len(sys.argv) < 3):
  qprintl('(O_o) Invalid arguments: please provide input file and output file')
  terminate()

inputFile = sys.argv[1]

# Open Dataset
qprint('Opening file...')
dataset = datasource.open_dataset(inputFile, mode = datasource.eAM_WRITE)
auxiliaryData = dataset.aux_data
qprintl('OK \\(^o^)/')

qprintl('Reading channels...')

# Get input channels
if (not inputChannelsProvided()):
  listAllChannels()
inputChannels = getInputChannels()
markInputChannels(inputChannels)
qprintl('')

kClusChannel = getChannelNumber(KCLUS_RESULT)
fmoChannel = getChannelNumber(FMO_RESULT)
sieveChannel = getChannelNumber(SIEVE_RESULT)

inputChannels = getInputChannelsByMark()

# Display all channels
for i in range(1, dataset.chan_count + 1):
  qprintl('  Channel {}: {}{}{}{}{}'.format(
    i,
    auxiliaryData.get_chan_description(i),
    ('\t\t[INPUT CHANNEL (^o^)]' if i in inputChannels else ''),
    ('\t\t[KCLUS CHANNEL (>_<)]' if i == kClusChannel else ''),
    ('\t\t[FMO CHANNEL (O_o)]' if i == fmoChannel else ''),
    ('\t\t[SIEVE CHANNEL (^w^)]' if i == sieveChannel else '')
  ))

# Execution

qprint('Press any key to continue...')
input()

qprint('\n\n===== (>_<) Starting Execution (>_<) =====\n\n')

# KCLUS

from pci.kclus import kclus

qprintl('[1 of 5] KCLUS\tExecuting K-Means...')
kclus(
  file = dataset.name,    # Input file name
  dbic = inputChannels,   # Input channels
  dboc = [kClusChannel],  # Output channel
  numclus = [5],          # Number of output cluster classes
  maxiter = [5]           # Maximum iterations
)
updateChannelName(kClusChannel, KCLUS_RESULT)
qprintl('[1 of 5] KCLUS\tExecuting K-Means...OK \\(^o^)/')

# FMO

from pci.fmo import fmo

qprint('[2 of 5] FMO\tApplying Mode Filter...')
fmo(
  file = dataset.name,    # Input file
  dbic = [kClusChannel],  # Input channel
  dboc = [fmoChannel],    # Output channel
  flsz = [3, 3]           # Filter size
)
updateChannelName(fmoChannel, FMO_RESULT)
qprintl('OK \\(^o^)/')

# SIEVE

from pci.sieve import sieve

qprint('[3 of 5] SIEVE\tApplying Sieve...')
sieve(
  file = dataset.name,    # Input file
  dbic = [fmoChannel],    # Input channel
  dboc = [sieveChannel],  # Output channel
  sthresh = [32]          # Polygon size threshold
)
updateChannelName(sieveChannel, SIEVE_RESULT)
qprintl('OK \\(^o^)/')

# RAS2POLY

from pci.ras2poly import ras2poly

qprintl('[4 of 5] RAS2POLY\tConvert rasters to polygons')
shpFiles = getOutputFiles()
qprintl('  Checking files...')
for shpFile in shpFiles:
  qprint('    {} exists?: '.format(shpFile))
  if (os.path.exists(shpFile)):
    qprint('Yes, deleting...')
    os.remove(shpFile)
    qprintl('OK \\(^o^)/')
  else:
    qprintl('No, skipped.')

qprint('  Converting rasters to polygon shape file...')
ras2poly(
  fili = dataset.name,                # Input file
  dbic = [sieveChannel],                         # Input channel
  filo = shpFiles[0], # Output file
  ftype = 'SHP'                       # Output type
)
qprintl('OK \\(^o^)/')

# PCTMAKE

from pci.pctmake import pctmake

qprintl('[5 of 5] PCTMAKE\tMaking pseudocolour table...')
pctOutputs = []
pctDesctiption = PCT_DESCRIPTION

qprintl(' Does KMeansPCT already exist?')
for i in dataset.get_pct_io_ids():
  pct = dataset.get_pct_io(i)
  if (pct.description == pctDesctiption):
    pctOutputs = [pct.id]
    break

if (len(pctOutputs) == 0):
  qprint('  No, create a new one...')
else:
  qprint('  Yes, overwriting the existing one...')

pctmake(
  file = dataset.name,        # Input file
  dbic = inputChannels[:3],  # Input raster channels (R, G, B)
  dbtc = [sieveChannel],      # Input theme channel
  dbpct = pctOutputs,         # Output PCT Segment
  dbsn = PCT_NAME,            # Output PCT Segment Name
  dbsd = pctDesctiption       # Output PCT Segment Description
)
qprintl('OK \\(^o^)/')

# Summarising

qprint('Finishing...')
unmarkInputChannels()
qprintl('OK \\(^o^)/')

listAllChannels()

qprintl('\nProgramme terminated with success!')

qprintl('\n                       ~( ^ O ^ )~')
qprintl('\n( ^_^) \\(^o^)/ (^_^ ) !! SUCCESS !! ( ^_^) \\(^o^)/ (^_^ )')
qprintl('\n                      \\\\( ^ O ^ )//\n')
