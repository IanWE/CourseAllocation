import threading
import pandas as pd
from . import appbuilder, db, app
import os

course = []
instructor = []
sysconfig = []
choices = []
if os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"],app.config["COURSE"])):
    course = pd.read_csv(os.path.join(app.config["UPLOAD_FOLDER"],app.config["COURSE"]))
    #choices = course.iloc[:,1].values.tolist()
    #choices = course.iloc[:,1].to_list()
    Code = sorted(list(set(course['Code'])))
    for i in Code:
        choices.append(" and ".join(course[course.Code==i].Course.to_list())+"("+i+")")
    #choices = [(0,"None")]+[(i+1,choices[i]) for i in range(len(choices))]
    choices = [(0,"None")]+[(Code[j],choices[j]) for j in range(len(choices)) if "as faculty" not in choices[j]]

if os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"],app.config["SYSCONFIG"])):
    sysconfig = pd.read_csv(os.path.join(app.config["UPLOAD_FOLDER"],app.config["SYSCONFIG"]))

if os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"],app.config["INSTRUCTOR"])):
    instructor = pd.read_csv(os.path.join(app.config["UPLOAD_FOLDER"],app.config["INSTRUCTOR"]))



lock = threading.Lock()
