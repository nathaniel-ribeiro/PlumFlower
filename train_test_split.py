import math
import polars as pl
from sklearn.model_selection import GroupShuffleSplit
import pandas as pd

df = pd.read_csv("data/annotated_games.csv")
print(df.info(memory_usage='deep'))