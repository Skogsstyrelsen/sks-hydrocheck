# sks-hydrocheck

This tool is developed by the Swedish Forest Agency and is used for calculating
hydrological properties related to forestry areas and water bodies that are
affected by forestry activities in such areas.

## Documentation

This repository includes the "book" [GIS-verktyg för att bedöma påverkan på
vattenmiljöer vid skogsbruksåtgärder](https://skogsstyrelsen.github.io/sks-hydrocheck/) (in Swedish) which describes the
background and methodology. This documentation is written in Markdown and DOT
language (Graphviz) and can be built into an online book using the utility
[mdBook](https://github.com/rust-lang/mdBook). Rendering the DOT graphs also
requires the mdBook preprocessor [mdBook
Graphviz](https://github.com/dylanowen/mdbook-graphviz) and having
[Graphviz](https://graphviz.gitlab.io/download/) installed.

## Setup conda environment and install dependencies

Setup conda environment from the provided [environment file](./environment.yml) by
executing the following inside project root folder.

```console
conda update -n base -c defaults conda
conda env create -f environment.yml -n skshc-env
```

### Dependencies

sks-hydrocheck's Python dependecies are:

```yml
  - python=3.11.0
  - configargparse=1.5.3
  - geopandas=0.12.1
  - rasterio=1.3.3
  - rasterstats=0.17.0
  - whitebox=2.2.0
```

### PROJ error

If you get a similar error in the output:

```console
ERROR PROJ: proj_identify: .../proj.db lacks DATABASE.LAYOUT.VERSION.MAJOR / DATABASE.LAYOUT.VERSION.MINOR metadata. It comes from another PROJ installation.
```

Do the following:

```console
conda activate skshc-env
...
# On Windows
conda env config vars set PROJ_LIB=%CONDA_PREFIX%\Library\share\proj
...
# On Unix
conda env config vars set PROJ_LIB=$CONDA_PREFIX/Library/share/proj
...
conda deactivate
conda activate skshc-env
```

Or simply add it as a regular environment variable before running.

## Usage

The tool is executed from command line either by passing parameters as arguments
or by using a config file. To list all parameters, run:

``` console
python -m skshc --help
```

Run using a config file:
``` console
python -m skshc -c config-file.conf
```

Verbose mode:
``` console
python -m skshc -c config-file.conf -v
```

Redirect output to log file:
``` console
python -m skshc -c config-file.conf --logfile log-file.log
```

### Config file example

``` ini
[general]
dem-workdir=path/to/dem_workdir                 # Working directory for hydrological DEM result and intermediate data
workdir=path/to/workdir                         # Working directory for area and flowpath processing
clean-workdir=False                             # If true, the working directory for areas and flowpaths will be cleaned before processing
epsg=3006                                       # Some tools require coordinate system definition which may be lost by Whitebox tools

[hydro-dem]
dem=path/to/dem.tif                             # The base DEM file
cell-size=2                                     # Resample base DEM to this cell size
fill-burn-streams=path/to/small_streams.shp     # Vector streams for fill burning into DEM
burn-streams=path/to/streams.shp                # Vector streams for burning at road/railway intersection
burn-roads=path/to/roads_rail.shp               # Vector roads/railway for burning at stream intersection
burn-width=50                                   # See Whitebox manual for tool BurnStreamsAtRoads
culverts=path/to/culverts.shp                   # Culvert as points for breaching road banks in DEM
culvert-snap-tolerance=100                      # Tolerance for snapping culvert point to roads
culvert-buffer-size=20                          # Breach radius around culvert

[targets]
target-streams=path/to/target_streams.shp       # Target stream vector data
target-streams-id-field=FID                     # Target stream identifier column
target-streams-prio-field=PRIO                  # Target stream priority information column

[aoi]
areas=path/to/areas.shp                         # Input polygons for influencing areas (forestry areas)
area-id-field=id                                # Influencing area identifier column
area-part-field=delomr                          # Influencing area part identifier column (for multipolygons)
#area-limit=30                                  # Maximum number of areas to process (infinite by default)

[mf]
mf=path/to/mf.tif                               # Input raster for soil moisture
mf-class-values=[1,2,3,4]                       # Raster values corresponding to soil moisture classes in order: "torr" (dry), "frisk-fuktig" (damp), "blöt" (wet), "öppet vatten" (open water)
dem-streams-threshold=10.0                      # [map unit]*10^-4 For example, if map units are meters the value will be specified as hectars [ha]
wet-near-streams-distance=5.0                   # The distance from identified streams, within the soil moisture is analyzed

[flowpaths]
flowpath-segment-id-field=FID                   # Whitebox will create FID field for shapefiles automatically it is recommended to use for segment ID
seed-point-threshold=0.5                        # [map unit]*10^-4 For example, if map units are meters the value will be specified as hectars [ha]
flowpath-segment-length=100                     # Maximum length of flowpath segments when split for overlay analysis
flowpath-buffer-size=2                          # Flowpath segment buffer size for overlay analysis
threads=8                                       # Area iteration for flowpath calculation may use multiple threads for concurrent processing
```

### All options

``` console
$ python -m skshc -h

usage: skshc [-h] [-c CONFIGFILE] [--logfile [LOG_FILE]] [-v] [--dem-only] --dem-workdir DEM_WORK_DIR --workdir WORK_DIR [--clean-workdir] [--append-areas [APPEND_AREAS]] [--append-flowpaths [APPEND_FLOWPATHS]] --epsg EPSG --dem BASE_DEM [--cell-size [CELL_SIZE]] [--culverts [CULVERTS]]
                  [--culvert-snap-tolerance [CULVERT_SNAP_TOLERANCE]] [--culvert-buffer-size [CULVERT_BUFFER_SIZE]] [--fill-burn-streams [FILL_BURN_STREAMS]] [--burn-streams [BURN_STREAMS]] [--burn-roads [BURN_ROADS]] [--burn-width [BURN_WIDTH]] --target-streams TARGET_STREAMS
                  [--target-streams-id-field [TARGET_STREAMS_ID_FIELD]] [--target-streams-prio-field [TARGET_STREAMS_PRIO_FIELD]] --areas AREAS --area-id-field AREA_ID_FIELD --area-part-field AREA_PART_FIELD [--dem-streams-threshold DEM_STRM_THRESH] --mf MF_RASTER
                  [--wet-near-streams-distance WET_STRM_DIST] [--mf-class-values MF_CLASS_VALUES MF_CLASS_VALUES MF_CLASS_VALUES MF_CLASS_VALUES] [--seed-point-threshold [SEED_POINT_THRESHOLD]] [--flowpath-buffer-size [FLOWPATH_BUFFER_SIZE]] [--flowpath-segment-length [FLOWPATH_SEGMENT_LENGTH]]
                  --flowpath-segment-id-field SEGMENT_ID_FIELD [--area-limit [AREA_LIMIT]] [--threads [THREADS]]

options:
  -h, --help            show this help message and exit
  -c CONFIGFILE, --configfile CONFIGFILE
                        config file path
  --logfile [LOG_FILE]  output to the specified log file - if not specified output redirects to stdout
  -v, --verbose         run whitebox in verbose mode
  --dem-only            process hydrological dem only
  --dem-workdir DEM_WORK_DIR
                        DEM working directory
  --workdir WORK_DIR    working directory
  --clean-workdir       remove existing working directory
  --append-areas [APPEND_AREAS]
                        area dataset to append result to
  --append-flowpaths [APPEND_FLOWPATHS]
                        flowpath dataset to append result to
  --epsg EPSG           EPSG code
  --dem BASE_DEM        base DEM
  --cell-size [CELL_SIZE]
                        resample dem to cell size
  --culverts [CULVERTS]
                        culvert vector points
  --culvert-snap-tolerance [CULVERT_SNAP_TOLERANCE]
                        tolerance used when snapping culverts to roads - infinite if ommited
  --culvert-buffer-size [CULVERT_BUFFER_SIZE]
                        buffer zone size for culvert overlay on DEM
  --fill-burn-streams [FILL_BURN_STREAMS]
                        vector streams for fill burning into dem
  --burn-streams [BURN_STREAMS]
                        vector streams for burning at roads
  --burn-roads [BURN_ROADS]
                        vector roads for burning streams
  --burn-width [BURN_WIDTH]
                        maximum road embankment width
  --target-streams TARGET_STREAMS
                        vector streams - polylines or polygons
  --target-streams-id-field [TARGET_STREAMS_ID_FIELD]
                        target stream id field name
  --target-streams-prio-field [TARGET_STREAMS_PRIO_FIELD]
                        target stream prio info field name
  --areas AREAS         area of interest for zonal stats
  --area-id-field AREA_ID_FIELD
                        area of interest identity field
  --area-part-field AREA_PART_FIELD
                        exploded area parts id field
  --dem-streams-threshold DEM_STRM_THRESH
                        flow acc threshold [ha] for extracting streams from DEM
  --mf MF_RASTER        soil moisture raster for zonal stats
  --wet-near-streams-distance WET_STRM_DIST
                        distance [m] from stream to map wet areas
  --mf-class-values MF_CLASS_VALUES MF_CLASS_VALUES MF_CLASS_VALUES MF_CLASS_VALUES
                        soil moisture class raster values in order dry, damp, wet, open water
  --seed-point-threshold [SEED_POINT_THRESHOLD]
                        seed point flow accumulation threshold [ha] - if not specified 3rd quartile will be used
  --flowpath-buffer-size [FLOWPATH_BUFFER_SIZE]
                        flowpath buffer size for zonal stats along line
  --flowpath-segment-length [FLOWPATH_SEGMENT_LENGTH]
                        flowpath segment length to split into for zonal stats along line
  --flowpath-segment-id-field SEGMENT_ID_FIELD
                        flowpath segment id field
  --area-limit [AREA_LIMIT]
                        max number of areas to process
  --threads [THREADS]
                        number of threads to use for flowpath iterations

Args that start with '--' (eg. --logfile) can also be set in a config file (skshc.conf or specified via -c). Config file syntax allows: key=value, flag=true, stuff=[a,b,c] (for details, see syntax at https://goo.gl/R74nmi). If an arg is specified in more than one place, then commandline values
override config file values which override defaults.
```

### Caching

The package module `utils.py` provides a `Cache` class which will let the tool
reuse output of any existing intermediate or result data. When a Whitebox
instance is initialized, all its methods having an `output` parameter are
decorated with the `cache_handler` decorator. This decorator is also applied to
some of the tool's own methods which produces an output. **Important: When
changing the input data or parameters for the model, make sure to remove any
intermediate data that would be affected by the changes.**

### Threading

The process of tracking downstream flowpaths from areas is limited to run for
one area at a time. To speed up the processing of multiple areas the tool offers
concurrent processing using threading from Python's `multiprocessing.dummy`
module. Threading is used rather than multi-processing since the process is
primarily I/O bound and therefore multiple cores are not taken advantage of.
However, benchmark tests show that the total runtime of flowpath iterations may
be reduced to at least 1/3 by increasing the number of threads.

*Relative processing rate for iterating over 15 areas for different number of threads used (higher is faster)*
| threads | rate |
| ------- | ---- |
| 1       | 1.0x |
| 2       | 1.8x |
| 4       | 2.4x |
| 8       | 3.0x |

## Friskrivningsklausul/Disclaimer

Författaren har hela ansvaret för innehållet. Innehållet ska inte tolkas som Europeiska unionens eller EU-kommissionens officiella ståndpunkt.
The author has full responsibility for the content. The content should not be interpreted as the official view of the European Commission or the European Union.

## Licens

Se [license.txt](license.txt)