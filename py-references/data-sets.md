## Forest Cover Type (FCT) (Frank and Asuncion 2010)

File `./ref/forest-cover-type-dataset/covtype.csv` found on [kaggle.com](https://www.kaggle.com/uciml/forest-cover-type-dataset/version/1)

### About this file
Cartographic variables of 581,012 measurements. The columns include the following dummy variables:

**Wilderness Area** (4 dummy variable binary columns, 0 = absence or 1 = presence): Wilderness area designation. Key is:

1. Rawah Wilderness Area
2. Neota Wilderness Area
3. Comanche Peak Wilderness Area
4. Cache la Poudre Wilderness Area

**Soil Type***
(40 dummy variable binary columns, 0 = absence or 1 = presence): Soil Type designation. Options are:

1. Cathedral family - Rock outcrop complex, extremely stony
2. Vanet - Ratake families complex, very stony
3. Haploborolis - Rock outcrop complex, rubbly
4. Ratake family - Rock outcrop complex, rubbly
5. Vanet family - Rock outcrop complex complex, rubbly
6. Vanet - Wetmore families - Rock outcrop complex, stony
7. Gothic family
8. Supervisor - Limber families complex
9. Troutville family, very stony
10. Bullwark - Catamount families - Rock outcrop complex, rubbly
11. Bullwark - Catamount families - Rock land complex, rubbly. 12 Legault family - Rock land complex, stony
12. Unknown
13. Catamount family - Rock land - Bullwark family complex, rubbly
14. Pachic Argiborolis - Aquolis complex
15. unspecified in the USFS Soil and ELU Survey
16. Cryaquolis - Cryoborolis complex
17. Gateview family - Cryaquolis complex
18. Rogert family, very stony
19. Typic Cryaquolis - Borohemists complex
20. Typic Cryaquepts - Typic Cryaquolls complex
21. Typic Cryaquolls - Leighcan family, till substratum complex
22. Leighcan family, till substratum, extremely bouldery
23. Leighcan family, till substratum - Typic Cryaquolls complex
24. Leighcan family, extremely stony
25. Leighcan family, warm, extremely stony
26. Granile - Catamount families complex, very stony
27. Leighcan family, warm - Rock outcrop complex, extremely stony
28. Leighcan family - Rock outcrop complex, extremely stony
29. Como - Legault families complex, extremely stony
30. Como family - Rock land - Legault family complex, extremely stony
31. Leighcan - Catamount families complex, extremely stony
32. Catamount family - Rock outcrop - Leighcan family complex, extremely stony
33. Leighcan - Catamount families - Rock outcrop complex, extremely stony
34. Cryorthents - Rock land complex, extremely stony
35. Cryumbrepts - Rock outcrop - Cryaquepts complex
36. Bross family - Rock land - Cryumbrepts complex, extremely stony
37. Rock outcrop - Cryumbrepts - Cryorthents complex, extremely stony
38. Leighcan - Moran families - Cryaquolls complex, extremely stony
39. Moran family - Cryorthents - Leighcan family complex, extremely stony
40. Moran family - Cryorthents - Rock land complex, extremely stony

### Columns
- **ElevationElevation** in meters.
- **AspectAspect** in degrees azimuth.
- **SlopeSlope** in degrees.
- **Horizontal_Distance_To_HydrologyHorizontal** distance to nearest surface water features.
- **Vertical_Distance_To_HydrologyVertical** distance to nearest surface water features.
- **Horizontal_Distance_To_RoadwaysHorizontal** distance to nearest roadway.
- **Hillshade_9amHill** shade index at 9am, summer solstice. Value out of 255.
- **Hillshade_NoonHill** shade index at noon, summer solstice. Value out of 255.
- **Hillshade_3pmHill** shade index at 3pm, summer solstice. Value out of 255.
- **Horizontal_Distance_To_Fire_PointsHorizontal** distance to nearest wildfire ignition points.
- **Wilderness_Area1**
- **Wilderness_Area2**
- **Wilderness_Area3**
- **Wilderness_Area4**
- **Soil_Type1**
- **Soil_Type2**
- **Soil_Type3**
- **Soil_Type4**
- **Soil_Type5**
- **Soil_Type6**
- **Soil_Type7**
- **Soil_Type8**
- **Soil_Type9**
- **Soil_Type10**
- **Soil_Type11**
- **Soil_Type12**
- **Soil_Type13**
- **Soil_Type14**
- **Soil_Type15**
- **Soil_Type16**
- **Soil_Type17**
- **Soil_Type18**
- **Soil_Type19**
- **Soil_Type20**
- **Soil_Type21**
- **Soil_Type22**
- **Soil_Type23**
- **Soil_Type24**
- **Soil_Type25**
- **Soil_Type26**
- **Soil_Type27**
- **Soil_Type28**
- **Soil_Type29**
- **Soil_Type30**
- **Soil_Type31**
- **Soil_Type32**
- **Soil_Type33**
- **Soil_Type34**
- **Soil_Type35**
- **Soil_Type36**
- **Soil_Type37**
- **Soil_Type38**
- **Soil_Type39**
- **Soil_Type40**
- **Cover_Type** Forest Cover Type designation. Integer value between 1 and 7, with the following key:
  - Spruce/Fir
  - Lodgepole Pine
  - Ponderosa Pine
  - Cottonwood/Willow
  - Aspen
  - Douglas-fir
  - Krummholz