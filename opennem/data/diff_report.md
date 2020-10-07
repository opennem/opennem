
Opennem Report
==============

Contents
========

* [Opennem Report](#opennem-report)
* [Summary](#summary)
* [Renamed Stations](#renamed-stations)
* [Changed Fueltechs](#changed-fueltechs)
* [Changed Capacities](#changed-capacities)
* [Stations not in current](#stations-not-in-current)
* [New Stations](#new-stations)

# Opennem Report

# Summary

||Prod|Version 3|
| :---: | :---: | :---: |
|Stations|402|530|
|Units|569|855|

# Renamed Stations

- `Earthpower Biomass` renamed to `Earthpower`
- `Hume (NSW)` renamed to `Hume`
- `Jindabyne (Mini Hydro)` renamed to `Jindabyne Small`
- `Jindabyne Pump` renamed to `Jindabyne Pump At Guthega`
- `Jounama (Mini Hydro)` renamed to `Jounama Small`
- `Kincumber` renamed to `Kincumber Site`
- `Limondale SF` renamed to `Limondale 1`
- `Lucas Heights 2` renamed to `Lucas Heights 1`
- `St George Leagues Club` renamed to `St George Leagues`
- `West Nowra` renamed to `West Nowra Generation Facility`
- `Western Suburbs League Club` renamed to `Western Suburbs League Club Campbelltown`
- `Willoughby` renamed to `Nine Network Willoughby`
- `Woodlawn Bioreactor` renamed to `Woodlawn Energy`
- `Woy Woy` renamed to `Woy Woy Site`
- `Darling Downs` renamed to `Darling Downs Solar Farm`
- `KRC Co-gen` renamed to `KRC`
- `Kidston` renamed to `Kidston Project`
- `Moranbah` renamed to `Moranbah Generation Project`
- `Mt Emerald` renamed to `Mount Emerald`
- `Rocky Point Co-gen` renamed to `Rocky Point`
- `Roma` renamed to `Roma Station`
- `Southbank Institute Of Technology` renamed to `Southbank Institute Of Technology 1`
- `Sunshine Coast` renamed to `Sunshine Coast Solar Farm`
- `Tableland Mill` renamed to `Tableland Mill 2`
- `Veolia Ti Tree Bio Reactor` renamed to `Veolia Ti Tree`
- `Amcor Glass` renamed to `Amcor Glass Gawler`
- `Bolivar Waste Water Treatment` renamed to `Water Bolivar`
- `Dalrymple North Battery` renamed to `Dalrymple North`
- `Dry Creek` renamed to `Dry Creek Station`
- `Lake Bonney 2` renamed to `Lake Bonney Windfarm`
- `Lake Bonney Bess1` renamed to `Lake Bonney`
- `Mintaro` renamed to `Mintaro Station`
- `Port Stanvac` renamed to `Pt Stanvac`
- `Tailem Bend 1` renamed to `Tailem Bend Project 1`
- `Tataria Bordertown` renamed to `Tataria`
- `Terminal Storage (Mini Hydro)` renamed to `Terminal`
- `Catagunya/Liapootah/Wayatinah` renamed to `Catagunya / Liapootah / Wayatinah`
- `Lemonthyme/Wilmot` renamed to `Lemonthyme / Wilmot`
- `Port Latta` renamed to `Port Latta Generator`
- `Woolnorth` renamed to `Woolnorth Studland Bay / Bluff Point`
- `Ballarat Battery` renamed to `Ballarat Energy`
- `Ballarat Hospital` renamed to `Ballarat Base Hospital`
- `Bogong/Mackay` renamed to `Bogong / Mackay`
- `Brooklyn` renamed to `Brooklyn U13`
- `Bulgana Green Hub` renamed to `Bulgana Green`
- `Energy Brix` renamed to `Morwell`
- `Gannawarra Battery` renamed to `Gannawarra Energy`
- `Hallam` renamed to `South East Water Halllam`
- `Hepburn Wind` renamed to `Hepburn Community`
- `Hume (VIC)` renamed to `Hume`
- `Mornington Waste Disposal` renamed to `Mornington`
- `Rubicon` renamed to `Rubicon Mountain`
- `Shepparton Wastewater Treatment` renamed to `Shepparton Facility`
- `Snowtown` renamed to `Snowtown 1`
- `Tatura Biomass` renamed to `Tatura Generator`
- `Traralgon Network Support` renamed to `Traralgon`
- `Valley Peaking` renamed to `Valley Peaking Facility`
- `Collie` renamed to `Collie G1`
- `Geraldton diesel` renamed to `Tesla Geraldton`
- `Kambalda` renamed to `Southern Cross`
- `Kemerton diesel` renamed to `Tesla Kemerton`
- `Kwinana` renamed to `Kwinana 3`
- `Kwinana Swift` renamed to `Kwinana 1`
- `Manjimup` renamed to `Bridgetown`
- `Metro` renamed to `Ambrisolar`
- `Mirrabooka` renamed to `Atlas`
- `Muja CD` renamed to `Muja`
- `Neerabup` renamed to `Neerabup 1`
- `Newgen Kwinana` renamed to `Kwinana`
- `Northam diesel` renamed to `Tesla Northam`
- `Picton diesel` renamed to `Tesla Picton`
- `Pinjara` renamed to `Pinjarra`
- `Richgro` renamed to `Cleantech Biogas`

# Changed Fueltechs

- Broadwater (`BWTR1`) fueltech `bioenergy_biomass` changed to `bioenergy_biogas`
- Condong (`CONDONG1`) fueltech `bioenergy_biomass` changed to `bioenergy_biogas`
- Wilga Park (`WILGAPK`) fueltech `gas_wcmg` changed to `gas_recip`
- Wilga Park B (`WILGB01`) fueltech `gas_wcmg` changed to `gas_recip`
- Braemar (`BRAEMAR1`) fueltech `gas_wcmg` changed to `gas_ocgt`
- Braemar (`BRAEMAR2`) fueltech `gas_wcmg` changed to `gas_ocgt`
- Braemar (`BRAEMAR3`) fueltech `gas_wcmg` changed to `gas_ocgt`
- Braemar 2 (`BRAEMAR5`) fueltech `gas_wcmg` changed to `gas_ocgt`
- Braemar 2 (`BRAEMAR6`) fueltech `gas_wcmg` changed to `gas_ocgt`
- Braemar 2 (`BRAEMAR7`) fueltech `gas_wcmg` changed to `gas_ocgt`
- Daandine (`DAANDINE`) fueltech `gas_wcmg` changed to `gas_recip`
- Wyong (`HAUGHT11`) fueltech `bioenergy_biogas` changed to `solar_utility`
- Moranbah Generation Project (`MORANBAH`) fueltech `gas_wcmg` changed to `gas_recip`
- Oaky Creek (`OAKYCREK`) fueltech `gas_wcmg` changed to `gas_recip`
- Roghan Road (`EDLRGNRD`) fueltech `bioenergy_biomass` changed to `bioenergy_biogas`
- Wivenhoe (`W/HOE#1`) fueltech `pumps` changed to `hydro`
- Wivenhoe (`W/HOE#2`) fueltech `pumps` changed to `hydro`
- Water Bolivar (`BOLIVAR1`) fueltech `pumps` changed to `bioenergy_biogas`
- Lake Bonney (`LBBL1`) fueltech `battery_charging` changed to ``
- Shepparton Facility (`SHEP1`) fueltech `bioenergy_biomass` changed to `bioenergy_biogas`
- Tatura Generator (`TATURA01`) fueltech `bioenergy_biomass` changed to `bioenergy_biogas`

# Changed Capacities

- Mugga Lane (`MLSP1`) capacity `13.6` changed to `12.0`
- Appin (`APPIN`) capacity `55.62` changed to `55.0`
- Bankstown Sports Club (`BANKSPT1`) capacity `2.0` changed to `1.0`
- Bayswater (`BW04`) capacity `685.0` changed to `660.0`
- Boco Rock (`BOCORWF1`) added capacity `113.0`
- Bomen (`BOMENSF1`) capacity `100.012` changed to `121.0`
- Broken Hill (`BROKENH1`) capacity `53.0` changed to `27.0`
- Capital (`CAPTL_WF`) capacity `140.7` changed to `140.0`
- Capital East (`CESF1`) capacity `0.205` changed to `1.0`
- Coleambally (`COLEASF1`) capacity `150.3` changed to `180.0`
- Glennies Creek (`GLENNCRK`) capacity `12.78` changed to `12.0`
- Grange Avenue (`GRANGEAV`) capacity `1.26` changed to `2.0`
- Griffith (`GRIFSF1`) capacity `30.0` changed to `27.0`
- Gullen Range (`GULLRWF1`) added capacity `165.0`
- Gunning (`GUNNING1`) capacity `46.5` changed to `47.0`
- Keepit (`KEEPIT`) capacity `7.2` changed to `6.0`
- Limondale 2 (`LIMOSF21`) capacity `28.98` changed to `38.0`
- Limondale 1 (`LIMOSF11`) capacity `220.0` changed to `275.0`
- Lucas Heights 2 (`LUCAS2S2`) capacity `17.25` changed to `5.0`
- Manildra (`MANSLR1`) capacity `50.0` changed to `25.0`
- Moree (`MOREESF1`) capacity `56.0` changed to `57.0`
- Mt Piper (`MP1`) capacity `660.0` changed to `700.0`
- Mt Piper (`MP2`) capacity `660.0` changed to `700.0`
- Parkes (`PARSF1`) capacity `50.5` changed to `55.0`
- Silverton (`STWF1`) capacity `198.94` changed to `198.0`
- Smithfield (`SITHE01`) capacity `185.0` changed to `39.0`
- Taralga (`TARALGA1`) capacity `27.0` changed to `106.0`
- The Drop (`THEDROP1`) capacity `2.5` changed to `3.0`
- White Rock (`WRSF1`) capacity `20.0` changed to `22.0`
- White Rock (`WRWF1`) capacity `172.48` changed to `175.0`
- White Rock (`WRSF1`) capacity `20.0` changed to `22.0`
- White Rock (`WRWF1`) capacity `172.48` changed to `175.0`
- Wilga Park B (`WILGB01`) capacity `6.0` changed to `12.0`
- Nine Network Willoughby (`NINEWIL1`) capacity `1.28` changed to `3.0`
- Baking Board (`BAKING1`) capacity `14.7` changed to `17.0`
- Barcaldine (`BARCSF1`) capacity `20.0` changed to `10.0`
- Browns Plains (`BPLANDF1`) capacity `1.03` changed to `2.0`
- Childers (`CHILDSF1`) capacity `55.87` changed to `64.0`
- Coopers Gap (`COOPGWF1`) capacity `122.56` changed to `452.0`
- Darling Downs (`DDPS1`) capacity `280.0` changed to `121.0`
- Daydream (`DAYDSF1`) capacity `167.75` changed to `79.0`
- Emerald (`EMERASF1`) capacity `72.0` changed to `88.0`
- Hamilton (`HAMISF1`) capacity `57.5` changed to `57.0`
- Wyong (`HAUGHT11`) capacity `2.246` changed to `132.0`
- Hayman (`HAYMSF1`) capacity `57.75` changed to `57.0`
- Hughenden (`HUGSF1`) capacity `18.0` changed to `10.0`
- Kareeya (`KAREEYA1`) capacity `21.6` changed to `21.0`
- Kareeya (`KAREEYA2`) capacity `21.6` changed to `21.0`
- Kareeya (`KAREEYA3`) capacity `21.6` changed to `21.0`
- Kareeya (`KAREEYA4`) capacity `21.6` changed to `21.0`
- Longreach (`LRSF1`) capacity `14.0` changed to `17.0`
- Mackay (`MACKAYGT`) capacity `34.0` changed to `30.0`
- Maryrorough (`MARYRSF1`) capacity `34.5` changed to `33.0`
- Moranbah North (`MBAHNTH`) capacity `63.84` changed to `63.0`
- Mount Emerald (`MEWF1`) capacity `127.65` changed to `180.0`
- Mt Stuart (`MSTUART1`) capacity `146.0` changed to `144.0`
- Mt Stuart (`MSTUART2`) capacity `146.0` changed to `144.0`
- Mt Stuart (`MSTUART3`) capacity `131.5` changed to `131.0`
- Oakey 1 (`OAKEY1SF`) capacity `25.0` changed to `30.0`
- Oakey 2 (`OAKEY2SF`) capacity `55.64` changed to `65.0`
- Roghan Road (`EDLRGNRD`) capacity `1.15` changed to `2.0`
- Rugby Run (`RUGBYR1`) capacity `65.0` changed to `83.0`
- Stapylton (`STAPYLTON1`) capacity `2.14` changed to `3.0`
- Sun Metals (`SMCSF1`) capacity `118.0` changed to `117.0`
- Tarong North (`TNPS1`) capacity `450.0` changed to `443.0`
- Veolia Ti Tree (`TITREE`) capacity `4.4` changed to `2.0`
- Whitsunday (`WHITSF1`) capacity `57.5` changed to `57.0`
- Yarranlea (`YARANSF1`) capacity `102.96` changed to `121.0`
- Bungala Two (`BNGSF2`) capacity `110.0` changed to `135.0`
- Hallett 1 (`HALLWF1`) capacity `94.5` changed to `95.0`
- Lake Bonney (`LKBONNY1`) capacity `80.5` changed to `81.0`
- Port Lincoln (`POR03`) capacity `23.5` changed to `23.0`
- Pt Stanvac (`STANV1`) capacity `29.0` changed to `58.0`
- Pt Stanvac (`STANV2`) capacity `29.0` changed to `58.0`
- Snuggery (`SNUG1`) capacity `63.0` changed to `21.0`
- Snuggery (`SNUGNL1`) capacity `21.0` changed to `25.0`
- Starfish Hill (`STARHLWF`) capacity `33.0` changed to `35.0`
- Tataria (`TATIARA1`) capacity `0.48` changed to `1.0`
- Willogoleche (`WGWF1`) capacity `27.44` changed to `119.0`
- Wingfield 1 (`WINGF1_1`) capacity `4.1` changed to `5.0`
- Wingfield 2 (`WINGF2_1`) capacity `4.1` changed to `5.0`
- Butlers Gorge (`BUTLERSG`) capacity `12.2` changed to `15.0`
- Catagunya / Liapootah / Wayatinah (`LI_WY_CA`) capacity `173.7` changed to `173.0`
- Cattle Hill (`CTHLWF1`) capacity `153.6` changed to `148.0`
- George Town (`GEORGTN1`) capacity `15.0` changed to `30.0`
- Granville Harbour (`GRANWF1`) capacity `111.6` changed to `111.0`
- Paloona (`PALOONA`) capacity `28.0` changed to `33.0`
- Port Latta Generator (`PORTLAT1`) capacity `23.0` changed to `11.0`
- Que River (`QUERIVE1`) capacity `48.0` changed to `24.0`
- Rowallan (`ROWALLAN`) capacity `10.5` changed to `11.0`
- Waterloo (`WATERLWF`) capacity `130.8` changed to `130.0`
- Woolnorth Studland Bay / Bluff Point (`WOOLNTH1`) added capacity `140.0`
- Bairnsdale (`BDL01`) capacity `47.0` changed to `46.0`
- Bairnsdale (`BDL02`) capacity `47.0` changed to `46.0`
- Bald Hills (`BALDHWF1`) capacity `106.6` changed to `59.0`
- Ballarat Base Hospital (`BBASEHOS`) capacity `3.0` changed to `1.0`
- Banimboola (`BAPS`) capacity `12.85` changed to `12.0`
- Bannerton (`BANN1`) capacity `100.0` changed to `50.0`
- Bogong / Mackay (`MCKAY1`) capacity `140.0` changed to `53.0`
- Bogong / Mackay (`MCKAY2`) capacity `50.0` changed to `53.0`
- Broadmeadows (`BROADMDW`) capacity `6.18` changed to `5.0`
- Bulgana Green (`BULGANA1`) capacity `204.4` changed to `87.0`
- Bulgana Green (`BULGANA1`) capacity `204.4` changed to `182.0`
- Cherry Tree (`CHYTWF1`) capacity `57.6` changed to `57.0`
- Clayton (`CLAYTON`) capacity `12.0` changed to `11.0`
- Crowlands (`CROWLWF1`) capacity `79.95` changed to `79.0`
- Dartmouth (`DARTM1`) capacity `185.0` changed to `150.0`
- Dundonnell (`DUNDWF3`) capacity `121.8` changed to `121.0`
- Eildon (`EILDON1`) added capacity `60.0`
- Eildon (`EILDON3`) capacity `4.5` changed to `5.0`
- Elaine (`ELAINWF1`) capacity `83.6` changed to `83.0`
- Gannawarra (`GANNSF1`) capacity `55.0` changed to `25.0`
- Gannawarra Energy (`GANNBG1`) capacity `25.33` changed to `30.0`
- Gannawarra Energy (`GANNBL1`) capacity `30.875` changed to `30.0`
- Glenmaggie (`GLENMAG1`) capacity `1.9` changed to `4.0`
- South East Water Halllam (`HLMSEW01`) capacity `0.25` changed to `1.0`
- Karadoc (`KARSF1`) capacity `96.9` changed to `104.0`
- Loy Yang B (`LOYYB1`) capacity `535.0` changed to `500.0`
- Loy Yang B (`LOYYB2`) capacity `580.0` changed to `500.0`
- Maroona (`MAROOWF1`) capacity `7.2` changed to `6.0`
- Murra Warra (`MUWAWF1`) capacity `225.7` changed to `231.0`
- Numurkah (`NUMURSF1`) capacity `107.52` changed to `74.0`
- Rubicon Mountain (`RUBICON`) capacity `2.7` changed to `13.0`
- Springvale (`SVALE1`) capacity `4.2` changed to `5.0`
- Wemen (`WEMENSF1`) capacity `97.5` changed to `97.0`
- West Kiewa (`WKIEWA1`) capacity `34.0` changed to `31.0`
- West Kiewa (`WKIEWA2`) capacity `34.0` changed to `31.0`
- Yallourn W (`YWPS1`) capacity `350.0` changed to `360.0`
- Yallourn W (`YWPS2`) capacity `350.0` changed to `360.0`
- Yallourn W (`YWPS3`) capacity `375.0` changed to `380.0`
- Yallourn W (`YWPS4`) capacity `375.0` changed to `380.0`
- Yaloak South (`YSWF1`) capacity `28.7` changed to `28.0`
- Yarrawonga (`YWNGAHYD`) capacity `9.5` changed to `9.0`
- Greenough River (`GREENOUGH_RIVER_PV1`) capacity `40.0` changed to `10.0`

# Stations not in current

|Name|Code|Facilities|
| :---: | :---: | :---: |
|Eraring|ERGT01|1|
|Goonumbla|GOONUMSF|1|
|White Rock|WRWF1|1|
|White Rock Wind and|WHIROCWIND|2|
|Callide A|CALL_A|2|
|Callide B|CALL_B|2|
|Callide C|CALLIDEC1|2|
|Grosvenor 2|GROSV2|1|
|Swanbank B|SWAN_B|4|
|Swanbank E|SWAN_E|1|
|Wivenhoe (Mini Hydro)|WIVENSH|1|
|Lake Bonney 1|LKBONNY1|1|
|Lake Bonney 3|LKBONNY3|1|
|Snowtown South|SNOWSTH|1|
|Temporary Generation North|SATGN|1|
|Poatina|PTINA220|1|
|Bulgana Green Power Hub - Units|BULGREPOWER|1|
|Eildon (Run of River)|EILDONPD|1|
|Bluewaters|BLUEWATERS|2|
|Kalamunda|KALAMUNDA_SG|1|
|Kwinana cogen|TIWEST_COG1|1|
|Parkeston|PRK_AG|1|
|Red Hill|RED_HILL|1|
|South Cardup|SOUTH_CARDUP|1|
|Tamala Park|TAMALA_PARK|1|
|Wagerup|ALCOA_WGP|3|
|Walkaway|ALINTA_WWF|1|

# New Stations

|Name|Code|Facilities|
| :---: | :---: | :---: |
|Albury|None|1|
|Bakers Maison|None|1|
|Bango|None|1|
|Belrose|None|1|
|Blayney|None|1|
|Chillamurra|None|1|
|Club Merrylands|None|1|
|Collector|None|1|
|Crookwell|None|1|
|Crudine Ridge|None|1|
|Darlington Point|None|1|
|De Bortoli Wines|None|1|
|Draytons Family Wines|None|1|
|Horsley Park|None|1|
|Kiamal|None|1|
|Lake Macquarie Community|None|1|
|Mount Majura|None|1|
|Nymboida|None|1|
|Oaky|None|1|
|Parkes Shire Council STP|None|1|
|Parkes Shire Council WTP|None|1|
|Penrith RSL|None|1|
|Proten|None|2|
|Revesby Workers Club|None|1|
|Singleton|None|1|
|Snowy|SNOWYP|1|
|Snowy 2.0|None|1|
|St George Leagues Club Kogarah|None|1|
|Summer Hill|None|1|
|Sunraysia|None|1|
|Taronga Western Plains Zoo|None|1|
|Todae CSU|None|1|
|Todae Llandilo|None|1|
|Todae Minchinbury|None|1|
|Wetherill Park|None|1|
|Wyong|None|1|
|Aldi Brendale|None|1|
|Birkdale|None|1|
|Callide|CALLIDE|5|
|Callide C|CALLIDEC|2|
|Churchill Abattoir|None|1|
|Cohuna|None|1|
|Dunblane|None|1|
|FPC Green Energy|None|1|
|Fraser Coast Community|None|1|
|Inkerman Mill|None|2|
|Kalamia Mill|None|1|
|Kennedy Energy Park|None|2|
|Lake Somerset|None|1|
|Lakeland|None|1|
|Llewellyn Motors|None|1|
|Macknade Mill|None|1|
|Maryborough Mill|None|2|
|McNamee Partners|None|1|
|Molendinar|None|1|
|Molong|None|1|
|Moranbah Workers|None|1|
|Mount Sheridan Plaza|None|1|
|Mulgrave Central Mill|MULGRAVE|1|
|Normanton|None|1|
|Plane Creek Mill|PLANECRK|2|
|Portland|None|3|
|Proserpine|None|2|
|SIPS Staypylton Industrial|None|1|
|Somerset Dam|SOMERSET|1|
|South Johnstone Mill|None|3|
|St Ursulas College Yeppoon|None|1|
|Suntown|None|2|
|Swanbank B|SWANBANK|5|
|Swanbank JV|None|2|
|Tableland Mill|TBLAND|2|
|Todae DHP|None|1|
|Todae Lourdes|None|1|
|Tong Park Agricultural|None|1|
|University Of Southern Queensland Toowoomba|None|1|
|Vulcan Yatala|None|1|
|Warwick|None|1|
|Winton|None|1|
|Woolcock Centre|None|1|
|Adelaide Airport|None|1|
|Adelaide Zoo|None|1|
|Aquatic & Leasure Centre|None|1|
|BHP Olympic Dam|None|1|
|Kingscote|None|1|
|Nawma Balefill Site Uleybury|None|1|
|Peterborough|None|1|
|Redmud Green Energy|None|7|
|SA VPP|None|1|
|Seacliff|None|1|
|Snapper Point|None|1|
|Vibe Energy|None|1|
|Yalumba Oxford Landing|None|1|
|Yes Sunlands|None|1|
|Glenorchy|None|1|
|Hobart|None|1|
|Lake Margaret|None|1|
|Lower Lake Margaret|None|1|
|St Patricks College Launceston|None|1|
|Tods Corner|None|1|
|Aeroten Leongatha|None|1|
|Ballarat|None|1|
|Bayswood Timber Hallam|None|1|
|Beaconhills College Berwick|None|1|
|Bendigo|None|1|
|Biala|None|1|
|Boronia|None|1|
|Bridgewater|None|1|
|Bunurong Bangholme|None|1|
|Cardinia Creek Minihydro|None|1|
|Carina West H2E|None|1|
|Cedar Meats Geelong|None|1|
|Ferguson North|None|1|
|Flavorite Marketing|None|1|
|Glenrowan West Sun|None|1|
|JL King & Co|None|1|
|Jessica Way Truganina|None|1|
|Melbourne Regional|MELBRL|1|
|Midland Highway Orrvale|None|1|
|Moorabool|None|1|
|Mount Waverley|None|1|
|Newhaven College|None|1|
|Portland|PORTLAND|1|
|Rewaste Wollert|None|1|
|SCS Shepparton|None|1|
|Sale Hospital|None|1|
|Shamic Sheetmetal|None|1|
|Shepparton|None|1|
|Stockyard Hill|None|1|
|Swan Hill Solar Farm|None|1|
|Todae La Trobe University Wodonga|None|1|
|Todae Nillumbik|None|1|
|Todae Toowoomba|None|1|
|UoM Archives Brunswick|None|1|
|UoM McCoy Carlton|None|1|
|UoM Peter Hall Parkville|None|1|
|UoM Sports Centre Parkville|None|1|
|UoM The Spot Carlton|None|1|
|Vawdrey Manufacturing|None|1|
|Wantirna|None|1|
|William Hovell|WILLHOV|1|
|Yatpool|None|1|
|Zilzie Winery|None|1|
|Alcoa Wagerup|ALCOA|1|
|Bluewaters 1|BW1_BLUEWATERS|1|
|Bluewaters 2|BW2_BLUEWATERS|1|
|Goldfields|PRK|1|
|Kalamunda|KALAMUNDA|1|
|Kwinana Eg1|PPP_KCP|1|
|Merredin|MERSOLAR|1|
|Red Hill|RED|1|
|South Cardup|SOUTH|1|
|Tamala Park|TAMALA|1|
|Tiwest|TIWEST|1|
|Wagerup|ALINTA_WGP|2|
|Walkaway|ALINTA|1|
