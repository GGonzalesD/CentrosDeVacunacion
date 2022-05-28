import pandas as pd
import time

x = time.time()
df = pd.read_csv("data.csv")


df_pos = df[['px', 'py']]
df_inf = df[['inf']]
df_vac = df[['vac']]
df_age = df[['age']]
df_distances = df[[f"d{i+1}" for i in range(30)]]

print(df_distances)
print(time.time()-x)