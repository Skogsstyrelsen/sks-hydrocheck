# Beräkna regionala hydrologiska egenskaper

> Med *regional* avses hela det område, t.ex. ett större vattendrags
> avrinningsområde, som verktyget ska kunna utföra beräkningar för. Området
> mostvarar utbredningen för höjdmodellen i föregeånde steg och de beräknade
> egenskaperna kopplas i efterföljande steg till ärendepolygoner och rinnvägar
> inom området.

Följande moment ingår i processen för beräkning av regionala hydrologiska
egenskaper som resulterar i ett antal raster-dataset, d.v.s. att för varje
ytenhet (beroende på höjdmodellens upplösning) presentera information som på
något sätt är kopplat till flödesackumulering. Bearbetningen kan vara relativt
tidskrävande men resultatet för hela (regionala) området kan återanvändas för
återkommande bearbetning av flera avverkningsärendeområden.

- Beräkna flödesackumulering som specfikt avrinningsområde [m2]
- Beräkna flödesackumulering som specfikt avrinningsområde [ha]
- Extrahera vattendrag från flödesackumulering > `x` ha
- Beräkna avstånd till extraherade vattendrag - *nära vattendrag*
- Extrahera markfuktighet *blöt* vid *nära vattendrag*
- Beräkna lutning i varje cell
- Beräkna sedimenttransportindex i varje cell

```dot process
digraph {
    graph[rankdir=LR, nodesep=0.1, ranksep=0.3]
    node[fontsize=10]
    edge[arrowsize=0.6, arrowhead=vee]

    # Data
    {
      node[shape = "plain"]
      breached_dem [ label="Breached\n DEM" ]
      flowacc_data [ label="Flow\n accumulation\n [m2]" ]
      flowacc_ha_data [ label="Flow\n accumulation\n [ha]" ]
      extract_streams_data [ label="Extracted\n streams" ]
    }

    # Joints
    {
      node[shape="point" height=0.01]
      flowacc_joint
      flowacc_ha_joint
    }

    # Processing
    {
      node[shape="box" style=rounded]
      flowacc_calc [ label="D8FlowAccumulation" ]
      flowacc_ha_calc [ label="RasterCalculator\n (flow.acc / 1e4)" ]
      extract_streams_calc [ label="ConditionalEvaluation\n (flow.acc > x ha)" ]
    }

    breached_dem -> flowacc_calc
    flowacc_calc -> flowacc_joint [arrowhead=none]
    flowacc_joint -> {flowacc_ha_calc, flowacc_data}
    flowacc_ha_calc -> flowacc_ha_joint [arrowhead=none]
    flowacc_ha_joint -> {extract_streams_calc, flowacc_ha_data}
    extract_streams_calc -> extract_streams_data
}
```
*Figur 3.2.A. Process för beräkning av olika representationer av flödesackumulering*

## Egenskaper med koppling till recipient

> Recipienter är de vattendrag som det är av intresse att studera avrinning till
> från påverkande avrinningsområden, d.v.s. avvkerkningsområden.

I följande steg beräknas allokering, d.v.s. vilken recipient som berörs av vad,
samt rinnavstånd till recipient. Indata är vektoriserade ytor som representerar
vattendragen och måste ha ett ID samt vara klassade som prioriterat eller icke
prioriterat vattendrag (PRIO=1, PRIO=0).

- Beräkna flödesriktningsraster (D8)
- Maska bort vattenkroppar från flödesriktningsraster
  > Detta steg "inaktiverar" avrinning i maskningsområdet (recipienterna) vilket
  > ger resultatet att allokeringsspårning stannar när en recipient har nåtts.
- Omvandla recipientvektorytor till raster med ID
- Omvandla recipientvektorytor till raster med information om prioritet
- Separera prio-raster i två raster - prio, ej prio
- Beräkna raster med rinnavstånd till prio / ej prio
- Vektorisera allokeringsraster till polygoner med recipient-ID
- Hämta information om prioritet från recipientpolygoner till allokeringspolygoner

```dot process
digraph {
    graph[rankdir=LR, nodesep=0.1, ranksep=0.3]
    node[shape=circle, fontsize=10, width=0.5]
    edge[arrowsize=0.6, arrowhead=vee]

    # Data
    {
      node[shape = "plain"]
      trgt_vec [ label="Target streams\n (vector)" ]
      breached_dem [ label="Breached\n DEM" ]
      aoi [ label="Area of interest" ]
    }

    # Processing
    {
      node[shape="box" style=rounded]
      p2r [ label="PolygonToRaster" ]
      ce_pr [ label="ConditionalEvaluation\n (value==1)" ]
      ce_np [ label="ConditionalEvaluation\n (value==0)" ]
      dist_pr [ label="DistanceToStream\n (prio)" ]
      dist_np [ label="DistanceToStream\n (non-prio)" ]
      zs [ label="ZonalStats" style="dashed" ]
    }

    {rank=same aoi zs}
    trgt_vec -> p2r -> {ce_pr,ce_np}
    breached_dem -> {dist_pr,dist_np} -> zs
    ce_pr -> dist_pr
    ce_np -> dist_np
    aoi -> zs
}
```
*Figur 3.2.B. Process för beräkning av allokering och rinnavstånd till recipienter*