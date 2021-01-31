import pandas as pd
import numpy as np
import datetime
import time
import random
import logging
import copy

log = logging.getLogger(__name__)
class Calculator():
    def __init__(self,instructor,course,sysconfig):
        self.instructor = instructor
        self.course = course
        self.sysconfig = sysconfig
        self.W = []
        self.config = dict()
        self.teacherMax = dict()

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
        self.config['never'] = sysconfig[sysconfig['config']=='Weight_for_courses_never_taught'].iloc[0,1]
        self.config['addition'] = sysconfig[sysconfig['config']=='Weight_for_additional_instructor_to_a_course'].iloc[0,1]

        self.config[1] = sysconfig[sysconfig['config']=='Penalty_for_teaching_courses'].iloc[0,1]
        self.config[2] = sysconfig[sysconfig['config']=='Penalty_for_teaching_more_than_4_classes'].iloc[0,1]
        self.config[3] = sysconfig[sysconfig['config']=='Penalty_for_teaching_multiple_courses'].iloc[0,1]
        self.config["top"] = sysconfig[sysconfig['config']=='Penalty_for_teaching_more_than_MaxSec'].iloc[0,1]
        self.config["bottom"] = sysconfig[sysconfig['config']=='Penalty_for_teaching_less_than_MaxSec'].iloc[0,1]

        self.config['Term'] = str(int(sysconfig[sysconfig['config']=='Year'].iloc[0,1]))+"-"+str(int(sysconfig[sysconfig['config']=='Term'].iloc[0,1]))
        self.config['Year'] = sysconfig[sysconfig['config']=='Year'].iloc[0,1]
        self.weight_init()

    #preference weight * # of sections * workload - weight of history + penalty of multiple courses
    def weight_init(self):
        a = self.instructor
        b = self.course
        config = self.config
        #base = b['Ins/Sec']*b['Act']*self.config['N']
        #base = base.values
        correspond = {}
        self.pre_teacher_dict = dict()
        self.course_list = []
        index = 0
        self.preset = dict()
        for i in range(b.shape[0]):
            for j in range(int(b['Act'][i])):#split courses
                if type(b['PreAllocation'][i]) is not str:
                    correspond[b['Code'][i]] = correspond.get(b['Code'][i],[])#Code:[1,2,3]
                    correspond[b['Code'][i]].append(len(self.W))
                    self.W.append([b['Ins/Sec'][i]]*a.shape[0])
                    self.course_list.append(b['Code'][i])
                elif "(" in b['PreAllocation'][i]:
                    p = b['PreAllocation'][i]
                    l = p.split("/")#load all pre-setted courses
                    #print("XXXXXXXXXXXXXXXXXXXXXX"+b['Code'][i],p)
                    self.preset[b['Code'][i]] = p.replace("/","|")
                    for p in l:
                        correspond[p.split("(")[0]] = correspond.get(p.split("(")[0],0) + int(p.split("(")[1].split(")")[0])#Course:number
                        if b['Code'][i][-1]=="F":
                            code = b['Code'][i][:-1]
                        else:
                            code = b['Code'][i]
                        self.pre_teacher_dict[p.split("(")[0]] = self.pre_teacher_dict.get(p.split("(")[0],[])
                        self.pre_teacher_dict[p.split("(")[0]].append(code)
                    #correspond[b['Code'][i]] = #Course:number
        self.correspond = correspond
        for j in range(self.instructor.shape[0]):
            for k in range(2,10):
                code = a.iloc[j,k]
                c = a.columns[k]
                #If code is null
                if code not in b['Code'].values:
                    continue
                for i in correspond[code]:
                    #print("!!!"+str(self.W[i][j])+" "+str(config[c]))
                    self.W[i][j] *= config[c]
                    #print("!!!"+str(self.W[i][j]))
            maxsec = a.iloc[j,10]
            if not pd.isna(maxsec):
                self.teacherMax[j] = maxsec
                print("Teacher:",self.instructor.name[j])
            else:
                self.teacherMax[j] = 10000
            #previous-taught classes
            if a.shape[1]>11:
                familiarity = dict()
                #for k in range(10,a.shape[1]):
                #code = a.iloc[j,k]#code1/code2/code3...
                code = a.loc[j,'history']#code1/code2/code3...
                if pd.isna(code):
                    continue
                familiarity = config['history']
                for i in range(b.shape[0]):
                    temp_f = config['never']
                    if not pd.isna(code) and b.Code[i] in code:#if course is in the keys
                        temp_f = min(temp_f,familiarity)
                    #print(correspond)
                    if b.Code[i] in self.preset or b.Act[i]==0:
                        continue
                    for k in correspond[b.Code[i]]:
                        self.W[k][j] += temp_f

    #Greedy algorithm for bound
    def greedy(self,W,t):
        base = len(self.W)-len(W)
        s = 0
        trace = []
        teachers = copy.deepcopy(t)
        course_dict = copy.deepcopy(self.course_dict)
        teacher_dict = copy.deepcopy(self.teacher_dict)
        for i in range(len(W)):
            temp = copy.deepcopy(W[i])#.copy()
            for j in range(len(teachers)):
                if teachers[j] >= 4:
                    temp[j] = temp[j]*(1+self.config[2]*(teachers[j]-3))
                else:
                    temp[j] = temp[j]*(1+self.config[1]*teachers[j])
                teacher_dict[j] = teacher_dict.get(j,[])
                #A teacher should teach course as less as possible
                if len(set(teacher_dict[j])) > 0:
                    if self.course_list[i+base] in teacher_dict[j]:
                        temp[j] += self.config[3]*(len(set(teacher_dict[j]))-1)**3
                    else:
                        temp[j] += self.config[3]*len(set(teacher_dict[j]))**3
                #Teache target number of courses
                if teachers[j] >= self.teacherMax[j]:
                    temp[j] += self.config["top"]
                elif self.teacherMax[j]!=10000:
                    temp[j] += self.config["bottom"]/(self.teacherMax[j]-teachers[j])
                else:
                    temp[j] += self.config["bottom"]
                #Let a course be only assigned to one teacher
                course_dict[self.course_list[i+base]] = course_dict.get(self.course_list[i+base],[])
                cs = course_dict[self.course_list[i+base]]
                l = len(set(cs))
                if j not in cs:
                    l = l*self.config['addition']
                    temp[j] += l
            index = temp.index(min(temp))
            course_dict[self.course_list[i+base]].append(index)
            teacher_dict[index].append(self.course_list[i+base])
            teachers[index] += 1
            s += temp[index]
            trace.append(index)
            #print("Min:"+str(s)+"|"+str(temp[index])+"|"+str(index))
            #print("Course:",self.course_list[i])
            #print(temp)
            #print(W[i])
        return s,trace
    
    def dfs(self,i=0):
        def check(i,W,teachers):
            rest_W = W[i:]
            bound,_ = self.greedy(rest_W,teachers)
            return bound
        if round(self.cost,5) >= round(self.mincost,5):
            #print(str(i)+" "+str(cost))
            #print("Ignore:"+str(self.mincost)+"   "+str(self.trace)+" "+str(self.best3cost))
            return
        elif i >= len(self.W):
            print("Find a trace with cost:"+str(self.cost)+"   "+str(self.trace))
            #mincost = self.mincost if len(self.best3cost)==0 else max(self.best3cost)
            if round(self.cost,5) not in self.best3cost:
                self.best3strategies.append(self.trace.copy())
                self.best3cost.append(round(self.cost,5))
                #if len(self.best3cost) > 3:
                #    index = self.best3cost.index(max(self.best3cost))
                #    del self.best3strategies[index]
                #    del self.best3cost[index]
            #if len(self.best3cost)>=3:
            if  len(self.best3cost)<1000:
                self.mincost = min(self.best3cost)
            else:
                self.mincost = sorted(self.best3cost)[int(len(self.best3cost)/4)]
        else:
            #prune
            bound = check(i,self.W,self.teachers)
            if round(self.cost+bound,5) >= round(self.mincost,5):
                #if round(self.cost+bound,5) >= round((self.greedycost+self.mincost)/2+0.0001,5):
                #print("Greedy Result:"+str(self.greedytrace))
                #print("Result:"+str(self.trace))
                #print("Cost Bound:"+str(self.cost)+" "+str(bound)+" min cost:"+str(self.mincost)+" "+str(i)+"/"+str(len(self.W)))
                #print(self.teachers,self.teacher_dict)
                return
            arg = np.array(self.W[i]).argsort()[::-1]
            #arg = range(len(self.W[0]))
            for j in arg:
                penalty = 0
                if self.teachers[j] >= 4:
                    penalty = self.W[i][j]*(1+self.config[2]*(self.teachers[j]-3))
                else:
                    penalty = self.W[i][j]*(1+self.config[1]*self.teachers[j])
                self.teacher_dict[j] = self.teacher_dict.get(j,[])
                if len(set(self.teacher_dict[j])) > 0:#A teacher should teach course as less as possible
                    #A teacher should teach less different courses
                    if self.course_list[i] in self.teacher_dict[j]:
                        penalty += self.config[3]*(len(set(self.teacher_dict[j]))-1)**3
                    else:
                        penalty += self.config[3]*len(set(self.teacher_dict[j]))**3
                #Let a course be only assigned to one teacher
                self.course_dict[self.course_list[i]] = self.course_dict.get(self.course_list[i],[])
                cs = self.course_dict[self.course_list[i]]
                self.teacher_dict[j].append(self.course_list[i])
                appended = False
                l = len(set(cs))
                #if j is not in course_dict, add it in and set a mark
                if j not in cs:
                    l = l * self.config['addition']
                    self.course_dict[self.course_list[i]].append(j)
                    appended = True
                    penalty += l
                if self.teachers[j] >= int(self.teacherMax[j]):
                    penalty += self.config["top"]
                elif self.teacherMax[j] != 10000:
                    penalty += self.config["bottom"]/(self.teacherMax[j]-self.teachers[j])
                else:
                    penalty += self.config["bottom"]
                self.teachers[j] += 1
                #print(str(i)+" Cost1 "+str(float(self.cost)))
                #self.cost += self.W[i][j]
                self.cost += penalty
                #print(str(i)+" Cost2 "+str(float(self.cost)))
                self.trace.append(j)
                self.dfs(i+1)
                #traceback
                self.teachers[j] -= 1
                self.cost -= penalty
                #self.cost -= self.W[i][j]
                del self.trace[-1]
                del self.teacher_dict[j][-1]
                if appended==True:
                    del self.course_dict[self.course_list[i]][-1]
                    #print(self.course_list[i],self.course_dict[self.course_list[i]])
                #print("-:",self.course_dict)
                #print("Penalty "+str(float(penalty))+" MinCost "+str(self.mincost))
                #print(str(i)+" Cost3 "+str(float(self.cost)))
    def calculate(self):
        #print(self.W)
        self.teachers = [0]*self.instructor.shape[0]
        self.teacher_dict = dict()
        for i in self.correspond:
            if i in self.instructor.name.values:
                self.teachers[self.instructor.name.values.tolist().index(i)] = self.correspond[i]
                self.teacher_dict[self.instructor.name.values.tolist().index(i)] = copy.deepcopy(self.pre_teacher_dict[i])
        self.trace = []
        self.cost = 0
        self.best3strategies = []
        self.best3cost = []
        start=time.time()
        self.course_dict = dict()
        greedycost,self.greedytrace = self.greedy(self.W, self.teachers)
        #print("XXXXXXXXXXXXXXXXXXXXX "+str(greedycost)+" "+str(self.greedytrace))
        #self.teachers[16] += 1
        #self.course_dict[self.course_list[0]]=[16]
        #cost1,trace1 = self.greedy(self.W[1:],self.teachers)
        #print("XXXXXXXXXXXXXXXXXXXXX "+str(cost1)+" "+str(trace1))
        self.mincost = greedycost + 0.00001
        self.dfs(0)
        for i in range(len(self.best3cost)):
            log.debug("Strategy "+str(i)+":"+str(self.best3cost[i]))
            log.debug(self.best3strategies[i])
            log.debug("Courses:")
            for j in range(self.course.shape[0]):
                log.debug(self.course.iloc[j,0]+":"+self.instructor.iloc[self.best3strategies[i][j],0])
        end=time.time()
        log.debug("The procession took "+str(end-start)+" seconds")
    
    def fetch_result(self):
        return self.best3cost,self.best3strategies

    def fetch_result2(self):
        d = dict()
        d["Strategy 1"] = []
        d["Strategy 2"] = []
        d["Strategy 3"] = []
        strategy = [dict(),dict(),dict()]
        costs = np.array(self.best3cost)
        ma = max(self.best3cost)
        mi = min(self.best3cost)
        mid = (ma+mi)/2
        ma = mid
        mid = (ma+mi)/2
        first = self.best3strategies[self.best3cost.index(mi)]
        print(mid,np.where(costs>=mid)[0])
        second = self.best3strategies[np.where(costs>mid)[0][0]]
        third = self.best3strategies[np.where(costs>mid)[0][0]]
        self.best3strategies = [first,second,third]
        self.best3cost = [mi,mid,ma]
        print(self.best3strategies)
        for j in range(len(self.W)):
            for k in range(3):
                course = self.course_list[j]
                index = self.instructor.iloc[self.best3strategies[k][j],0]
                strategy[k][course] = strategy[k].get(course,dict())
                strategy[k][course][index] = strategy[k][course].get(index,0) + 1
        for i in range(3):
            for j,cname in zip(self.course['Code'].values,self.course['Course'].values):
                flag = 1
                s = "" 
                #print(strategy[i])
                if j in strategy[i].keys():
                    for k in strategy[i][j]:
                        if flag!=1:
                            s += "|"
                        flag = 0
                        s += k+"("+str(strategy[i][j][k])+")"
                elif j in self.preset:
                    if flag!=1:
                        s += "|"
                    s += self.preset[j] 
                d["Strategy "+str(i+1)].append(s)
        index = self.course.Course+" {"+self.course.Code+"}"
        df = pd.DataFrame(d,index=index)
        return self.best3cost,df,index

