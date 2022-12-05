import configargparse

def setup_logging(verbose=False, log_file=None):
    import logging
    from sys import stdout
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = '%(asctime)s [%(module)s] %(levelname)s %(message)s'
    log_datefmt = '%Y-%m-%d %H:%M:%S'

    if log_file is not None:
        logging.basicConfig(filename=log_file, filemode="a", format=log_format, datefmt=log_datefmt, level=log_level)
    else:
        logging.basicConfig(stream=stdout, format=log_format, datefmt=log_datefmt, level=log_level)

if __name__ == '__main__':

    cfg_parser = configargparse.ArgParser(prog="skshc", default_config_files=['skshc.conf'])
    arg_parser = configargparse.get_argument_parser()

    cfg_parser.add('-c', '--configfile', required=False, is_config_file=True, help='config file path')
    cfg_parser.add('--logfile', dest='log_file', nargs='?', default=None, help='output to the specified log file - if not specified output redirects to stdout')
    cfg_parser.add('-v', '--verbose', dest='verbose', action="store_true", help='verbose logging mode')
    cfg_parser.add('--dem-only', dest='dem_only', action='store_true', help="process hydrological dem only")
    cfg_parser.add('--dem-workdir', dest='dem_work_dir', required=True, help='DEM working directory')
    cfg_parser.add('--workdir', dest='work_dir', required=True, help='working directory')
    cfg_parser.add('--clean-workdir', dest='clean_workdir', action="store_true", help='remove existing working directory')
    cfg_parser.add('--append-areas', dest='append_areas', nargs='?', default=None, help='area dataset to append result to')
    cfg_parser.add('--append-flowpaths', dest='append_flowpaths', nargs='?', default=None, help='flowpath dataset to append result to')
    cfg_parser.add('--epsg', dest='epsg', required=True, type=int, help='EPSG code')
    cfg_parser.add('--dem', dest='base_dem', required=True, help='base DEM')
    cfg_parser.add('--cell-size', dest='cell_size', nargs='?', type=int, default=None, help='resample dem to cell size')
    cfg_parser.add('--culverts', dest='culverts', nargs='?', default=None, help='culvert vector points')
    cfg_parser.add('--culvert-snap-tolerance', dest='culvert_snap_tolerance', nargs='?', type=float, default=None, help='tolerance used when snapping culverts to roads - infinite if ommited')
    cfg_parser.add('--culvert-buffer-size', dest='culvert_buffer_size', nargs='?', type=float, default=10.0, help='buffer zone size for culvert overlay on DEM')
    cfg_parser.add('--fill-burn-streams', dest='fill_burn_streams', nargs='?', default=None, help='vector streams for fill burning into dem')
    cfg_parser.add('--burn-streams', dest='burn_streams', nargs='?', default=None, help='vector streams for burning at roads')
    cfg_parser.add('--burn-roads', dest='burn_roads', nargs='?', default=None, help='vector roads for burning streams')
    cfg_parser.add('--burn-width', dest='burn_width', nargs='?', type=float, default=None, help='maximum road embankment width')
    cfg_parser.add('--target-streams', dest='target_streams', required=True, help='vector streams - polylines or polygons')
    cfg_parser.add('--target-streams-id-field', dest='target_streams_id_field', nargs='?', default="FID", help='target stream id field name')
    cfg_parser.add('--target-streams-prio-field', dest='target_streams_prio_field', nargs='?', default="PRIO", help='target stream prio info field name')
    cfg_parser.add('--areas', dest='areas', required=True, help='area of interest for zonal stats')
    cfg_parser.add('--area-id-field', dest='area_id_field', required=True, help='area of interest identity field')
    cfg_parser.add('--area-part-field', dest='area_part_field', required=True, help='exploded area parts id field')
    cfg_parser.add('--dem-streams-threshold', dest='dem_strm_thresh', type=float, default=10.0, help='flow acc threshold [ha] for extracting streams from DEM')
    cfg_parser.add('--mf', dest='mf_raster', required=True, help='soil moisture raster for zonal stats')
    cfg_parser.add('--wet-near-streams-distance', dest='wet_strm_dist', type=float, default=10.0, help='distance [m] from stream to map wet areas')
    cfg_parser.add('--mf-class-values', dest='mf_class_values', default=[1,2,3,4], type=int, nargs=4, help='soil moisture class raster values in order dry, damp, wet, open water')
    cfg_parser.add('--seed-point-threshold', dest='seed_point_threshold', nargs='?', type=float, default=None, help='seed point flow accumulation threshold [ha] - if not specified 3rd quartile will be used')
    cfg_parser.add('--flowpath-buffer-size', dest='flowpath_buffer_size', nargs='?', type=float, default=10.0, help='flowpath buffer size for zonal stats along line')
    cfg_parser.add('--flowpath-segment-length', dest='flowpath_segment_length', nargs='?', type=float, default=100.0, help='flowpath segment length to split into for zonal stats along line')
    cfg_parser.add('--flowpath-segment-id-field', dest='segment_id_field', required=True, help='flowpath segment id field')
    cfg_parser.add('--area-limit', dest='area_limit', nargs='?', type=int, default=None, help='max number of areas to process')
    cfg_parser.add('--threads', dest='threads', nargs='?', type=int, default=1, help='number of threads to use for flowpath iterations')

    cfg_args = cfg_parser.parse_args()

    # Arguments validation
    if (cfg_args.burn_streams and not cfg_args.burn_roads):
        arg_parser.error("--burn-streams requires --burn-roads")
    elif (not cfg_args.burn_streams and cfg_args.burn_roads):
        arg_parser.error("--burn-roads requires --burn-streams")

    for k,v in vars(cfg_args).items():
        if v is not None and isinstance(v, int) and v < 0:
            arg_parser.error(f"integer argument {k} cannot be negative")

    setup_logging(verbose=cfg_args.verbose, log_file=cfg_args.log_file)

    from skshc import dem
    dem_output = dem.main(cfg_args)

    if not cfg_args.dem_only:
        from skshc import area
        area_output = area.main(cfg_args, dem_output)
