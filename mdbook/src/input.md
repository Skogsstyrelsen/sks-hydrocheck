# Indata

Nedan presenteras indata som används i modellen. De specificerade produkterna är
de som använts vid utveckling av verkytget men andra underlag med motsvarande
egenskaper kan användas. Några indata är obligatoriska för att köra modellen
medan övriga är frivilliga men rekommenderade för att erhålla ett bra resultat.

| Data                        | Typ               | Krav | Produkt                                                       |
| --------------------------- | ----------------- | :--- | ------------------------------------------------------------- |
| Höjdmodell (terrängmodell)  | Raster, GeoTIFF   | Ja   | Lantmäteriets Markhöjdmodell Nedladdning, grid 1+ [^1]        |
| Diken                       | Vektor, linjer    | Nej  | SLU Dikeskartor [^2]                                          |
| Vattendrag                  | Vektor, linjer    | Nej  | Lantmäteriets Terrängkartan [^3]                              |
| Vägar + järnvägar           | Vektor, linjer    | Nej  | Lantmäteriets Terrängkartan [^3]                              |
| Väg-/järnvägstrummor        | Vektor, punkter   | Nej  | Trafikverkets datapaket Vägtrummor punkter geografisk vy [^4] |
| Recipienter med prioklasser | Vektor, polygoner | Ja   | Klassade[^5] vattenförekomster (ytor) från Terrängkartan [^3] |
| Avverkningsanmälansområden  | Vektor, polygoner | Ja   | Ytor kopplade till avverkningsanmälningar från Skogsstyrelsen |
| Markfuktighetskarta         | Raster, GeoTIFF   | Ja   | SLU Markfuktighetskarta [^6]                                  |

[^1]: <https://www.lantmateriet.se/globalassets/geodata/geodataprodukter/hojddata/mhm1_plus.pdf>

[^2]: <https://www.slu.se/institutioner/skogens-ekologi-skotsel/forskning2/dikeskartor/>

[^3]: <https://www.lantmateriet.se/sv/geodata/vara-produkter/produktlista/terrangkartan/>

[^4]: <https://lastkajen.trafikverket.se/productpackages/10170> [kräver inloggning]

[^5]: Klassning (prio/ej prio) görs med hjälp av annat underlag som anses representera recipienter som kräver extra hänsyn

[^6]: <https://www.slu.se/institutioner/skogens-ekologi-skotsel/forskning2/markfuktighetskartor/om-slu-markfuktighetskarta/>
