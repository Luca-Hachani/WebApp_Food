import pandas as pd


PATH_USERS = "data/PP_users.csv"
df_users = pd.read_csv(PATH_USERS, sep=',')
# print(df_users.info())

PATH_RECIPES = "data/PP_recipes.csv"
df_recipes = pd.read_csv(PATH_RECIPES, sep=',')
print(df_recipes.info())
# print(df_recipes.head())

PATH_RECIPES_RAW = "data/RAW_recipes.csv"
df_recipes_raw = pd.read_csv(PATH_RECIPES_RAW, sep=',')
print(df_recipes_raw.info())
# print(df_recipes_raw.head())

print(df_recipes["ingredient_ids"][df_recipes["id"] == 424415])
print(df_recipes_raw["ingredients"][df_recipes_raw["id"] == 424415])
