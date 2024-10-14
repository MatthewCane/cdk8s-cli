# /// script
# requires-python = "==3.13"
# dependencies = [
#   "requests<3",
#   "polars"
# ]
# ///

import requests
import polars as pl

resp = requests.get("https://peps.python.org/api/peps.json")
data = resp.json()

df = pl.DataFrame([data[row] for row in data])

print(df.filter(df["number"] == 723))
