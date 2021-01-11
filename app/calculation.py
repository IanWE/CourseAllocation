import pandas as pd
import numpy as np
import datetime
import time
import random
import logging

log = logging.getLogger(__name__)
class Calculator():
    def __init__(self,instructor,course,sysconfig):
        self.instructor = instructor
        self.course = course
        self.sysconfig = sysconfig
        self.W = []
        self.config = dict()

        self.config['FirstP'] = sysconfig[sysconfig['config']=='Weight_for_meeting_first_preference'].iloc[0,1]
        self.config['SecondP'] = sysconfig[sysconfig['config']=='Weight_for_meeting_second_preference'].iloc[0,1]
        self.config['ThirdP'] = sysconfig[sysconfig['config']=='Weight_for_meeting_third_preference'].iloc[0,1]
        self.config['FourthP'] = sysconfig[sysconfig['config']=='Weight_for_meeting_fourth_preference'].iloc[0,1]
        self.config['FifthP'] = sysconfig[sysconfig['config']=='Weight_for_meeting_fifth_preference'].iloc[0,1]

        self.config['FirstN'] = sysconfig[sysconfig['config']=='Weight_for_meeting_courses_not_to_teach'].iloc[0,1]
        self.config['SecondN'] = sysconfig[sysconfig['config']=='Weight_for_meeting_courses_not_to_teach'].iloc[0,1]
        self.config['ThirdN'] = sysconfig[sysconfig['config']=='Weight_for_meeting_courses_not_to_teach'].iloc[0,1]
        self.config['N'] = sysconfig[sysconfig['config']=='Weight_for_not_meeting_any_of_the_5_preference'].iloc[0,1]

        self.config[12] = sysconfig[sysconfig['config']=='Weight_for_courses_taught_in_the_past_0-12_months'].iloc[0,1]
        self.config[24] = sysconfig[sysconfig['config']=='Weight_for_courses_taught_in_the_past_13-24_months'].iloc[0,1]
        self.config['other'] = sysconfig[sysconfig['config']=='Weight_for_other_courses_taught'].iloc[0,1]
        self.config['never'] = sysconfig[sysconfig['config']=='Weight_for_courses_never_taught'].iloc[0,1]

        self.config[1] = sysconfig[sysconfig['config']=='Penalty_for_teaching_courses'].iloc[0,1]
        self.config[2] = sysconfig[sysconfig['config']=='Penalty_for_teaching_more_courses'].iloc[0,1]

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
        self.course_list = []
        index = 0
        self.preset = dict()
        for i in range(b.shape[0]):
            for j in range(int(b['Act'][i])):
                if type(b['PreAllocation'][i]) is not str:
                    correspond[b['Code'][i]] = correspond.get(b['Code'][i],[])#Code:[1,2,3]
                    correspond[b['Code'][i]].append(len(self.W))
                    self.W.append([b['Ins/Sec'][i]]*a.shape[0])
                    self.course_list.append(b['Code'][i])
                elif "(" in b['PreAllocation'][i]:
                    p = b['PreAllocation'][i]
                    l = p.split("/")#load all pre-setted courses
                    #print("XXXXXXXXXXXXXXXXXXXXXX"+b['Code'][i],p)
                    self.preset[b['Code'][i]] = p
                    for p in l:
                        correspond[p.split("(")[0]] = correspond.get(p.split("(")[0],0) + int(p.split("(")[1].split(")")[0])#Course:number
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
            #previous-taught classes
            if a.shape[1]>10:
                familiarity = dict()
                for k in range(10,a.shape[1]):
                    code = a.iloc[j,k]#code1/code2/code3...
                    if pd.isna(code):
                        continue
                    c = a.columns[k]
                    if c == self.config['Term']:
                        continue
                    m = 0
                    if "-" in c:#make sure there is not format error
                        ym = c.split("-")
                        #ym = int(ym[0])*12+int(ym[1])
                        ym = int(float(ym[0]))
                    y = self.config['Year'] - ym
                    if y==0:
                        familiarity[code] = config[12]
                    elif y==1:
                        familiarity[code] = config[24]
                        #familiarity = config[24]
                    elif y>1:
                        familiarity[code] = config['others']
                        #familiarity = config['others']
                for i in range(b.shape[0]):
                    temp_f = config['never']
                    for key in familiarity:#find courses taught in the past
                        if b.Code[i] in key:#if course is in the keys
                            temp_f = min(temp_f,familiarity[key])
                    #print(correspond)
                    if b.Code[i] in self.preset or b.Act[i]==0:
                        continue
                    for k in correspond[b.Code[i]]:
                        self.W[k][j] += temp_f
    
    #Greedy algorithm for bound
    def greedy(self,W,t):
        s = 0
        trace = []
        teachers = t.copy()
        for i in range(len(W)):
            #s += sum(W[i])/len(W[i])
            temp = W[i].copy()
            for j in range(len(teachers)):
                if teachers[j] > 3:
                    temp[j] = temp[j]*(1+self.config[2]*(teachers[j]-3))
                else:
                    temp[j] = temp[j]*(1+self.config[1]*teachers[j])
            index = temp.index(min(temp))
            teachers[index] += 1
            s += temp[index]
            trace.append(index)
        return s,trace
    
    def dfs(self,i=0):
        def check(i,W,teachers):
            rest_W = W[i:]
            bound,_ = self.greedy(rest_W,teachers)
            return bound

        if round(self.cost,5) >= round(self.mincost,5):
            #print(str(i)+" "+str(cost))
            #print("Ignore:"+str(mincost)+"   "+str(trace)+" "+str(best3cost))
            return
        elif i>=len(self.W):
            print("Find a trace with cost:"+str(self.cost)+"   "+str(self.trace))
            if len(self.best3cost)>=3:
                index = self.best3cost.index(max(self.best3cost))
                del self.best3strategies[index]
                del self.best3cost[index]
            self.best3strategies.append(self.trace.copy())
            self.best3cost.append(self.cost)
            self.mincost = max(self.best3cost)
        else:
            #prune
            bound = check(i,self.W,self.teachers)
            if round(self.cost+bound,5) >= round(self.mincost,5):
                #print("Cost Bound:"+str(self.cost)+" "+str(bound)+" min cost:"+str(self.mincost)+" "+str(i)+"/"+str(len(self.W)))
                return
            arg = np.array(self.W[i]).argsort()[::-1]
            for j in arg:
                penalty = 0
                if self.teachers[j] > 3:
                    penalty = self.W[i][j]*self.config[2]*(self.teachers[j]-3)
                else:
                    penalty = self.W[i][j]*self.config[1]*self.teachers[j]
                self.teachers[j] += 1
                #print("Penalty "+str(float(penalty))+" WeightIJ "+str(W[i][j]))
                #print("Cost1 "+str(float(cost)))
                self.cost += self.W[i][j]
                self.cost += penalty
                #print("Cost2 "+str(float(cost)))
                self.trace.append(j)
                self.dfs(i+1)
                #traceback
                self.teachers[j] -= 1
                self.cost -= penalty
                self.cost -= self.W[i][j]
                del self.trace[-1]
                #print("Penalty "+str(float(penalty))+" WeightIJ "+str(W[i][j]))
                #print("Cost3 "+str(int(cost)))
    
    def calculate(self):
        #print(self.W)
        self.teachers = [0]*self.instructor.shape[0]
        for i in self.correspond:
            if i in self.instructor.name.values:
                self.teachers[self.instructor.name.values.tolist().index(i)] = self.correspond[i]
        self.trace = []
        self.cost = 0
        self.best3strategies = []
        self.best3cost = []
        self.mincost = 1000
        start=time.time()
        greedycost,greedytrace = self.greedy(self.W, self.teachers)
        self.mincost = greedycost + 0.2
        self.dfs(0)
        for i in range(len(self.best3cost)):
            log.debug("Strategy "+str(i)+":"+str(self.best3cost[i]))
            #log.debug(self.best3strategies[i])
            #log.debug("Courses:")
            #for j in range(self.course.shape[0]):
            #    log.debug(self.course.iloc[j,0]+":"+self.instructor.iloc[self.best3strategies[i][j],0])
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
                            s += "/"
                        flag = 0
                        s += k+"("+str(strategy[i][j][k])+")"
                elif j in self.preset:
                    if flag!=1:
                        s += "/"
                    s += self.preset[j] 
                d["Strategy "+str(i+1)].append(s)
        index = self.course['Course'].values
        df = pd.DataFrame(d,index=index)
        #print(df[:3])
        return self.best3cost,df

