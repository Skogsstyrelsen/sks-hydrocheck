import geopandas as gpd
import rasterio as rio
from rasterstats import zonal_stats
from shapely.ops import linemerge
from shapely.geometry import LineString, Point
from skshc.utils import Cache
from numpy import quantile, nanquantile, float_

cache = Cache().cache_handler # Regular cache
gdf_or_file = lambda s: s if isinstance(s, gpd.geodataframe.GeoDataFrame) else gpd.read_file(s)

@cache
def left_join(left, right, left_key, add_fields, output, right_key=None):
    left_data = gdf_or_file(left)
    right_data = gdf_or_file(right)
    joined = left_data.join(right_data.set_index(right_key or left_key)[add_fields], how="left", on=[left_key])
    joined.to_file(output)
    return output

@cache
def join_container(input, container, output, drop_container_index=True):
    input_gdf = gdf_or_file(input)
    container_gdf = gdf_or_file(container)
    intersection = input_gdf.sjoin(container_gdf, how="left", predicate="within")
    if drop_container_index:
        intersection.drop("index_right", inplace=True, axis=1)
    intersection.to_file(output)
    return output

@cache
def join_target_info(source, target, key_fields, rank_fields, rank_fields_asc, output, epsg=None, flow_acc=None, flow_acc_threshold=None):
    src_df = gdf_or_file(source)
    trgt_df = gdf_or_file(target)
    if epsg is not None:
        src_df = src_df.set_crs(epsg=epsg, allow_override=True)
        trgt_df = trgt_df.set_crs(epsg=epsg, allow_override=True)
    intersect = src_df[key_fields + ['geometry']].overlay(trgt_df, how="intersection")

    if flow_acc is not None and flow_acc_threshold is not None:
        # Ignore target allocation intersecting areas with flow acc below threshold
        zs = zonal_stats(
            intersect,
            flow_acc,
            stats='max',
            geojson_out=True
        )
        intersect = gpd.GeoDataFrame.from_features(zs).query(f"max >= {flow_acc_threshold}")
        intersect.drop('max', axis=1, inplace=True)

    # Select one target per area by sorting first on prio then on biggest overlap
    intersect.sort_values(
        by=rank_fields,
        ascending=rank_fields_asc,
        inplace=True,
        key=lambda col: [x.area if col.name == 'geometry' else x for x in col]
    )
    intersect.drop_duplicates(subset=key_fields, keep='first', inplace=True)
    intersect.drop('geometry', axis=1, inplace=True)
    merged = src_df.merge(intersect, how="left", on=key_fields)
    merged.to_file(output)
    return output

@cache
def explode_areas(aggregated_input, part_field, output):
    gdf = gdf_or_file(aggregated_input)
    gdf_exploded = gdf.explode()
    gdf_exploded[part_field] = gdf_exploded.index.get_level_values(1)+1
    gdf_exploded_indexed = gdf_exploded.reset_index(drop=True)
    gdf_exploded_indexed.to_file(output)
    return output

@cache
def batch_zonal_stats(base_shape, key_fields, input_map, output):
    base_data = gdf_or_file(base_shape)
    for i in input_map:
        zs = zonal_stats(base_shape, i["raster"], stats=i["stats"], geojson_out=True)
        zsdf = gpd.GeoDataFrame.from_features(zs)[key_fields+i["stats"]]
        zsdf.rename(dict(zip(i["stats"], i["out_cols"])), axis=1, inplace=True)
        base_data = base_data.merge(zsdf, how="left", on=key_fields)
    base_data.to_file(output)
    return output

@cache
def normalize_by_length(lines, fields, output):
    gdf = gdf_or_file(lines)
    gdf[fields] = gdf[fields].div(gdf.geometry.length, axis=0)
    gdf.to_file(output)
    return output

@cache
def zonal_class_stats(base_shape, raster, col_map, output, fracs=False):
    cats, cols = [list(x) for x in zip(*col_map.items())]
    base_cols = gdf_or_file(base_shape).columns
    new_cols = base_cols.insert(-1, cats).to_list()
    cat_stats = zonal_stats(base_shape, raster, categorical=True, geojson_out=True)
    csdf = gpd.GeoDataFrame.from_features(cat_stats, columns=new_cols)
    csdf.rename(col_map, axis=1, inplace=True)
    if fracs:
        frac_cols = [f"{c}_frac" for c in cols]
        csdf[frac_cols] = csdf[cols].apply(lambda x: x / x.sum(), axis=1)
    csdf.to_file(output)
    return output

def q3(x, ignore_nan=True):
    if ignore_nan:
        return nanquantile(x, q=0.75)
    return quantile(x, q=0.75)

@cache
def clean_result(input, output, epsg=None):
    gdf = gdf_or_file(input)
    if epsg is not None:
        gdf = gdf.set_crs(epsg=epsg, allow_override=True)
    float_columns = [c for c in gdf.columns if gdf[c].dtype == float_]
    # Round floats
    gdf[float_columns] = gdf[float_columns].round(2)
    gdf.to_file(output, driver='GeoJSON')
    return output

@cache
def merge_stats(left_shape, right_shape, left_keys, right_keys, aggs, output, prio_field=None):
    left = gdf_or_file(left_shape)
    right = gdf_or_file(right_shape)

    # Group initially by prio field, if specified ...
    right_grouped = right.groupby(by=right_keys if prio_field is None else right_keys+[prio_field]).agg(aggs).reset_index()
    right_grouped.columns=[f"{p}_{s}".replace("mean", "avg") if p in aggs else p for p,s in right_grouped.columns]
    # ... and sort by prio field descending to remove influence from non-prio
    if prio_field is not None:
        right_grouped.sort_values(
            by=[prio_field],
            ascending=[False],
            inplace=True
        )
        right_grouped.drop_duplicates(subset=right_keys, keep='first', inplace=True)
        right_grouped.drop(prio_field, axis=1, inplace=True)

    merged = left.join(right_grouped.set_index(right_keys), how="left", on=left_keys)
    merged.to_file(output, driver='GeoJSON')
    return output

@cache
def create_culvert_zones(culvert_points, roads, output, tolerance=None, buffer_size=10):
    # Snap to roads
    snap_lines=gdf_or_file(roads).geometry.unary_union
    snapped_points=gdf_or_file(culvert_points)
    snapped_points['geometry'] = snapped_points.apply(snap_points_to_line, args=(snap_lines, tolerance), axis=1)
    # Buffer snapped points and save to file
    snapped_points.buffer(buffer_size).to_file(output)
    return output

@cache
def raster_to_polygon(raster, band, value_field_name, value_field_type, output):
    with rio.open(raster) as src:
        image = src.read(band)
        results = [
            {'properties': {value_field_name: (value_field_type)(v)}, 'geometry': s}
            for s, v in rio.features.shapes(image, transform=src.transform)
            if v != src.nodata
        ]
    gdf = gpd.GeoDataFrame.from_features(results)
    gdf.to_file(output)

# Dataframe tools

def split_lines(gdf, distance, part_id_column):
    def cut_line(line, distance, lines):
        # Cuts a line in several segments at a distance from its starting point
        if distance <= 0.0 or distance >= line.length:
            return [LineString(line)]
        coords = list(line.coords)
        for i, p in enumerate(coords):
            pd = line.project(Point(p))
            if pd == distance:
                return [
                    LineString(coords[:i+1]),
                    LineString(coords[i:])
                    ]
            if pd > distance:
                cp = line.interpolate(distance)
                lines.append(LineString(coords[:i] + [(cp.x, cp.y)]))
                line = LineString([(cp.x, cp.y)] + coords[i:])
                if line.length > distance:
                    cut_line(line, distance, lines)
                else:
                    lines.append(LineString([(cp.x, cp.y)] + coords[i:]))
                return lines

    def cut_transform(x, distance):
        x['geometry'] = cut_line(x['geometry'], float(distance), list())
        return x

    # Cut lines
    gdf = gdf.apply(cut_transform, args=(distance,), axis=1)
    # Explode multilines
    gdf = gdf.explode('geometry')

    # Create and store new index
    gdf.reset_index(drop=True, inplace=True)
    gdf[part_id_column]=gdf.index

    # Dataframe is converted to regular Pandas dataframe in previous steps and must be explicitly converted
    gdf = gpd.GeoDataFrame(gdf, geometry='geometry')

    return gdf

def append_result(target, source, driver='GeoJSON', index_column=None):
    """Appends file or geodataframe to existing file"""
    target_gdf = gdf_or_file(target)
    source_gdf = gdf_or_file(source)
    joined = target_gdf.append(source_gdf, ignore_index=True)
    if index_column is not None:
        joined[index_column]=joined.index
    joined.to_file(target, driver=driver)
    return target

## Dataframe apply functions

def merge_transform(x):
    try:
        t = linemerge(x['geometry'])
        if isinstance(t, LineString):
            x['geometry']=t
        else:
            x['geometry']=t.geoms
        return x
    except:
        return x

def snap_points_to_line(row, line, tolerance=None):
    orig_geom = row.geometry
    snapped_geom = line.interpolate(line.project(orig_geom))
    if tolerance is not None and orig_geom.distance(snapped_geom) > tolerance:
        return orig_geom
    return snapped_geom
