# Metodöversikt

Processen för modelleringen kan grovt delas upp i fyra faser enligt nedan.

- [1. Förberedelser av hydrologisk höjdmodell](./prepare_hydrologial_dem.md)
- [2. Beräkna regionala hydrologiska egenskaper](./calculate_regional_hydrology.md)
- [3. Beräkna zonstatistik inom varje påverkande område](./zonal_statistics.md)
- [4. Beräkna rinnvägar från påverkande område](./calculate_flowpaths.md)

```dot process
digraph {
    graph[rankdir=LR, nodesep=0.1, ranksep=0.2]
    edge[arrowsize=0.6, arrowhead=vee]
    node[fontsize=10, width=0.5]
    rankdir=TD

    # Data
    subgraph cluster_input {
      label="INDATA";
      graph[style=dotted];
      node[shape=plain]
      {
        node[fontsize="14"]
        areas [ label="Ärendeområden"]
        recipients [ label="Recipienter"]
        orig_dem [ label="Höjdmodell"]
      }
      culverts [ label="Trummor" ]
      roads [ label="Väg, järnväg" ]
      streams [ label="Vattendrag, diken" ]
      mf [ label="Markfuktighetskarta" ]
    }

    # Processing

    subgraph cluster_process {
      label="BEARBETNING"
      node[shape="box" style=rounded]
      hydro_dem [ label="1. Hydrologisk höjdmodell" ]
      regional_hydro [ label="2. Hydrologiska egenskaper\n(regionalt) och allokering"]
      local_hydro [ label="3. Hydrologiska egenskaper (lokalt)"]
      trace_flowpath [ label="4. Spårning av rinnvägar"]
    }

    # Result
    subgraph cluster_result {
      label="RESULTAT";
      node [ color="red" penwidth="2" fontsize="14"]
      area_stats [ label="Ärendeområden med hydrologisk information"]
      flowpaths [ label="Rinnvägar med hydrologisk information"]
    }
    {orig_dem, culverts, roads, streams} -> hydro_dem
    {local_hydro} -> area_stats
    {hydro_dem, recipients} -> regional_hydro -> flowpaths
    {areas, mf, regional_hydro} -> local_hydro -> trace_flowpath -> flowpaths -> area_stats
}
```
