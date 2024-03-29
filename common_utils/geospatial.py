from collections import Counter
from typing import List, Tuple
import time
import timeit
import pandas as pd
import pyarrow as pa
import numpy as np
import scipy.stats as ss
from scipy.spatial import ConvexHull
import hashlib 
import uuid
import math
from multiprocessing import Pool, Process, JoinableQueue
from multiprocessing.pool import ThreadPool
from functools import partial


def combinations(l: list, k: int) -> List[Tuple[float, float]]:
    if k <= 0:
        comb = [None]
    else:
        comb = []
        for i, item in enumerate(l, 1):
            rem_items = l[i:]
            rem_comb = combinations(rem_items, k-1)
            comb.extend(item if c 
                        is None else (item, c) for c in rem_comb)

    return comb

class Haversine(object):
  
    def __init__(self, df: pd.core.frame.DataFrame):
        '''
        Accepts a df object in the following format:
        ================
        color  lat   lng
        black  -2.4  -1.2
        yellow 1.9   2.0
        ================
        '''
        
        self.df = df
        self.R = 1. #6371e3 # m

    def geo_to_xyz(self, lat, lon) -> Tuple[float, float, float]:
        """
        Convert geodesical points to Euclidean coord space
        """

        #Convert lat/lon (must be in radians) to Cartesian coordinates for each location.
        lat, lon = list(map(math.radians, (lat, lon)))
        
        X = self.R * math.cos(lat) * math.cos(lon)
        Y = self.R * math.cos(lat) * math.sin(lon)
        Z = self.R * math.sin(lat)
        
        return (X, Y, Z)        
        
    def calc_centroid(self, *args) -> Tuple[float, float]:
        """
        Calculate centroid of the vector between two geodesical points
        """

        lat1, lat2, lon1, lon2 = args
        #Convert lat/lon (must be in radians) to Cartesian coordinates for each location.
        X1 = self.R * math.cos(lat1) * math.cos(lon1)
        Y1 = self.R * math.cos(lat1) * math.sin(lon1)
        Z1 = self.R * math.sin(lat1)

        X2 = self.R * math.cos(lat2) * math.cos(lon2)
        Y2 = self.R * math.cos(lat2) * math.sin(lon2)
        Z2 = self.R * math.sin(lat2)
        
        #Compute average x, y and z coordinates.
        x = (X1 + X2) / 2
        y = (Y1 + Y2) / 2
        z = (Z1 + Z2) / 2

        #Convert average x, y, z coordinate to latitude and longitude.
        Lon = math.atan2(y, x)
        Hyp = np.sqrt(x * x + y * y)
        Lat = math.atan2(z, Hyp)
        
        return (Lon, Lat)
    

    def __distance(self, coords: List[Tuple[Tuple[float, float],
                                            Tuple[float, float]]]) -> float:
        """
        Calc distance between two pairs of geodesical points using Haversine formula.
        Shouldn't be called directly. 
        Method is called by `get_distance` method.
        """
        
        max_dist = 0
        for i, ele in enumerate(coords):

            lat1, lon1 = list(map(math.radians, ele[0]))
            lat2, lon2 = list(map(math.radians, ele[1]))
            #const R = 6371e3; // metres
            dlat = lat2-lat1
            dlon = lon2-lon1
            a = math.sin(dlat/2)**2 + \
                math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            d = self.R * c
            if d > max_dist: 
                max_dist = d
                coords = [lat1, lat2, lon1, lon2]
                centroid = self.calc_centroid(*coords)

        return max_dist, centroid

    def get_distance(self, x: pd.core.frame.DataFrame) -> float:
        """
        Calc distance and centroid between two pairs of geodesical points using Haversine formula.
        """
        lat_ = x.lat.tolist()
        lng_ = x.lng.tolist()
        lat_pairs = combinations(l=lat_, k=2)
        lng_pairs = combinations(l=lng_, k=2)
        lat_lng_pairs = [((i[0],j[0]),(i[1],j[1]))for i,j in list(zip(lat_pairs, lng_pairs))]
        d, cetr = self.__distance(coords = lat_lng_pairs)

        return (d, cetr)

    def df_grouped_split(self, num_part=6):
        """
        Split DataFrame obj onto batches
        """
        keyslst = list(self.df.index.values)
        batches = np.array_split(keyslst, num_part) 

        collection = [self.df.loc[batch] for batch in batches]

        return collection        

    def parallelize_df_grouped(self,
                               func=None,
                               num_part=20, 
                               num_workers=20):
        
        """
        Function for parallelizing mapped operations using pandas multiprocessing
        """
        
        df_split = self.df_grouped_split(num_part=num_part)
        pool = ThreadPool(num_workers)
        pred_dicts_list = pool.map(func, df_split)
        pool.close()
        pool.join() 
        
        return pred_dicts_list    
    
    def __df_w_max_dist(self, df):
        """
        Given batch Dataframe obj generated a new DataFrame object with dist and centroid 
        """
        res = df.groupby(by=["color"])[['lat', 'lng']].apply(lambda x: self.get_distance(x)).reset_index()
        dd = pd.concat([res, res.pop(0).apply(pd.Series).add_prefix("dist_")], axis=1)
        dd.rename(columns={"dist_0": "dist", 
                           "dist_1": "centroid"}, inplace=True)
        
        return dd
    
    def calc_df_w_max_dist(self) -> pd.core.frame.DataFrame:
        """
        Generate DataFrame object after grouping by color attribute and 
        calculating a max distance within ech group respectively
        """
        
        res = self.parallelize_df_grouped(self.__df_w_max_dist)
        df_ = pd.concat(res)
        self.df_w_max_dist = df_

    def get_df_w_max_dist(self):
        if hasattr(self, 'df_w_max_dist'):
            print("No Need to Calc an Agg DataFrame. Already pre-calc")
            return self.df_w_max_dist
        else:
            print("Cannot find an Agg DataFrame with Max Distance. Start Calc...")
            self.calc_df_w_max_dist()
            return self.df_w_max_dist
    
    def get_color(self) -> str:
        dd = self.get_df_w_max_dist()
        
        return dd.loc[dd.dist==dd.dist.max(), "color"].tolist()[0]

    def get_centroid(self) -> Tuple[float, float]:
        dd = self.get_df_w_max_dist()
        
        return dd.loc[dd.dist==dd.dist.max(), "centroid"].tolist()[0]