# Problem of finding the Centroid and Haversine distance between the farthest pair of points from a given set of geospatial data.

## 🐣 Getting Started

Go through the following steps to begin 
### 1. Generate Synthetical Geospatial data in a format (Color, Longitude, Latitude). 
### 2. View Generated Geospatial Data:
```commandline
color	lat	lng
black	-2.4	-1.2
yellow	1.9	2.0
green	1.7	-2.9
green	2.8	-1.8
white	0.6	5.4
black	0.4	1.3
green	0.3	1.3
yellow	6.7	-5.8
blue	-0.9	0.1
green	-1.5	2.1
brown	0.4	0.7
green	-2.3	2.0
blue	-1.0	4.1
white	3.2	-1.3
blue	3.4	4.2
```
### 3. Instantiate a `Haversine` class object
### 4. Split initial dataset on batches using `df_grouped_split` method 
### Run A Max distance calculation over pairs of points usgin `calc_df_w_max_dist` method. Obtain a DataFrame object being grouped by the color tag and storing calculated max distance and centroid values 
### 5. View Agg DataFRame with Max Distance and Centroid:
```commandline
color	dist	centroid
black	2.042647e+06	(2.956368880342494, 0.5743992588682816)
blue	1.908009e+06	(-2.5673265605687723, -0.25584450532494524)
brown	2.123246e+06	(-1.3278875752548343, 0.5584286712200024)
green	1.705374e+06	(1.2444037844974314, -1.0145344415131412)
red	2.162102e+06	(-0.7022535620006337, -0.050632744150717716)
```
### 6. Show Color Label of element with max distance using `get_color` method
### 7. Show Centroid of element with max distance: `get_centroid` method
```
Color Label of element with max distance:
No Need to Calc an Agg DataFrame. Already pre-calc
yellow
Centroid of element with max distance:
No Need to Calc an Agg DataFrame. Already pre-calc
(-2.029313929423414, 0.8413364902024645)
Code block 'Calc Haversine distance' took: 234321.4952093549 ms
```