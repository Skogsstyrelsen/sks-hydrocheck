import logging
import whitebox
from skshc import tools
from skshc.utils import Output, Cache, wbt_callback, setup_work_dir

logger = logging.getLogger(__name__)

# Initialize Whitebox Tools
wbt = whitebox.WhiteboxTools()
wbt.set_default_callback(wbt_callback)
wbt.set_verbose_mode(True) # Callback needs all info
wbt_cacher = Cache()
wbt_cacher.cache_funcs(wbt)

def main(args):
    work_dir = setup_work_dir(args.dem_work_dir)
    output = Output(work_dir)
    output.add('culvert_zones', "culvert_zones.shp" if args.culverts else None)
    output.add('dem_burn_culverts', "dem_culverts_burned.tif" if args.culverts else None)
    output.add('dem_resampled', "dem_resampled.tif" if args.cell_size else None)
    output.add('dem_fill_burn_streams', "dem_fill_burn_streams.tif" if args.fill_burn_streams else None)
    output.add('dem_burn_roads', "dem_burn_roads.tif" if args.burn_roads else None)
    output.add('dem_breach', "dem_breached.tif")

    calc_hydro_dem(
        base_dem=args.base_dem,
        culverts=args.culverts,
        culvert_snap_tolerance=args.culvert_snap_tolerance,
        culvert_buffer_size=args.culvert_buffer_size,
        burn_roads=args.burn_roads,
        culvert_zones=output.culvert_zones,
        dem_burn_culverts=output.dem_burn_culverts,
        dem_breach=output.dem_breach,
        burn_streams=args.burn_streams,
        burn_width=args.burn_width,
        fill_burn_streams=args.fill_burn_streams,
        cell_size=args.cell_size,
        dem_resampled=output.dem_resampled,
        dem_fill_burn_streams=output.dem_fill_burn_streams,
        dem_burn_roads=output.dem_burn_roads
    )

    output.add('flow_acc', "dem_flow_acc.tif")
    output.add('flow_acc_ha', "dem_flow_acc_ha.tif")
    calc_flow_acc(
        dem=output.dem_breach,
        flow_acc=output.flow_acc,
        flow_acc_ha=output.flow_acc_ha
    )

    output.add('target_streams_id_raster', "target_streams_id.tif")
    output.add('target_streams_prio_raster', "target_streams_prio.tif")
    output.add('target_streams_prio1_raster', "target_streams_prio1.tif")
    output.add('target_streams_prio0_raster', "target_streams_prio0.tif")
    output.add('flow_acc_ha_threshold', "dem_flow_acc_ha_threshold.tif")
    output.add('dem_streams_extracted', "dem_streams_extracted.tif")
    output.add('dist2dem_strm_extr', "dist2dem_strm_extr.tif")
    output.add('dist2stream_prio1', "dist2stream_prio1.tif")
    output.add('dist2stream_prio0', "dist2stream_prio0.tif")
    output.add('dist2stream_prio1_masked', "dist2stream_prio1_masked.tif")
    output.add('dist2stream_prio0_masked', "dist2stream_prio0_masked.tif")
    output.add('d8_pointer', "d8_ptr.tif")
    output.add('d8_pointer_masked', "d8_ptr_masked.tif")
    output.add('target_allocation_raster', "target_allocation.tif")
    output.add('target_allocation_vector', "target_allocation.shp")
    output.add('target_allocation_vector_prio', "target_allocation_prio.shp")

    calc_allocation(
        base_dem=output.dem_resampled or args.base_dem,
        hydro_dem=output.dem_breach,
        target_streams=args.target_streams,
        target_streams_id_field=args.target_streams_id_field,
        target_streams_prio_field=args.target_streams_prio_field,
        flow_acc_ha=output.flow_acc_ha,
        seed_point_threshold=args.seed_point_threshold,
        dem_strm_thresh=args.dem_strm_thresh,
        target_streams_id_raster=output.target_streams_id_raster,
        target_streams_prio_raster=output.target_streams_prio_raster,
        target_streams_prio1_raster=output.target_streams_prio1_raster,
        target_streams_prio0_raster=output.target_streams_prio0_raster,
        flow_acc_ha_threshold=output.flow_acc_ha_threshold,
        dem_streams_extracted=output.dem_streams_extracted,
        dist2dem_strm_extr=output.dist2dem_strm_extr,
        dist2stream_prio1=output.dist2stream_prio1,
        dist2stream_prio0=output.dist2stream_prio0,
        dist2stream_prio1_masked=output.dist2stream_prio1_masked,
        dist2stream_prio0_masked=output.dist2stream_prio0_masked,
        d8_pointer=output.d8_pointer,
        d8_pointer_masked=output.d8_pointer_masked,
        target_allocation_raster=output.target_allocation_raster,
        target_allocation_vector=output.target_allocation_vector,
        target_allocation_vector_prio=output.target_allocation_vector_prio,
    )

    output.add('slope', "slope.tif")
    output.add('sediment_transport_index', "sediment_transport_index.tif")

    calc_sti(
        base_dem=output.dem_resampled or args.base_dem,
        flow_acc=output.flow_acc,
        slope=output.slope,
        sediment_transport_index=output.sediment_transport_index
    )

    output.add('mf_resampled', "mf_resampled.tif")
    output.add('mf_wet_near_streams', "mf_wet_near_streams.tif")

    calc_wet(
        mf_raster=args.mf_raster,
        base_dem=output.dem_resampled or args.base_dem,
        mf_resampled=output.mf_resampled,
        dist2dem_strm_extr=output.dist2dem_strm_extr,
        wet_strm_dist=args.wet_strm_dist,
        mf_wet_class_val=args.mf_class_values[2],
        cell_size=args.cell_size or 1,
        mf_wet_near_streams=output.mf_wet_near_streams
    )

    return output

def calc_hydro_dem(
    base_dem,  # required input
    dem_breach, # required output
    cell_size=None, burn_streams=None, burn_roads=None, burn_width=None, fill_burn_streams=None, # optional input
    culverts=None, culvert_snap_tolerance=None, culvert_buffer_size=None,  # optional input
    dem_resampled=None, dem_fill_burn_streams=None, dem_burn_roads=None, # optional output
    culvert_zones=None, dem_burn_culverts=None # optional output
):
    # Resample DEM
    if dem_resampled and cell_size:
        logger.info("-> Creating resampled raster")
        wbt.resample(
            inputs=base_dem,
            output=dem_resampled,
            cell_size=cell_size,
            method="cc"
        )

    # Create culvert zones
    if culverts and culvert_buffer_size:
        logger.info("-> Creating culvert zones")
        tools.create_culvert_zones(
            culvert_points=culverts,
            roads=burn_roads,
            tolerance=culvert_snap_tolerance,
            buffer_size=culvert_buffer_size,
            output=culvert_zones
        )

        # Burn culvert elevations to DEM using "flatten lakes" tool
        logger.info("-> Burning culvert elevations to DEM")
        wbt.flatten_lakes(
            dem=dem_resampled or base_dem,
            lakes=culvert_zones,
            output=dem_burn_culverts
        )

    # FillBurn streams into DEM
    if fill_burn_streams:
        logger.info("-> Creating fillburn raster")
        wbt.fill_burn(
            dem=dem_burn_culverts or dem_resampled or base_dem,
            streams=fill_burn_streams,
            output=dem_fill_burn_streams
        )

    # Burn streams at roads
    if burn_streams and burn_roads and burn_width:
        logger.info("-> Creating burn-at-roads raster")
        wbt.burn_streams_at_roads(
            dem=dem_fill_burn_streams or dem_burn_culverts or dem_resampled or base_dem,
            streams=burn_streams,
            roads=burn_roads,
            output=dem_burn_roads,
            width=burn_width
        )

    # Breach resampled DEM
    logger.info("-> Creating breached raster")
    wbt.breach_depressions(
        dem=dem_burn_roads or dem_fill_burn_streams or dem_burn_culverts or dem_resampled or base_dem,
        output=dem_breach,
        max_depth=None,
        max_length=None,
        flat_increment=0.0001,
        fill_pits=False
    )

def calc_flow_acc(
    dem, #dem_breach
    flow_acc, flow_acc_ha # required output
):
    # Create flow accumulation raster
    logger.info("-> Creating flow accumulation raster")
    wbt.d8_flow_accumulation(
        i=dem,
        output=flow_acc,
        out_type="catchment area",
        log=False,
        clip=False,
        pntr=False,
        esri_pntr=False
    )

    # Create flow accumulation raster in ha units
    logger.info("-> Creating flow accumulation (ha) raster")
    wbt.raster_calculator(
        output=flow_acc_ha,
        statement=f"'\"{flow_acc}\" / 10000'",
    )

def calc_allocation(
    base_dem, #dem_resampled
    hydro_dem, #dem_breached
    target_streams, target_streams_id_field, target_streams_prio_field,
    flow_acc_ha, seed_point_threshold, dem_strm_thresh,
    target_streams_id_raster,
    target_streams_prio_raster,
    target_streams_prio1_raster,
    target_streams_prio0_raster,
    flow_acc_ha_threshold,
    dem_streams_extracted,
    dist2dem_strm_extr,
    dist2stream_prio1,
    dist2stream_prio0,
    dist2stream_prio1_masked,
    dist2stream_prio0_masked,
    d8_pointer,
    d8_pointer_masked,
    target_allocation_raster,
    target_allocation_vector,
    target_allocation_vector_prio
):
    # Vector polygon target streams to raster
    logger.info("-> Creating target stream id raster from vector polygons")
    wbt.vector_polygons_to_raster(
        i=target_streams,
        field=target_streams_id_field,
        nodata=True,
        output=target_streams_id_raster,
        base=base_dem # Do not use breach raster as base to avoid float64 dtype
    )

    logger.info("-> Creating target stream prio raster from vector polygons")
    wbt.vector_polygons_to_raster(
        i=target_streams,
        field=target_streams_prio_field,
        nodata=True,
        output=target_streams_prio_raster,
        base=base_dem # Do not use breach raster as base to avoid float64 dtype
    )

    # Reclass stream raster
    logger.info("-> Reclassifying prio target stream raster")
    wbt.conditional_evaluation(
        i=target_streams_prio_raster,
        output=target_streams_prio1_raster,
        statement="value == 1",
        true=1,
        false=0
    )

    logger.info("-> Reclassifying non-prio target stream raster")
    wbt.conditional_evaluation(
        i=target_streams_prio_raster,
        output=target_streams_prio0_raster,
        statement="value == 0",
        true=1,
        false=0
    )

    logger.info("-> Extracting flow accumulation from seedpoint threshold and above")
    wbt.conditional_evaluation(
        i=flow_acc_ha,
        output=flow_acc_ha_threshold,
        statement=f"value >= {seed_point_threshold}",
        true=flow_acc_ha,
        false=None
    )

    logger.info("-> Extracting DEM streams")
    wbt.extract_streams(
        flow_accum=flow_acc_ha,
        output=dem_streams_extracted,
        threshold=dem_strm_thresh,
        zero_background=False
    )

    # Calculate distance to streams
    logger.info("-> Calculating distance to extracted DEM streams")
    wbt.downslope_distance_to_stream(
        dem=hydro_dem,
        streams=dem_streams_extracted,
        output=dist2dem_strm_extr
    )

    logger.info("-> Creating distance to prio target stream raster")
    wbt.downslope_distance_to_stream(
        dem=hydro_dem,
        streams=target_streams_prio1_raster,
        output=dist2stream_prio1,
        dinf=False
    )

    logger.info("-> Creating distance to non-prio target stream raster")
    wbt.downslope_distance_to_stream(
        dem=hydro_dem,
        streams=target_streams_prio0_raster,
        output=dist2stream_prio0,
        dinf=False
    )

    if seed_point_threshold is not None:
        logger.info("-> Masking distance to prio target stream raster using seed point threshold")
        wbt.conditional_evaluation(
            i=flow_acc_ha,
            output=dist2stream_prio1_masked,
            statement=f"value >= {seed_point_threshold}",
            true=dist2stream_prio1,
            false=None
        )
        logger.info("-> Masking distance to non-prio target stream raster using seed point threshold")
        wbt.conditional_evaluation(
            i=flow_acc_ha,
            output=dist2stream_prio0_masked,
            statement=f"value >= {seed_point_threshold}",
            true=dist2stream_prio0,
            false=None
        )
    else:
        dist2stream_prio1_masked = None
        dist2stream_prio0_masked = None

    logger.info("-> Calculate D8 pointer")
    wbt.d8_pointer(
        dem=hydro_dem,
        output=d8_pointer,
        esri_pntr=False
    )

    logger.info("-> Mask D8 pointer")
    wbt.conditional_evaluation(
        i=target_streams_id_raster,
        output=d8_pointer_masked,
        statement="value != nodata",
        true=None,
        false=d8_pointer
    )

    logger.info("-> Cost allocate water")
    wbt.cost_allocation(
        source=target_streams_id_raster,
        backlink=d8_pointer,
        output=target_allocation_raster
    )

    logger.info("-> Vectorizing target allocation")
    target_ref_field = "TRGT_FID"
    tools.raster_to_polygon(
        raster=target_allocation_raster,
        band=1,
        value_field_name=target_ref_field,
        value_field_type=int,
        output=target_allocation_vector
    )

    tools.left_join(
        left=target_allocation_vector,
        left_key=target_ref_field,
        right=target_streams,
        right_key=target_streams_id_field,
        add_fields=[target_streams_prio_field],
        output=target_allocation_vector_prio
    )

def calc_sti(base_dem, flow_acc, slope, sediment_transport_index): #dem_resampled
    logger.info("-> Calculate slope")
    wbt.slope(
        dem=base_dem,
        output=slope,
        zfactor=None,
        units="degrees"
    )

    logger.info("-> Calculate sediment transport index")
    wbt.sediment_transport_index(
        sca=flow_acc,
        slope=slope,
        output=sediment_transport_index,
        sca_exponent=0.4,
        slope_exponent=1.3
    )

def calc_wet(
    mf_raster, #args.mf_raster
    base_dem, #dem_resampled
    mf_resampled,
    dist2dem_strm_extr,
    wet_strm_dist, #args
    mf_wet_class_val, #args
    cell_size, #args
    mf_wet_near_streams
):
    # Find wet areas within distance to extracted streams
    logger.info("-> Resampling soil moisture raster based on DEM")
    wbt.resample(
        inputs=mf_raster,
        output=mf_resampled,
        base=base_dem,
        method="cc",
    )

    logger.info("-> Calculating wet areas within distance to extracted streams")
    wbt.raster_calculator(
        statement=f'(("{dist2dem_strm_extr}" <= {wet_strm_dist}) && ("{mf_resampled}" == {mf_wet_class_val}))*{cell_size}^2',
        output=mf_wet_near_streams
    )
