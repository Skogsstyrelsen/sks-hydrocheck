# Ärendepolygoner med hydrologisk statistik

- Med "området" avses respektive ärendes geografiska yta.
- Eventuella ärendeegenskaper som finns med i indata beskrivs ej nedan

| Egenskap                                            | Kolumn      | Beskrivning                                                                                               |
| --------------------------------------------------- | ----------- | --------------------------------------------------------------------------------------------------------- |
| **Ärende-ID**                                       | id          | Polygonens objekt-ID                                                                                      |
| **Ärendebeteckning**                                | arende_bet  | Ärendebeteckning                                                                                          |
| **Manuell handläggning**                            | man_handl   | Bedömning manuell handläggning (0=Nej, 1=Ja)                                                              |
| **Motivering, handläggning**                        | motivering  | Motivering för eller emot manuell handläggning                                                            |
| **Avrinning till prioriterat vatten**               | prio        | Avrinning från området når prioriterat vattendrag (utan passage via ej prioriterat vatten) (0=Nej, 1=Ja)  |
| **Kortaste rinnsträcka (m) till PV**                | dstpr_min   | Minsta rinnavstånd (m) till prioriterat vattendrag                                                        |
| **Kortaste rinnsträcka (m) till icke-PV**           | dstnp_min   | Minsta rinnavstånd (m) till ej prioriterat vattendrag                                                     |
| **Blöt yta nära vattendrag**                        | wetstr_sum  | Summerad yta (m2) av blött område som ligger inom 5 m till ett vattendrag med minst 10 ha tillrinningsyta |
| **Maximal flödesackumulering (ha)**                 | flwacc_max  | Maximal flödesackumulering i en punkt inom området som specifik avrinningsyta (ha)                        |
| **Torr yta (m2)**                                   | dry         | Areal (m2) inom området som utgörs av TORR mark enl. markfuktighetskarta                                 |
| **Frisk-Fuktig yta (m2)**                           | dmp         | Areal (m2) inom området som utgörs av FRISK-FUKTIG mark enl. markfuktighetskarta                         |
| **Blöt yta (m2)**                                   | wet         | Areal (m2) inom området som utgörs av BLÖT mark enl. markfuktighetskarta                                 |
| **Öppet vatten (m2)**                               | wtr         | Areal (m2) inom området som utgörs av ÖPPET VATTEN enl. markfuktighetskarta                              |
| **Torr yta (%)**                                    | dry_frac    | Andel av området som utgörs av TORR mark enl. markfuktighetskarta                                        |
| **Frisk-Fuktig yta (%)**                            | dmp_frac    | Andel av området som utgörs av FRISK-FUKTIG mark enl. markfuktighetskarta                                |
| **Blöt yta (%)**                                    | wet_frac    | Andel av området som utgörs av BLÖT mark enl. markfuktighetskarta                                        |
| **Öppet vatten (%)**]                               | wtr_frac    | Andel av området som utgörs av ÖPPET VATTEN enl. markfuktighetskarta                                     |
| **Recipient-ID**                                    | trgt_fid    | Objekt-ID för recipienten (vattendragsyta)                                                                |
| **Sedimenttransportindex nedströms (medel)**        | st_avg_avg  | Medelvärde av genomsnittligt sedimenttransportindex för rinnvägar nedströms området                       |
| **Sedimenttransportindex nedströms (övre kvartil)** | st_avg_q3   | Övre kvartil av genomsnittligt sedimenttransportindex för rinnvägar nedströms området                     |
| **Lutning nedströms (medel)**                       | slp_avg_avg | Medelvärde av genomsnittlig flödesvägslutning för rinnvägar nedströms området                             |
| **Lutning nedströms (övre kvartil)**                | slp_avg_q3  | Övre kvartil av genomsnittlig flödesvägslutning för rinnvägar nedströms området                           |
| **Flödesackumulering nedströms (medel)**            | fla_avg_avg | Medelvärde av genomsnittlig flödesackumulering för rinnvägar nedströms området                            |
| **Flödesackumulering nedströms (övre kvartil)**     | fla_avg_q3  | Övre kvartil av genomsnittlig flödesackumulering för rinnvägar nedströms området                          |
