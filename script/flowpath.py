from multiprocessing.dummy import Pool as ThreadPool
import itertools
from pathlib import Path
import logging
import whitebox
import geopandas as gpd
import rasterio
import rasterio.mask
from rasterio import features
from shapely.geometry import shape
from fiona.errors import DriverError
from skshc import tools
from skshc.utils import Output, Counter, Cache, WBTProcessingError, wbt_callback

cache = Cache().cache_handler
logger = logging.getLogger(__name__)

# Initialize Whitebox Tools
wbt = whitebox.WhiteboxTools()
wbt.set_default_callback(wbt_callback)
wbt.set_verbose_mode(True) # Callback needs all info
wbt_cacher = Cache()
wbt_cacher.cache_funcs(wbt)

@cache
def remove_inside(base, container, output, epsg=None):
    gdf = gpd.read_file(base)
    if epsg is not None:
        gdf = gdf.set_crs(epsg)
    outside = gdf.overlay(container, how="difference")
    outside.to_file(output)
    return output

@cache
def flowpath_split(flowpaths, flowpath_segment_length, segment_id_field, output):
    gdf = gpd.read_file(flowpaths)
    gdf_exp = gdf.explode("geometry", index_parts=False)
    flowpaths_split_gdf = tools.split_lines(gdf_exp, flowpath_segment_length, segment_id_field)
    flowpaths_split_gdf.to_file(output)
    return output

@cache
def flowpath_buffer(flowpaths, flowpath_buffer_size, output):
    gdf = gpd.read_file(flowpaths)
    gdf.geometry=gdf.buffer(flowpath_buffer_size, join_style=3, cap_style=2)
    gdf.to_file(output)
    return output

@cache
def extract_seed_points(flow_acc, mask_geom, output, flow_acc_threshold=None):
    with rasterio.open(flow_acc) as src:
        img, affine = rasterio.mask.mask(src, [mask_geom], crop=True)
    shapes = features.shapes(img, transform=affine)
    values = []
    geometries = []
    for geom, value in shapes:
        values.append(value)
        geometries.append(shape(geom).centroid)

    candidates = gpd.GeoDataFrame({'value': values, 'geometry': geometries})
    selected = candidates[candidates.value >= (flow_acc_threshold or tools.q3(values))]

    if len(selected) > 0:
        selected.to_file(output)
        return output

    return None

def calc_stream_slope(d8_ptr, flowpaths_raster, dem, output):
    wbt.stream_slope_continuous(
        d8_pntr=d8_ptr,
        streams=flowpaths_raster,
        dem=dem,
        output=output,
        esri_pntr=False,
        zero_background=False
    )
    return output

def trace_flowpaths(seed_pts, d8_pntr, output):
    wbt.trace_downslope_flowpaths(
        seed_pts=seed_pts,
        d8_pntr=d8_pntr,
        output=output,
        esri_pntr=False,
        zero_background=False
    )
    return output

def vectorize_flowpaths(flowpaths, d8_pointer, output):
    wbt.raster_streams_to_vector(
        streams=flowpaths,
        d8_pntr=d8_pointer,
        output=output,
        esri_pntr=False
    )
    return output

def rasterize_flowpaths(flowpaths, base, output):
    wbt.rasterize_streams(
        streams=flowpaths,
        base=base,
        output=output,
        nodata=True,
        feature_id=True
    )
    return output

@cache
def add_id_column(input, field_names, values, output):
    gdf = gpd.read_file(input)
    for i, field_name in enumerate(field_names):
        if field_name not in gdf.columns:
            gdf[field_name] = values[i]
    gdf.to_file(output)
    return output

def merge_area_flowpaths(vector_flowpaths, output):
    wbt.merge_vectors(
        inputs=",".join(vector_flowpaths),
        output=output,
    )
    return output

def smooth_flowpaths(input, output):
    wbt.smooth_vectors(
        i=input,
        output=output,
        filter=3
    )
    return output

def main(args, dem_data, areas, area_id_fields, area_ref_fields, area_part_selection=[]):
    pool = ThreadPool(args.threads)
    output = Output(work_dir=args.work_dir)

    output.add('flowpaths_merged', "flowpaths_merged.shp")
    output.add('flowpaths_outside', "flowpaths_outside.shp")
    output.add('flowpaths_split', "flowpaths_split.shp")
    output.add('flowpath_zones', "flowpath_zones.shp")
    output.add('flowpath_zonal_stats', "flowpath_zonal_stats.shp")
    output.add('flowpath_stats', "flowpath_stats.shp")
    output.add('flowpaths_raster', "flowpaths.tif")
    output.add('flowpaths_slope_raster', "flowpaths_slope.tif")
    output.add('flowpaths_smoothed', "flowpaths_smooth.shp")

    areas_gdf = gpd.read_file(areas)
    main_area_field, part_field = area_id_fields

    if area_part_selection:
        main_ids, part_ids = zip(*area_part_selection)
        areas_gdf = areas_gdf[areas_gdf[main_area_field].isin(main_ids)]

    area_list = list(areas_gdf[[main_area_field, part_field, 'geometry']].to_records(index=False))

    def iter_areas(area, area_counter):
        mid, pid, geom = area # Unpack main-area, part-id, geom tuple
        logger.info(f"-> Remaining flowpath iterations: {area_counter.sub()}")
        logger.info(f"-> Starting flowpath iteration for area: {mid}, part: {pid}")
        area_part_work_dir = Path(args.work_dir) / f"{mid}_{pid}"
        area_output = Output(work_dir=area_part_work_dir)
        area_output.add('seed_points', "seed_points.shp")
        area_output.add('flowpaths', "flowpaths.tif")
        area_output.add('flowpaths_vector', "flowpaths.shp")
        area_output.add('flowpaths_vector_allocated', "flowpaths_alloc.shp")
        area_output.add('flowpaths_area', "flowpaths_area.shp")

        if Path(area_output.flowpaths_area).is_file():
            logger.info(f"Flowpath result for area {mid}.{pid} already exists - skipping")
            return area_output.flowpaths_area

        area_part_work_dir.mkdir(parents=True, exist_ok=True)

        logger.info("-> Extracting seed points")
        seed_points = extract_seed_points(
            flow_acc=dem_data.flow_acc_ha_threshold,
            mask_geom=geom,
            flow_acc_threshold=args.seed_point_threshold,
            output=area_output.seed_points
        )

        if seed_points is not None:
            try:
                flowpaths = trace_flowpaths(seed_points, dem_data.d8_pointer_masked, output=area_output.flowpaths)
                flowpaths_vector = vectorize_flowpaths(flowpaths, dem_data.d8_pointer_masked, output=area_output.flowpaths_vector)
                logger.info("-> Join target info to flowpath")
                flowpaths_vector_allocated = tools.join_container(
                    input=flowpaths_vector,
                    container=dem_data.target_allocation_vector_prio,
                    output=area_output.flowpaths_vector_allocated
                )
                flowpath_count = len(gpd.read_file(flowpaths_vector_allocated, ignore_geometry=True))
                assert flowpath_count > 0
            except (WBTProcessingError, DriverError, AssertionError):
                logger.warning(f"Failed to calculate flowpath for area {mid}.{pid}")
                return None

            flowpaths_area = add_id_column(flowpaths_vector_allocated, field_names=area_ref_fields, values=[mid, pid], output=area_output.flowpaths_area)
            return flowpaths_area

    area_counter = Counter(start=len(area_list))
    flowpath_list = pool.starmap(iter_areas, zip(area_list, itertools.repeat(area_counter)))
    flowpath_list = [f for f in flowpath_list if f is not None]

    logger.info("-> Merging flowpaths")
    merge_area_flowpaths(flowpath_list, output=output.flowpaths_merged)

    logger.info("-> Remove flowpaths inside areas")
    remove_inside(output.flowpaths_merged, container=areas_gdf, epsg=args.epsg, output=output.flowpaths_outside)

    logger.info("-> Rasterizing merged flowpaths")
    rasterize_flowpaths(output.flowpaths_merged, dem_data.dem_breach, output=output.flowpaths_raster)

    logger.info("-> Calculating stream slope")
    calc_stream_slope(dem_data.d8_pointer, output.flowpaths_raster, dem_data.dem_breach, output=output.flowpaths_slope_raster)

    logger.info("-> Split and buffer flowpaths")
    flowpath_split(
        flowpaths=output.flowpaths_outside,
        flowpath_segment_length=args.flowpath_segment_length,
        segment_id_field=args.segment_id_field,
        output=output.flowpaths_split
    )

    flowpath_buffer(
        flowpaths=output.flowpaths_split,
        flowpath_buffer_size=args.flowpath_buffer_size,
        output=output.flowpath_zones
    )

    logger.info("-> Calculating flowpath zonal stats for sediment transport index, stream slope and flow accumulation")

    zmap = [
        {"raster": dem_data.sediment_transport_index, "stats": ["mean"], "out_cols": ["st_mean"]},
        {"raster": output.flowpaths_slope_raster, "stats": ["mean"], "out_cols": ["slp_mean"]},
        {"raster": dem_data.flow_acc_ha_threshold, "stats": ["mean"], "out_cols": ["fla_mean"]}
    ]
    zcols = [c for z in zmap for c in z["out_cols"]]
    tools.batch_zonal_stats(
        base_shape=output.flowpath_zones,
        key_fields=[args.segment_id_field],
        input_map=zmap,
        output=output.flowpath_zonal_stats
    )

    tools.left_join(
        output.flowpaths_split,
        output.flowpath_zonal_stats,
        args.segment_id_field,
        zcols,
        output=output.flowpath_stats
    )

    logger.info("-> Smoothing merged flowpaths")
    smooth_flowpaths(output.flowpath_stats, output=output.flowpaths_smoothed)

    return output.flowpaths_smoothed
