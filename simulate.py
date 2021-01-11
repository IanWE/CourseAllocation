import pandas as pd
import numpy as np
import datetime
import time
import random

a=pd.read_csv("real_data/instructor.csv")
b=pd.read_csv("real_data/course.csv")
sysconfig = pd.read_csv("real_data/sysconfig.csv")
random.seed(2)
#a.iloc[i,4:] = np.array(random.sample(b.Code.values.tolist(),8))
#a.iloc[0,2:4] = np.array(random.sample(a.iloc[0,5:].values.tolist(),2))
base = b['Ins/Sec']*b['Act']
b = b[base!=0] #filter out course with 0 class
#for i in range(5):
for i in range(a.shape[0]):
    a.iloc[i,2:10] = np.array(random.sample(b.Code.values.tolist(),8))
    y = str(datetime.datetime.now().year)
    date = int(time.time()/(60*60*24))

t = str(datetime.datetime.now().year-2)+"-"+str(datetime.datetime.now().month)
for i in range(a.shape[0]):
    a.loc[i,t] = random.sample(a.iloc[i,2:7].tolist(),1)[0]

#t = str(datetime.datetime.now().year-1)+"-"+str(datetime.datetime.now().month-1)
#for i in range(a.shape[0]):
#    a.loc[i,t] = random.sample(a.iloc[i,2:7].tolist(),1)[0]
#
#t = str(datetime.datetime.now().year)+"-"+str(datetime.datetime.now().month+1)
#for i in range(a.shape[0]):
#    a.loc[i,t] = random.sample(a.iloc[i,2:10].tolist(),1)[0]

config = dict()
config['FirstP'] = sysconfig[sysconfig['config']=='Weight_for_meeting_first_preference'].iloc[0,1]
config['SecondP'] = sysconfig[sysconfig['config']=='Weight_for_meeting_second_preference'].iloc[0,1]
config['ThirdP'] = sysconfig[sysconfig['config']=='Weight_for_meeting_third_preference'].iloc[0,1]
config['FourthP'] = sysconfig[sysconfig['config']=='Weight_for_meeting_fourth_preference'].iloc[0,1]
config['FifthP'] = sysconfig[sysconfig['config']=='Weight_for_meeting_fifth_preference'].iloc[0,1]

config['FirstN'] = sysconfig[sysconfig['config']=='Weight_for_meeting_courses_not_to_teach'].iloc[0,1]
config['SecondN'] = sysconfig[sysconfig['config']=='Weight_for_meeting_courses_not_to_teach'].iloc[0,1]
config['ThirdN'] = sysconfig[sysconfig['config']=='Weight_for_meeting_courses_not_to_teach'].iloc[0,1]
config['N'] = sysconfig[sysconfig['config']=='Weight_for_not_meeting_any_of_the_5_preference'].iloc[0,1]

config[12] = sysconfig[sysconfig['config']=='Weight_for_courses_taught_in_the_past_0-12_months'].iloc[0,1]
config[24] = sysconfig[sysconfig['config']=='Weight_for_courses_taught_in_the_past_13-24_months'].iloc[0,1]
config['other'] = sysconfig[sysconfig['config']=='Weight_for_other_courses_taught'].iloc[0,1]
config['never'] = sysconfig[sysconfig['config']=='Weight_for_courses_never_taught'].iloc[0,1]

config[1] = sysconfig[sysconfig['config']=='Penalty_for_teaching_the_second_course'].iloc[0,1]
config[2] = sysconfig[sysconfig['config']=='Penalty_for_teaching_the_third_course'].iloc[0,1]

#b = b.sort_values('Act')
#b = b.sort_values('Act')
#calculate the weight matrix
## initialize W
base = b['Ins/Sec']*b['Act']*config['N']
base = base.values
W = []
for i in range(b.shape[0]):
    W.append([base[i]]*a.shape[0])

#preference weight * # of sections * workload - weight of history + penalty of multiple courses
for j in range(a.shape[0]):
    for k in range(2,10):
        code = a.iloc[j,k]
        c = a.columns[k]
        for i in b[b.Code==code].index:
            W[i][j] *= config[c]
    #previous-taught classes
    if a.shape[1]>10:
        familiarity = dict()
        for k in range(10,a.shape[1]):
            code = a.iloc[i,k]
            if pd.isna(code):
                continue
            c = a.columns[k]
            current_month = datetime.datetime.now().year*12+datetime.datetime.now().month
            m = 0
            if "-" in c:#make sure there is not format error
                ym = c.split("-")
                ym = int(ym[0])*12+int(ym[1])
            else:
                ym = m
            m = current_month - ym
            if m<=12 and m>0:
                familiarity[code] = config[12]
            elif m>12 and m<=24:
                familiarity[code] = config[24]
                #familiarity = config[24]
            elif m>24:
                familiarity[code] = config['others']
                #familiarity = config['others']
        for i in range(b.shape[0]):
            temp_f = config['never']
            for key in familiarity:#find courses taught in the past
                if b.Code[i] in key:
                    temp_f = min(temp_f,familiarity[key]) 
            W[i][j] += temp_f
                
# Greedy
def check(i,teachers):
    rest_W = W[i:]
    bound,_ = greedy(rest_W,teachers)
    return bound

# Algorithm
def dfs(i):
    global mincost
    global best3strategies
    global best3cost
    #global penalty
    global trace
    global cost
    global teachers
    if cost >= mincost:
        #print(str(i)+" "+str(cost))
        #print("Ignore:"+str(mincost)+"   "+str(trace)+" "+str(best3cost))
        return
    elif i>=len(W):
        print("Find a trace with cost:"+str(cost)+"   "+str(trace))
        if len(best3cost)>=3:
            index = best3cost.index(max(best3cost))
            del best3strategies[index]
            del best3cost[index]
        best3strategies.append(trace.copy())
        best3cost.append(cost)
        mincost = max(best3cost)
    else:
        #prune
        bound = check(i,teachers) 
        if cost+bound >= mincost:
            #print("Cost Bound:"+str(cost)+" "+str(bound))
            return
        arg = np.array(W[i]).argsort()[::-1]
        for j in arg:
            penalty = 0
            if teachers[j] >= 2:
                penalty = W[i][j]*config[2]*teachers[j]
            elif teachers[j] >= 1:
                penalty = W[i][j]*config[1]
            teachers[j] += 1
            #print("Penalty "+str(float(penalty))+" WeightIJ "+str(W[i][j]))
            #print("Cost1 "+str(float(cost)))
            cost += W[i][j]
            cost += penalty
            #print("Cost2 "+str(float(cost)))
            trace.append(j)
            dfs(i+1)
            #traceback
            teachers[j] -= 1
            cost -= penalty
            cost -= W[i][j]
            del trace[-1] 
            #print("Penalty "+str(float(penalty))+" WeightIJ "+str(W[i][j]))
            #print("Cost3 "+str(int(cost)))

print(W)

def greedy(W,t=[0]*a.shape[0]):
    s = 0
    trace = []
    teachers = t.copy()
    for i in range(len(W)):
        #s += sum(W[i])/len(W[i])
        temp = W[i].copy()
        for j in range(len(teachers)):
            if teachers[j] >= 2:
                temp[j] = temp[j]*(1+config[2]*teachers[j])
            elif teachers[j] >= 1:
                temp[j] = temp[j]*(1+config[1])
        index = temp.index(min(temp))
        teachers[index] += 1
        #print("Before "+str(W[i]))
        #print("After "+str(temp))
        s += temp[index]
        trace.append(index)
    return s,trace

s,trace = greedy(W[:])
print("Set the minimun cost as "+str(s)+" Trace:"+str(trace))
print("Courses:")
for i in range(b.shape[0]):
    print(b.iloc[i,0]+":"+a.iloc[trace[i],0])

trace = []
teachers = [0]*a.shape[0]
n = len(W)-len(W[j])
best3strategies = []
best3cost = []
cost = 0
mincost = 300 
mincost = s+1
dfs(0)
start=time.time()
for i in range(len(best3cost)):
    print("Strategy "+str(i)+":"+str(best3cost[i]))
    print(best3strategies[i])
    print("Courses:")
    for j in range(b.shape[0]):
        print(b.iloc[j,0]+":"+a.iloc[best3strategies[i][j],0])
end=time.time()
print("The procession took "+str(end-start)+" seconds")

for i in range(a.shape[0]):
    a.iloc[i,a.shape[1]-1] = b[b.Code==a.iloc[i,a.shape[1]-1]].Course.values[0]
a.to_csv("temp_instructor.csv",index=False)
b.to_csv("temp_course.csv",index=False)
#type([])==list
