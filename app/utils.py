import threading
import pandas as pd
from . import appbuilder, db, app
import os

switch = "s1"
stop = False
keep = True
course = []
instructor = []
sysconfig = []
choices = []
if os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"],app.config["COURSE"])):
    course = pd.read_csv(os.path.join(app.config["UPLOAD_FOLDER"],app.config["COURSE"]))
    #choices = course.iloc[:,1].values.tolist()
    #choices = course.iloc[:,1].to_list()
    Code = sorted(list(set(course['Code'])))
    #exlude those prelocated courses.
    for i in Code:
        if len(course[course.Code==i].Course.to_list())>1:
            choices.append(" and ".join(course[course.Code==i].Course.to_list())+"("+i+")")
            continue
        pl = course[course.Code==i]['PreAllocation'].values[0]
        act = course[course.Code==i]["Act"].values[0]
        if act==0:
            continue
        print(pl, type(pl) is str)
        if type(pl) is str:
            pl = pl.split("/")
            number_of_courses = 0
            for c in pl:
                print("Calculate ",c)
                number_of_courses += int(c.split("(")[-1].split(")")[0])
            print(i)
            print("Number of courses:",number_of_courses)
            print("Act:",act)
            if number_of_courses >= act:
                continue
        choices.append(" and ".join(course[course.Code==i].Course.to_list())+"("+i+")")
    choices = [(0,"None")]+[(Code[j],choices[j]) for j in range(len(choices))]
    #choices = [(0,"None")]+[(Code[j],choices[j]) for j in range(len(choices)) if "as faculty" not in choices[j]]

if os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"],app.config["SYSCONFIG"])):
    sysconfig = pd.read_csv(os.path.join(app.config["UPLOAD_FOLDER"],app.config["SYSCONFIG"]))

if os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"],app.config["INSTRUCTOR"])):
    instructor = pd.read_csv(os.path.join(app.config["UPLOAD_FOLDER"],app.config["INSTRUCTOR"]))
    print(instructor)



lock = threading.Lock()
