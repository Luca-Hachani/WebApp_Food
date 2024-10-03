import numpy as np
import pandas as pd


path_users = "data/PP_users.csv"
df_users = pd.read_csv(path_users, sep=',')
# print(df_users.info())

path_recipes = "data/PP_recipes.csv"
df_recipes = pd.read_csv(path_recipes, sep=',')
print(df_recipes.info())
# print(df_recipes.head())

path_recipes_raw = "data/RAW_recipes.csv"
df_recipes_raw = pd.read_csv(path_recipes_raw, sep=',')
print(df_recipes_raw.info())
# print(df_recipes_raw.head())

print(df_recipes["ingredient_ids"][df_recipes["id"]==424415])
print(df_recipes_raw["ingredients"][df_recipes_raw["id"]==424415])

