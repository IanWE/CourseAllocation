import random
import pandas as pd
import numpy as np

#b=pd.read_csv("app/static/uploads/course.csv")
#a=pd.read_csv("app/static/uploads/instructor.csv")
b=pd.read_csv("course.csv")
a=pd.read_csv("instructor.csv")

for i in range(a.shape[0]):
    codes = random.sample(b.Code.values.tolist(),8)
    for j in range(len(codes)):
        if "F"==codes[j][-1]:
            codes[j] = codes[j][:-1]
    a.iloc[i,2:10] = codes

a.to_csv("filled_instructor.csv",index=False)
