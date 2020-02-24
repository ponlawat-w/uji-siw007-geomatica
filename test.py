import sys
import os
import pci
# datasource: Dataset (.pix) File Manager
from pci.api import datasource

def qprint(msg):
  print(msg, end = '', flush = True)

def qprintl(msg):
  print(msg, flush = True)

# Open Dataset
qprint('Opening file...')
dataset = datasource.open_dataset('data/golden_horseshoe.pix', mode = datasource.eAM_WRITE)
# ↑ Open dataset from specified path
# ↓ aux_data is for managing channel description (get/set)
auxiliaryData = dataset.aux_data
qprintl('OK \\(^o^)/')

qprintl('Channels in dataset:')
for i in range(1, dataset.chan_count + 1):
  qprintl('  Channel {}: {}'.format(i, auxiliaryData.get_chan_description(i)))

# Create channels if not sufficient
qprintl('Is it neccessary to create a new channnel?')
if (dataset.chan_count < 9):
  qprint('  Yes, creating new channel(s)...')
  # pcimod: Channel Manager (Add/Delete)
  from pci.pcimod import pcimod
  pcimod(
    file = dataset.name,
    pciop = 'ADD',
    pcival = [9 - dataset.chan_count, 0, 0, 0]
  )
  dataset = datasource.open_dataset('data/golden_horseshoe.pix', mode = datasource.eAM_WRITE)
  auxiliaryData = dataset.aux_data
  qprintl('OK \\(^o^)/')
  qprintl('Channels in dataset:')
  for i in range(1, dataset.chan_count + 1):
    qprintl('  Channel {}: {}'.format(i, auxiliaryData.get_chan_description(i)))
else:
  qprintl('  No')

# KCLUS

# kclus: Unsupervised Classification with K-Means
from pci.kclus import kclus

qprintl('Executing K-Means...')
kclus(
  file = dataset.name,        # Input file name
  dbic = list(range(1, 7)),   # Input channels
  dboc = [7],                 # Output channel
  numclus = [5],              # Number of output cluster classes
  maxiter = [5]               # Maximum iterations
)
auxiliaryData.set_chan_description('K-Means', 7)
qprintl('Executing K-Means: OK \\(^o^)/')

# FMO

# fmo: Mode Filter
from pci.fmo import fmo

qprint('Applying Mode Filter...')
fmo(
  file = dataset.name,  # Input file
  dbic = [7],           # Input channel
  dboc = [8],           # Output channel
  flsz = [3, 3]         # Filter size
)
auxiliaryData.set_chan_description('Mode-Filtered K-Means', 8)
qprintl('OK \\(^o^)/')

# SIEVE

# sieve: Sieve
from pci.sieve import sieve

qprint('Applying Sieve...')
sieve(
  file = dataset.name,  # Input file
  dbic = [8],           # Input channel
  dboc = [9],           # Output channel
  sthresh = [32]        # Polygon size threshold
)
auxiliaryData.set_chan_description('Sieved Mode-Filtered K-Means', 9)
qprintl('OK \\(^o^)/')

# RAS2POLY

# ras2poly: Convertor of raster to polygon
from pci.ras2poly import ras2poly

qprint('Convert rasters to polygons')
shpFiles = [
  'data/golden_horseshow.dbf',
  'data/golden_horseshow.prj',
  'data/golden_horseshow.shp',
  'data/golden_horseshow.shp.pox',
  'data/golden_horseshow.shx'
]
qprintl('Checking files...')
for shpFile in shpFiles:
  qprint('    {} exists?: '.format(shpFile))
  if (os.path.exists(shpFile)):
    qprint('Yes, deleting...')
    os.remove(shpFile)
    qprintl('OK')
  else:
    qprintl('No, skipped.')

qprint('  Converting rasters to polygon shape file...')
ras2poly(
  fili = dataset.name,                # Input file
  dbic = [9],                         # Input channel
  filo = shpFiles[1], # Output file
  ftype = 'SHP'                       # Output type
)
qprintl('OK \\(^o^)/')

# PCTMAKE

# pctmake: Pseudotable Maker
from pci.pctmake import pctmake

qprintl('Making pseudocolour table...')
pctOutputs = []
pctDesctiption = 'KMeansPCT'

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
  file = dataset.name,    # Input file
  dbic = [1, 2, 3],       # Input raster channels (R, G, B)
  dbtc = [9],             # Input theme channel
  dbpct = pctOutputs,     # Output PCT Segment
  dbsn = 'KPCT',          # Output PCT Segment Name
  dbsd = pctDesctiption   # Output PCT Segment Description
)
qprintl('OK \\(^o^)/')

# Summarising

qprintl('Channels in dataset:')
for i in range(1, dataset.chan_count + 1):
  qprintl('  Channel {}: {}'.format(i, auxiliaryData.get_chan_description(i)))

qprint('Updating channel information...')
dataset.aux_data = auxiliaryData
qprintl('OK \\(^o^)/')

qprintl('\n                       ~( ^ O ^ )~')
qprintl('\n( ^_^) \\(^o^)/ (^_^ ) !! SUCCESS !! ( ^_^) \\(^o^)/ (^_^ )')
qprintl('\n                      \\\\( ^ O ^ )//\n')
