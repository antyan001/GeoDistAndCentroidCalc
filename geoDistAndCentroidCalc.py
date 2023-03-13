#!python

from collections import Counter
from typing import List, Tuple
import time
import timeit
import scipy.stats as ss
import pandas as pd
import numpy as np
import math

from common_utils import Haversine

class CodeTimer:
    def __init__(self, name=None):
        self.name = " '" + name + "'" if name else ""

    def __enter__(self):
        self.start = timeit.default_timer()

    def __exit__(self, exc_type, exc_value, traceback):
        self.took = (timeit.default_timer() - self.start) * 1000.0
        print("Code block" + self.name + " took: " + str(self.took) + " ms")
        
   
get_color = {0: "red", 
             1: "blue", 
             2: "yellow", 
             3: "black", 
             4: "green", 
             5: "brown", 
             6: "white"
            }

SIZE = 100_000 # 100_000_000

print("Generate a Synthetic Geospatial data")

## generate a random normal distribution of latitude values: constructing a CDF for latitude coord in Degrees
VAR = 3
x_lat = np.arange(-90., 90., 0.1)
xU, xL = x_lat + 0.5, x_lat - 0.5 
prob = ss.norm.cdf(xU, scale = VAR) - ss.norm.cdf(xL, scale = VAR)
prob_lat = prob / prob.sum() # normalize the probabilities so their sum is 1
# nums = np.random.choice(x, size = SIZE, p = prob)

## generate a random normal distribution of longitude values: constructing a CDF for longitude coord in Degrees
x_lng = np.arange(-180., 180., 0.1)
xU, xL = x_lng + 0.5, x_lng - 0.5 
prob = ss.norm.cdf(xU, scale = VAR) - ss.norm.cdf(xL, scale = VAR)
prob_lng = prob / prob.sum() # normalize the probabilities so their sum is 1
# nums = np.random.choice(x, size = SIZE, p = prob)

## generate floats of `lat` with proba from normal distribution
## generate floats of `lng` with proba from normal distribution
## generate colors with proba from random distribution

df = pd.DataFrame({'color': [get_color.get(np.random.randint(0,7),0) for i in range(SIZE)],
                   'lat'  : np.random.choice(x_lat, size = SIZE, p = prob_lat),
                   'lng'  : np.random.choice(x_lng, size = SIZE, p = prob_lng)
                  })

print("View Synthetic Geospatial data")

print(df.head())

df.info(memory_usage='deep')

with CodeTimer("Calc Haversine distance"):
    print("Instantiate a Haversine class object:")
    hh = Haversine(df)
    _ = hh.get_df_w_max_dist()
    print("View Agg DataFRame with Max Distance and Centroid:")
    print(hh.df_w_max_dist.head())
    print("Color Label of element with max distance:")
    print(hh.get_color())    
    print("Centroid of element with max distance:")
    print(hh.get_centroid())






