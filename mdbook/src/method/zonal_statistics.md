# Beräkna zonstatistik inom varje påverkande område

- Beräkna kortaste rinnsträckan till både prioriterade och icke-prioriterade vatten
- Beräkna statistik för markfuktighetskarta
- Beräkna maximal flödesackumulering

```dot process
digraph {
    graph[rankdir=LR, nodesep=0.3, ranksep=0.6]
    node[shape=circle, fontsize=10, width=1]
    edge[arrowsize=0.6, arrowhead=vee]

    # Data
    {
      node[shape = "plain"]
      dist_pr [ label="Distance to\n prio stream" ]
      dist_np [ label="Distance to\n non-prio stream" ]
      mf_class [ label="Soil moisture\n reclassified" ]
      mf_wetstr [ label="Soil moisture \"WET\"\n near streams" ]
      flow_acc [ label="Flow accumulation" ]
      aoi [ label="Area of interest" ]
      output [ label="Zonal stats output" ]
    }

    # Processing
    {
      node[shape="box" style=rounded]
      zs [ label="ZonalStats" style="dashed" ]
    }

    {rank=min dist_pr dist_np}
    {rank=same aoi zs output}
    {rank=max mf_class mf_wetstr flow_acc}
    {aoi, dist_pr, dist_np, mf_class, mf_wetstr, flow_acc} -> zs -> output
}
```
