# ydata_profiling
# pip install ydata-profiling

import os 
from pathlib import Path 
import pandas as pd 
from ydata_profiling import ProfileReport

os.chdir(Path(__file__).parent)



# 1. Read the CSV File
df = pd.read_csv("./my_data.csv")


# 2. Create a Profile
profile = ProfileReport(df)


# 3. Export the report to HTML
profile.to_file(output_file="./profile1.html")