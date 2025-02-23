import pandas as pd
df= pd.read_excel("data/competition.xlsx",parse_dates=['Report Date'])
print(df['Report Date'].dtype)