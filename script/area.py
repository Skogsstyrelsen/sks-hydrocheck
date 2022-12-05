import logging
import geopandas as gpd
from skshc import tools
from skshc.utils import Output, setup_work_dir
import warnings

logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore")
logging.getLogger('fiona').setLevel(logging.WARNING) # fiona debug level is too verbose
logging.getLogger('rasterio').setLevel(logging.WARNING) # rasterio debug level is too verbose

def prepare_areas(area_file, area_id_field, area_part_field, prepared_areas, area_limit):
    areas = gpd.read_file(area_file)
    if area_limit is not None and area_limit > 0:
        areas = areas.head(area_limit)

    # Remove duplicate areas on area id key
    logger.info("-> Remove duplicate areas on area id key")
    areas.drop_duplicates(subset=area_id_field, keep='first', inplace=True)

    # Explode areas and save to file
    logger.info("-> Explode multipolygon areas and create part id")
    tools.explode_areas(
        aggregated_input=areas,
        part_field=area_part_field,
        output=prepared_areas
    )

def main(args, input):
    work_dir = setup_work_dir(args.work_dir, clean=args.clean_workdir)
    output = Output(work_dir)
    output.add('areas_prepared', "areas_prepared.shp")
    output.add('dist_flwacc_zonal_stats', "dist_flwacc_zonal_stats.shp")
    output.add('mf_zonal_stats', "mf_zonal_stats.shp")
    output.add('areas_stats_prio', "areas_stats_prio.shp")
    output.add('areas_stats_prio_fp', "areas_stats_prio_fp.geojson")
    output.add('areas_clean', "areas_clean.geojson")
    output.add('flowpaths_clean', "flowpaths_clean.geojson")

    prepare_areas(
        area_file=args.areas,
        area_id_field=args.area_id_field,
        area_part_field=args.area_part_field,
        prepared_areas=output.areas_prepared,
        area_limit = args.area_limit
    )

    # Calculate zonal statistics for distance to streams and flow accumuluation within areas
    logger.info("-> Calculating area zonal statistics for distance to prio/non-prio streams and flow accumlation")

    zmap = [
        {"raster": input.dist2stream_prio1_masked or input.dist2stream_prio1, "stats": ["min"], "out_cols": ["dstpr_min"]},
        {"raster": input.dist2stream_prio0_masked or input.dist2stream_prio0, "stats": ["min"], "out_cols": ["dstnp_min"]},
        {"raster": input.mf_wet_near_streams, "stats": ["sum"], "out_cols": ["wetstr_sum"]},
        {"raster": input.flow_acc_ha, "stats": ["max"], "out_cols": ["flwacc_max"]}
    ]
    tools.batch_zonal_stats(
        base_shape=output.areas_prepared,
        key_fields=[args.area_id_field, args.area_part_field],
        input_map=zmap,
        output=output.dist_flwacc_zonal_stats
    )

    # Calculate zonal statistics for soil moisture raster within areas
    logger.info("-> Calculating area zonal statistics for soil moisture raster")
    tools.zonal_class_stats(
        base_shape=output.dist_flwacc_zonal_stats,
        raster=args.mf_raster,
        col_map=dict(zip(args.mf_class_values, ["dry", "dmp", "wet", "wtr"])),
        fracs=True,
        output=output.mf_zonal_stats
    )

    logger.info("-> Join target info to areas")

    # Join target prio to areas
    tools.join_target_info(
        source=output.mf_zonal_stats,
        target=input.target_allocation_vector_prio,
        epsg=args.epsg,
        key_fields=[args.area_id_field, args.area_part_field],
        flow_acc=input.flow_acc_ha,
        flow_acc_threshold=args.seed_point_threshold,
        rank_fields=[args.area_id_field, args.area_part_field, args.target_streams_prio_field, 'geometry'],
        rank_fields_asc=[True, True, False, False],
        output=output.areas_stats_prio
    )

    # Calculate flowpaths
    logger.info("-> Loading flowpath tool")
    import skshc.flowpath as fpt

    logger.info("-> Select areas for flowpath analysis")
    gdf = gpd.read_file(output.areas_stats_prio)
    selected_area_parts = gdf.query('dstpr_min==dstpr_min or dstnp_min==dstnp_min')[[args.area_id_field, args.area_part_field]].to_records(index=False).tolist()

    logger.info("-> Calculating flowpaths")
    area_ref_fields = ["area_id", "area_part"]
    flowpath_stats = fpt.main(
        args=args,
        dem_data=input,
        areas=output.areas_stats_prio,
        area_id_fields=[args.area_id_field, args.area_part_field],
        area_ref_fields=area_ref_fields,
        area_part_selection=selected_area_parts
    )

    logger.info("-> Merge flowpath stats to areas")
    q3 = tools.q3
    fp_aggs = {
        "st_mean": ["mean", q3],
        "slp_mean": ["mean", q3],
        "fla_mean": ["mean", q3]
    }
    tools.merge_stats(
        output.areas_stats_prio,
        flowpath_stats,
        left_keys=[args.area_id_field, args.area_part_field],
        right_keys=area_ref_fields,
        aggs=fp_aggs,
        prio_field=args.target_streams_prio_field,
        output=output.areas_stats_prio_fp
    )

    logger.info("-> Clean results")
    tools.clean_result(output.areas_stats_prio_fp, epsg=args.epsg, output=output.areas_clean)
    tools.clean_result(flowpath_stats, epsg=args.epsg, output=output.flowpaths_clean)

    if args.append_areas:
        logger.info("-> Appending area results to existing result")
        tools.append_result(target=args.append_areas, source=output.areas_clean)

    if args.append_flowpaths:
        logger.info("-> Appending flowpath results to existing result")
        tools.append_result(target=args.append_flowpaths, source=output.flowpaths_clean, index_column=args.segment_id_field)
