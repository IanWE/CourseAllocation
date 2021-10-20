import pandas as pd
import numpy as np
import datetime
import time
import random
import logging
import copy
from . import app
from . import utils as U
import re

log = logging.getLogger(__name__)
class Calculator_greedy():
    def __init__(self,instructor,course,sysconfig,number_of_results=300):
        self.instructor = instructor
        self.course = course[course['Act']>0] #ignore course with 0 action
        self.rearrange_course()
        self.sysconfig = sysconfig
        self.config = dict()
        self.teacherMax = self.instructor['MaxSec']
        self.bestcost = []
        self.filtered = False
        self.beststrategies = []
        self.bestteacherlists = []
        self.bestcost = []
        self.number_of_results = number_of_results

        self.config['FirstP'] = sysconfig[sysconfig['config']=='Weight_for_meeting_first_preference'].iloc[0,1]
        self.config['SecondP'] = sysconfig[sysconfig['config']=='Weight_for_meeting_second_preference'].iloc[0,1]
        self.config['ThirdP'] = sysconfig[sysconfig['config']=='Weight_for_meeting_third_preference'].iloc[0,1]
        self.config['FourthP'] = sysconfig[sysconfig['config']=='Weight_for_meeting_fourth_preference'].iloc[0,1]
        self.config['FifthP'] = sysconfig[sysconfig['config']=='Weight_for_meeting_fifth_preference'].iloc[0,1]

        self.config['FirstN'] = sysconfig[sysconfig['config']=='Weight_for_meeting_courses_not_to_teach'].iloc[0,1]
        self.config['SecondN'] = sysconfig[sysconfig['config']=='Weight_for_meeting_courses_not_to_teach'].iloc[0,1]
        self.config['ThirdN'] = sysconfig[sysconfig['config']=='Weight_for_meeting_courses_not_to_teach'].iloc[0,1]
        self.config['N'] = sysconfig[sysconfig['config']=='Weight_for_not_meeting_any_of_the_5_preference'].iloc[0,1]

        self.config["history"] = sysconfig[sysconfig['config']=='Weight_for_courses_taught_in_the_past'].iloc[0,1]
        #self.config['never'] = sysconfig[sysconfig['config']=='Weight_for_courses_never_taught'].iloc[0,1]
        self.config['addition'] = sysconfig[sysconfig['config']=='Weight_for_additional_instructor_to_a_course'].iloc[0,1]
        #self.config['Enhanced'] = sysconfig[sysconfig['config']=='Enhanced_search'].iloc[0,1]

        self.config[1] = sysconfig[sysconfig['config']=='Penalty_for_teaching_classes'].iloc[0,1]
        self.config[2] = sysconfig[sysconfig['config']=='Penalty_for_teaching_second_different_course'].iloc[0,1]
        self.config[3] = sysconfig[sysconfig['config']=='Penalty_for_teaching_third_different_course'].iloc[0,1]
        self.config[4] = sysconfig[sysconfig['config']=='Penalty_for_teaching_more_than_four_different_course'].iloc[0,1]

        self.config["top"] = sysconfig[sysconfig['config']=='Penalty_for_teaching_more_than_MaxSec'].iloc[0,1]
        self.config["bottom"] = sysconfig[sysconfig['config']=='Penalty_for_teaching_less_than_MaxSec'].iloc[0,1]
        self.config["NHP"] = sysconfig[sysconfig['config']=='Penalty_for_both_NP_and_NH'].iloc[0,1]

        self.config['Term'] = str(int(sysconfig[sysconfig['config']=='Year'].iloc[0,1]))+"-"+str(int(sysconfig[sysconfig['config']=='Term'].iloc[0,1]))
        self.config['Year'] = sysconfig[sysconfig['config']=='Year'].iloc[0,1]
        self.config['Intensity'] = sysconfig[sysconfig['config']=="Calculation_intensity"].iloc[0,1]
        self.W = self.weight_init(1)

    def rearrange_course(self):
        count_list = []
        for i in self.course.Code:
            count_list.append((self.instructor.iloc[:,2:7]==i).sum().sum())
        index = np.array(count_list).argsort()
        self.course = self.course.iloc[index,:]
        self.course.index = range(self.course.shape[0])

    def shuffle_courses(self):
        index = np.arange(self.course.shape[0])
        random.shuffle(index)
        self.course = self.course.iloc[index,:]
        self.course.index = range(self.course.shape[0])

    def split_courses(self,a,b,W,div,rem,i,n):
        for j in range(div):#split courses
            #Course:Index
            self.number_of_contained_courses.append(n)
            self.number_of_contained_act.append(n*b['Ins/Sec'][i])
            self.correspond[b['Code'][i]] = self.correspond.get(b['Code'][i],[])#Code:[1,2,3]
            self.correspond[b['Code'][i]].append(len(W))
            W.append([n*b['Ins/Sec'][i]]*a.shape[0])
            self.course_list.append(b['Code'][i])
            self.course_ins.append(n*b['Ins/Sec'][i])
        if rem != 0:
            self.number_of_contained_courses.append(rem)
            self.number_of_contained_act.append(rem*b['Ins/Sec'][i])
            self.correspond[b['Code'][i]] = self.correspond.get(b['Code'][i],[])#Code:[1,2,3]
            self.correspond[b['Code'][i]].append(len(W))
            W.append([rem*b['Ins/Sec'][i]]*a.shape[0])
            self.course_list.append(b['Code'][i])
            self.course_ins.append(rem*b['Ins/Sec'][i])
        return W
        
    #preference weight * # of sections * workload - weight of history + penalty of multiple courses
    def weight_init(self,n=1):
        W = []
        a = self.instructor#instructor csv
        b = self.course#course csv
        sum_sec = b['Act']*b['Ins/Sec']
        self.avg = sum_sec.sum()/sum_sec.shape[0]
        self.number_of_contained_courses = []
        config = self.config# config file
        self.correspond = dict() 
        self.pre_teacher_num = dict()
        self.pre_teacher_dict = dict()#pre-allocated courses, teacher:courses
        self.course_list = []#course list, index of W: course
        self.number_of_contained_act = []
        self.course_ins = []
        index = 0
        self.preset = dict() #course:teachers
        for i in range(b.shape[0]):
            if type(b['PreAllocation'][i]) is not str:
                div = int(b['Act'][i]/n)
                rem = int(b['Act'][i])%n
                W = self.split_courses(a,b,W,div,rem,i,n)
            elif "(" in b['PreAllocation'][i]:
                #load all pre-setted courses
                pre_allocated_course = re.findall("[(](\d+)[)]",b['PreAllocation'][i])
                pn = sum(map(int,pre_allocated_course))
                if pn < b['Act'][i]:
                    #print(b['Code'][i],(b['Act'][i] - pn))
                    s_sec = int(b['Act'][i] - pn)
                    div = int(s_sec/n)
                    rem = s_sec%n
                    W = self.split_courses(a,b,W,div,rem,i,n)
                p = b['PreAllocation'][i]
                ins = b['Ins/Sec'][i]
                l = p.split("/")
                self.preset[b['Code'][i]] = p.replace("/","|")
                for p in l:
                    self.pre_teacher_num[p.split("(")[0]] = self.pre_teacher_num.get(p.split("(")[0],0) 
                    self.pre_teacher_num[p.split("(")[0]] += int(p.split("(")[1].split(")")[0])*ins#Instructor:Number
                    #Get the code without last "F", and store it in pre_teacher_dict
                    if b['Code'][i][-1]=="F":
                        code = b['Code'][i][:-1]
                    else:
                        code = b['Code'][i]
                    self.pre_teacher_dict[p.split("(")[0]] = self.pre_teacher_dict.get(p.split("(")[0],[])
                    self.pre_teacher_dict[p.split("(")[0]].append(code)
        print("Preset:")
        print(self.preset)
        for j in range(1,self.instructor.shape[0]):
            npnh = [0]*len(W)
            preference = a.iloc[j,2:7].values
            #Allocate a course to instructors who do not have any preference
            filled_preference = 0
            for k in preference:
                if type(k) is str and k!='0':
                    filled_preference += 1
            if filled_preference == 0:
                filled_preference = 1
                if type(a.iloc[j,-1]) is str:
                    a.iloc[j,2] = a.iloc[j,-1].split('/')[0]
            #filled_preference = filled_preference/float(5)
            for k in range(2,10):
                code = a.iloc[j,k]
                c = a.columns[k]
                # If the code is not in the available course list
                if code not in b['Code'].values or code not in self.correspond:
                    continue
                # If the course is the preference or the list of not teaching.
                for i in self.correspond[code]:
                    W[i][j] *= config[c] #* filled_preference
                    if k<7:
                        npnh[i] = 1
            #Get the target number of classes the instructor need to teach
            maxsec = a.iloc[j,10]
            if not pd.isna(maxsec):
                self.teacherMax[j] = maxsec
            else:
                self.teacherMax[j] = 4
            #previous-taught classes
            if 'history' in a.columns:
                familiarity = dict()
                history = a.loc[j,'history']#code1/code2/code3...
                if pd.isna(history):
                    continue
                familiarity = config['history']
                for i in range(b.shape[0]):
                    temp_f = 1
                    if b.Code[i] not in self.correspond or b.Act[i]==0:
                        continue
                    #if course is in the keys
                    if b.Code[i] in history:
                        temp_f = min(1,familiarity)
                        for k in self.correspond[b.Code[i]]:
                            W[k][j] *= temp_f
                            npnh[k] += 2
            #if both NP NH
            for k,v in enumerate(npnh):
                if v == 0:
                    W[k][j] += self.config['NHP']
                elif v & 1==0:
                    W[k][j] += self.config['N']
        #print("=====================W=============")
        #print(W)
        #print("=====================W=============")
        return W
        #raise Exception 
                    
    #Greedy algorithm for bound
    def greedy(self,W,t):
        print("=============Start calculation===================")
        base = len(self.W)-len(W)
        s = 0
        trace = []
        teachers = copy.deepcopy(t)
        teacher_dict = copy.deepcopy(self.teacher_dict)
        for i in range(len(W)):
            temp = copy.deepcopy(W[i])
            for j in range(len(teachers)):
                #Add Penalty
                teacher_dict[j] = teacher_dict.get(j,[])
                #A teacher should teach different courses as few as possible
                if len(set(teacher_dict[j])) > 0:
                    if self.course_list[i+base] not in teacher_dict[j]:
                        if len(set(teacher_dict[j]))+1<4:
                            #add penalty of teaching different courses
                            temp[j] += self.config[len(set(teacher_dict[j]))+1]
                        else:#more than 4 classes
                            temp[j] += self.config[4]
                #Teachers should teach target number of classes
                if teachers[j]+self.number_of_contained_act[i+base] > self.teacherMax[j]:
                    temp[j] += self.config["top"]*(self.number_of_contained_act[i+base]+teachers[j]-self.teacherMax[j])
                else:
                    temp[j] += self.config["bottom"]/(self.teacherMax[j]-teachers[j])
            temp = list(temp)
            index = temp.index(min(temp))#get the teacher with the lowest penalty to teach this course
            #course_dict[self.course_list[i+base]].append(index)
            teacher_dict[index].append(self.course_list[i+base])
            teachers[index] += self.course_ins[i+base]
            s += temp[index]
            trace.append(index)
            #print(s)
            #print(teachers[index],self.teacherMax[index])
            #print(self.instructor.name.values[index],temp[index])
        print("===================Result=============================")
        print(trace,s)
        print("=============Stop calculation===================")
        return s,trace

    def calculate(self):
        app.config['CALCULATING'] = True
        #print(self.W)
        self.W = self.weight_init(1)
        self.teachers = [0]*self.instructor.shape[0]
        self.teacher_dict = dict()
        for i in self.pre_teacher_num:
            self.teachers[self.instructor.name.values.tolist().index(i)] = self.pre_teacher_num[i]
            self.teacher_dict[self.instructor.name.values.tolist().index(i)] = copy.deepcopy(self.pre_teacher_dict[i])
        #print(self.instructor.name.values.tolist())
        self.trace = []
        self.cost = 0
        self.beststrategies = []
        self.bestcost = []
        self.filtered = False
        start=time.time()
        self.course_dict = dict()
        self.courselists = []
        #
        tempbeststrategies = []
        tempcourselists = []
        tempbestcost = []
        for _ in range(self.number_of_results):
            self.teachers = [0]*self.instructor.shape[0]
            self.teacher_dict = dict()
            for i in self.pre_teacher_num:
                self.teachers[self.instructor.name.values.tolist().index(i)] = self.pre_teacher_num[i]
                self.teacher_dict[self.instructor.name.values.tolist().index(i)] = copy.deepcopy(self.pre_teacher_dict[i])
            greedycost,self.greedytrace = self.greedy(self.W, self.teachers)
            temp_strategy = []
            temp_course_list = []
            for i in range(len(self.greedytrace)):
                for j in range(int(self.number_of_contained_courses[i])):
                    temp_strategy.append(self.greedytrace[i])
                    temp_course_list.append(self.course_list[i])
            tempbeststrategies.append(temp_strategy)
            tempcourselists.append(temp_course_list)
            tempbestcost.append(greedycost)
            if U.stop==True:
                break
            self.shuffle_courses()
            self.W = self.weight_init(_%4+1)
        #
        indecies = np.array(tempbestcost).argsort()
        index = []
        for i in indecies:
            if tempbestcost[i] not in index:
                index.append(i)
                self.beststrategies.append(tempbeststrategies[i])
                self.courselists.append(tempcourselists[i])
                self.bestcost.append(tempbestcost[i])
            if len(index)==3:
                break
        end=time.time()
        #print(len(self.courselists[0]),self.bestcost)
        log.debug("The procession took "+str(end-start)+" seconds")
    
    def fetch_result3(self):
        d = dict()
        d["Strategy 1"] = []#self.beststrategies[0]
        d["Strategy 2"] = []#self.beststrategies[1]
        d["Strategy 3"] = []#self.beststrategies[2]
        strategy = [dict(),dict(),dict()]
        for k in range(3):
            for j in range(len(self.beststrategies[0])):
                course = self.courselists[k][j]
                index = self.instructor.iloc[self.beststrategies[k][j],0]
                strategy[k][course] = strategy[k].get(course,dict())
                #for i in range(self.number_of_contained_courses[j]):
                strategy[k][course][index] = strategy[k][course].get(index,0) + 1
        for i in range(3):
            for j,cname in zip(self.course['Code'].values,self.course['Course'].values):
                flag = 1
                s = "" 
                if j in strategy[i].keys():
                    for k in strategy[i][j]:
                        if flag!=1:
                            s += "|"
                        flag = 0
                        s += k+"("+str(strategy[i][j][k])+")"
                if j in self.preset:
                    if flag!=1:
                        s += "|"
                    s += self.preset[j] 
                d["Strategy "+str(i+1)].append(s)
        index = self.course.Course+" {"+self.course.Code+"}"
        df = pd.DataFrame(d,index=index).sort_index()
        return self.bestcost,df,index

