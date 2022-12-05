# Rinnvägslinjer för avrinning nedströms ärendeytor

- Rinnvägar är uppdelade i segment om X meter (standard är 100 m)

| Egenskap                                   | Kolumn      | Beskrivning                                                                                 |
| ------------------------------------------ | ----------- | ------------------------------------------------------------------------------------------- |
| **Segment-ID**                             | segm_id     | Linjesegmentets objekt-ID                                                                   |
| **Ärende-ID**                              | area_id     | Objekt-ID för ärendepolygon där avrinnningen startar                                        |
| **Recipient-ID**                           | trgt_fid    | Objekt-ID för målet (vattendragsyta)                                                        |
| **Avrinning till prioriterat vatten**      | prio        | Avrinning når prioriterat vattendrag (utan passage via ej prioriterat vatten) (0=Nej, 1=Ja) |
| **Sedimenttransportindex segment (medel)** | st_avg_avg  | Genomsnittligt sedimenttransportindex för rinnvägssegementet                                |
| **Lutning segment (medel)**                | slp_avg_avg | Genomsnittlig flödesvägslutning för rinnvägssegementet                                      |
| **Flödesackumulering segment (medel)**     | fla_avg_avg | Genomsnittlig flödesackumulering för rinnvägssegementet                                     |
