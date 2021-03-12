import os
import time
import zipfile
from flask import flash,render_template,g,url_for,redirect,send_file
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView, ModelRestApi
from flask_appbuilder import IndexView,SimpleFormView
from . import appbuilder, db, app
from . import utils as U
from .models import Instructor
from flask_babel import lazy_gettext as _
from flask_appbuilder.security.decorators import has_access, has_access_api, permission_name
from concurrent.futures import ThreadPoolExecutor
from .form import *
from flask_appbuilder.baseviews import BaseCRUDView, BaseFormView, BaseView, expose, expose_api
from flask_appbuilder._compat import as_unicode
import logging
from werkzeug.utils import secure_filename
from .calculation import Calculator
from wtforms.validators import ValidationError
import re

log = logging.getLogger(__name__)
executor = ThreadPoolExecutor(10)
"""
   Page to submit user's intention
"""
# zipfilename是压缩包名字，dirname是要打包的目录
def compress_file(zipfilename, dirname):  
    if os.path.isfile(dirname):
        with zipfile.ZipFile(zipfilename, 'w', zipfile.ZIP_DEFLATED) as z:
            z.write(dirname)
    else:
        with zipfile.ZipFile(zipfilename, 'w') as z:
            for root, dirs, files in os.walk(dirname):
                for single_file in files:
                    if single_file != zipfilename:
                        filepath = os.path.join(root, single_file)
                        z.write(filepath)

"""
    Upload
"""
class UploadView(SimpleFormView):
    form = UploadForm
    form_title = _('Upload CSVs of settings')
    message = "Uploaded Successfully"

    @expose("/form", methods=["POST"])
    @has_access
    def this_form_post(self):
        self._init_vars()
        form = self.form.refresh()
        if form.validate_on_submit():
            response = self.form_post(form)
            if not response:
                #return redirect(self.get_redirect())
                return redirect(appbuilder.get_url_for_index)
            return response
        else:
            widgets = self._get_edit_widget(form=form)
            return self.render_template(
                self.form_template,
                title=self.form_title,
                widgets=widgets,
                appbuilder=self.appbuilder,
            )

    def form_get(self,form):#prefill
        csv_names = [app.config["INSTRUCTOR"],app.config["COURSE"],app.config["SYSCONFIG"]]
        f = os.path.join(app.config['UPLOAD_FOLDER'], csv_names[0])
        if os.path.exists(f):
            tm = time.ctime(os.path.getmtime(f))
            form.instructor.description = "There is already a file:"+csv_names[0] +" uploaded at "+tm

        f = os.path.join(app.config['UPLOAD_FOLDER'], csv_names[1])
        if os.path.exists(f):
            tm = time.ctime(os.path.getmtime(f))
            form.course.description = "There is already a file:"+csv_names[1] +" uploaded at "+tm

        f = os.path.join(app.config['UPLOAD_FOLDER'], csv_names[2])
        if os.path.exists(f):
            tm = time.ctime(os.path.getmtime(f))
            form.sysconfig.description = "There is already a file:"+csv_names[2] +" uploaded at "+tm

    def form_post(self,form):
        csv_names = [app.config["INSTRUCTOR"],app.config["COURSE"],app.config["SYSCONFIG"]]
        csv_list =  [form.instructor.data,form.course.data,form.sysconfig.data]
        flag = 0
        for i,csv_file in enumerate(csv_list):
            if csv_file is not None:
                f = os.path.join(app.config['UPLOAD_FOLDER'], csv_names[i])
                #csv_file.filename = secure_filename(csv_file.filename)
                #csv_filename = csv_file.filename
                if os.path.exists(f):
                    os.remove(f)#remove
                log.debug("save file:"+f)
                csv_file.save(f)
                flag = 1
        if flag==1:
            app.config['SETTING_RENEWED'] = True #mark for calculation
            getChoices()
            flash(as_unicode(self.message), "info")

appbuilder.add_view(
    UploadView,
    'Upload CSVs to initialize the system',
    label=_('Upload CSVs to initialize the system'),
    icon='fa-upload',
    category='Setting',
    category_label=_('Setting'),
    category_icon='fa-wrench')

#Submit form
def getChoices():
    name = app.config["COURSE"]
    if os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"],name)):
        #Load and sort
        course = pd.read_csv(os.path.join(app.config["UPLOAD_FOLDER"],name))
        course.sort_values("Act",inplace=True,ascending=False)
        course.to_csv(os.path.join(app.config["UPLOAD_FOLDER"],name),index=False)
        course = pd.read_csv(os.path.join(app.config["UPLOAD_FOLDER"],name))

        choices = course.iloc[:,1].tolist()
        choices = [(i,choices[i]) for i in range(len(choices))]
        U.course = course
        U.choices = choices
    if os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"],app.config["INSTRUCTOR"])):
        U.lock.acquire()
        U.instructor = pd.read_csv(os.path.join(app.config["UPLOAD_FOLDER"],app.config["INSTRUCTOR"]))
        U.lock.release()
        if U.instructor.shape[1]==2:
            U.instructor['FirstP'] = ""
            U.instructor['SecondP'] = ""
            U.instructor['ThirdP'] = ""
            U.instructor['FourthP'] = ""
            U.instructor['FifthP'] = ""
            U.instructor['FirstN'] = ""
            U.instructor['SecondN'] = ""
            U.instructor['ThirdN'] = ""
            U.instructor['MaxSec'] = ""

    if os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"],app.config["SYSCONFIG"])):
        U.sysconfig = pd.read_csv(os.path.join(app.config["UPLOAD_FOLDER"],app.config["SYSCONFIG"]))

def seq_sel(pre_choice,s):
    def _seq_sel(form,field):
        #print("XXXXXXXXXXXXXXXXXXXXXX2 "+field.data+"  "+pre_choice.data)
        if field.data!='0' and pre_choice.data=='0':
            raise ValidationError('Please complete previous "'+s+'" options before selecting this.')
    return _seq_sel

class FillupView(SimpleFormView):
    form = FillupForm
    form_title = _('Please complete the following options.  (Your preference input will only be visible to RO and not visible to other instructors.)')
    message = "Submitted Successfully"
    user_info = ""
    columns = U.instructor.columns[2:10]

    @expose("/form", methods=["GET"])
    @has_access
    def this_form_get(self):
        self._init_vars()
        form = self.form.refresh()
        if len(U.instructor)==0:
            flash(as_unicode("The administrator has not uploaded the list of valid users."), "danger")
            return redirect(appbuilder.get_url_for_index)
        r = self.form_get(form)
        if r==True:
            flash(as_unicode("You are not valid user."), "danger")
            return redirect(appbuilder.get_url_for_index)    
        widgets = self._get_edit_widget(form=form)
        self.update_redirect()
        return self.render_template(
            self.form_template,
            title=self.form_title,
            widgets=widgets,
            appbuilder=self.appbuilder,
        )
    def form_get(self,form):
        user = g.user
        log.debug(user.email)
        user_info = U.instructor[U.instructor.email==user.email]
        courses = U.course
        log.debug(user_info)
        if user_info.shape[0]<=0:
            return True
        prechoice = user_info.iloc[0,2:10]
        for j,i in enumerate(self.columns):
            if not pd.isna(prechoice[j]) and prechoice[j] in courses['Code'].values:
                form.listoffield[i].data = user_info.iloc[0,:][i]
                form.listoffield[i].description = "You have chose "+prechoice[j]+"."

    @expose("/form", methods=["POST"])
    @has_access
    def this_form_post(self):
        self._init_vars()
        if app.config['CALCULATING'] == True:
            flash(as_unicode("Allocation routine running in progress. Please submit your form a couple of minutes later."), "danger")
            form = self.form.refresh()
            widgets = self._get_edit_widget(form=form)
            return self.render_template(
                self.form_template,
                title=self.form_title,
                widgets=widgets,
                appbuilder=self.appbuilder,
            )
        elif app.config['CALCULATING'] == False:
            form = self.form.refresh()
            for i,j in enumerate(self.columns):
                if (i>0 and i<5) or i>5:
                    s = "Preference" if i<5 else "Unwanted Course"
                    form.listoffield[j].validators = [seq_sel(form.listoffield[self.columns[i-1]], s)]
            if form.validate_on_submit():
                response = self.form_post(form)
                if not response:
                    #return redirect(self.get_redirect())
                    return redirect(appbuilder.get_url_for_index)
                return response
            else:
                widgets = self._get_edit_widget(form=form)
                return self.render_template(
                    self.form_template,
                    title=self.form_title,
                    widgets=widgets,
                    appbuilder=self.appbuilder,
                )

    def form_post(self,form):
        user = g.user
        user_info = U.instructor[U.instructor.email==user.email]#read the index
        index = user_info.index[0]
        for i in self.columns:
            U.lock.acquire()
            U.instructor.loc[index,i] = form.listoffield[i].data
            app.config['SETTING_RENEWED'] = True #mark for calculation
            U.lock.release()
            log.debug(user.email+":"+i+"-"+form.listoffield[i].data)
        U.instructor.to_csv(os.path.join(app.config["UPLOAD_FOLDER"],app.config["INSTRUCTOR"]),index=False)
        flash(as_unicode(self.message), "info")

appbuilder.add_view(
    FillupView,
    'Fillup',
    label=_('Submit the form of your preference.'),
    icon='fa-send-o',
    category='Fillup',
    category_label=_('Preference'),
    category_icon='fa-wpforms')

#appbuilder.add_link(
#        )

"""
    Download
"""
class DownloadView(BaseView):
    #route_base = "/download"
    default_view = "method1"
    error_message = "Compress Failed or No Files found!"
    @expose('/method1/')
    @has_access
    def method1(self):
        r = self.csvs()    
        if r!=0:
            return send_file(r, as_attachment=True) 
        else:
            flash(as_unicode(self.error_message), "danger")
        return redirect(appbuilder.get_url_for_index)    

    def csvs(self):
        compressed_file = os.path.join(app.config['FILE_FOLDER'],"csvs.zip")
        if not os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'],app.config['SYSCONFIG'])):
            return 0
        z = zipfile.ZipFile(compressed_file, 'w' ,zipfile.ZIP_DEFLATED)
        for i in os.listdir(app.config['UPLOAD_FOLDER']):
            #compress_file(compressed_file,os.path.join(app.config["UPLOAD_FOLDER"],i))
            #print(os.path.join(app.config["UPLOAD_FOLDER"],i),i)
            z.write(os.path.join(app.config["UPLOAD_FOLDER"],i),i)
        z.close()
        if os.path.exists(compressed_file):
            return compressed_file
        else:
            return 0
        
#
appbuilder.add_view(
    DownloadView,
    'Download',
    label=_('Download CSVs.'),
    icon='fa-file',
    category='Download',
    category_label=_('Download'),
    category_icon='fa-download')

"""
    Calculate the loss of Classes Allocation
"""
class CalculateFormView(SimpleFormView):
    error_message = "Please upload the CSVs to initialize the system"
    form = CalculatorForm
    #formv = CalculatorViewForm
    form_title = _("Please choose the allocation strategy")
    form_template = "edit.html"
    vform_template = "instructor_strategy_page.html"
    view_template = "loading.html"
    message = "Saved successfully"
    calculator = Calculator(U.instructor,U.course,U.sysconfig)
    default_view = "form_view"

    def to_html(self,strategies):
        insts = dict()
        for i in range(strategies.shape[0]):
            course = strategies.index[i].split("{")[-1].split("}")[0]
            if re.match("[A-Z]*[a-z]*\d+F",course) is not None:
                continue
            for j in range(strategies.shape[1]):
                teachers = strategies.iloc[i,j]
                ts = teachers.split("|")
                newts = ""
                for t in ts:
                    tn = t.split("(")[0]
                    newts += t
                    #If the course is not tn's preference.
                    if course not in U.instructor[U.instructor.name==tn].iloc[0,2:7].values:
                        newts += " NP"
                    if "history" not in U.instructor.columns or (type(U.instructor[U.instructor.name==tn]["history"].values[0]) is not str) or (course not in U.instructor[U.instructor.name==tn]["history"].values[0]):
                        newts += " NH"
                    newts += "|"
                newts = newts[:-1]
                strategies.iloc[i,j] = newts
            num = int(t.split("(")[1].split(")")[0])
        html = strategies.to_html()
        html = html.replace("|","<br>")
        html += '<p style="text-align:center;font-size:16px;">NP: not a preferred course &nbsp;&nbsp;&nbsp; NH: not a course taught before</p>'
        html = html.replace("NP",'<font color="#A00000">NP</font>')
        html = html.replace("NH",'<font color="#CC6600">NH</font>')

        # Table 2
        results = []
        for i in range(3):
            strategy = strategies.iloc[:,[i]]
            insts = dict()
            for j in range(strategy.shape[0]):
                code = strategies.index[j].split("{")[1].split("}")[0]
                teachers = strategy.iloc[j,0]
                for t in teachers.split("|"):
                    tn = t.split("(")[0]
                    n = int(t.split("(")[1].split(")")[0])
                    insts[tn] = insts.get(tn,dict())
                    insts[tn][code] = insts[tn].get(code,0) + n
            workload = {'# of different courses':[],"# of sections":[],"Equivalent workload":[],"Allocation":[]}
            for j in range(U.instructor.shape[0]):
                name = U.instructor.name[j]
                if name not in insts:
                    workload['# of different courses'].append(0)
                    workload['# of sections'].append(0)
                    workload["Equivalent workload"].append(0)
                    workload["Allocation"].append("-")
                    continue
                workload['# of different courses'].append(len(insts[name]))
                secs = 0
                w = 0
                allocation = ""
                for code in insts[name]:
                    secs += insts[name][code]
                    w += insts[name][code] * U.course[U.course.Code==code]['Ins/Sec'].values[0]
                    allocation += code+"("+str(insts[name][code])+")"+"/"
                allocation = allocation[:-1]
                workload['# of sections'].append(secs)
                workload["Equivalent workload"].append(w)
                workload["Allocation"].append(allocation)
            workload = pd.DataFrame(workload)
            workload.index = U.instructor.name
            html += '<br><br><p tyle="text-align:center;font-size:20px;"><b>Strategy '+str(i+1)+':</b></p>'
            html += workload.to_html()
            results.append(workload.to_html())
        return html

    def calculate(self):
        app.config['CALCULATING'] = True
        CalculateFormView.calculator = Calculator(U.instructor,U.course,U.sysconfig)
        CalculateFormView.calculator.calculate()
        U.lock.acquire()
        app.config['SETTING_RENEWED'] = False
        app.config['CALCULATING'] = False
        U.lock.release()
        return redirect(url_for(self.__class__.__name__+'.this_form_get'))

    @expose("/view",methods=["GET"])
    @has_access
    def form_view(self):
        self._init_vars()
        if len(U.course)==0 or len(U.sysconfig)==0 or len(U.instructor)==0:
            flash(as_unicode(self.error_message), "danger")
            return redirect(appbuilder.get_url_for_index)
        #if os.path.exists(os.path.join(app.config["FILE_FOLDER"],app.config["result"])):
        if app.config["SETTING_RENEWED"] == True:
            if app.config['CALCULATING'] == False:
                try:
                    executor.submit(self.calculate)
                except Exception as e:
                    flash(as_unicode("Error:Calulation Failed"), "danger")
                    log.debug(e)
            return self.render_template(
                        self.view_template,
                        appbuilder = self.appbuilder,
                        result="Success"
                    )
        else:
            return redirect(url_for(self.__class__.__name__+'.this_form_get'))

    @expose("/form", methods=["GET"])
    def this_form_get(self):
        self._init_vars()
        #costs,strategies,index = CalculateFormView.calculator.fetch_result3()
        #try:
        costs,strategies,index = CalculateFormView.calculator.fetch_result3()
        if costs==False:
            flash(as_unicode("Cannot find the strategy"), "danger")

            return redirect(appbuilder.get_url_for_index)
        app.config['SETTING_RENEWED'] = True #mark for calculation
        flash(as_unicode("Error: Fetch result failed. Please retry it."), "danger")

        #return redirect(appbuilder.get_url_for_index)
        form = self.form.refresh()
        self.form_get(form,costs)
        widgets = self._get_edit_widget(form=form)
        self.update_redirect()
        strategies = self.to_html(strategies)
        #For other instructor, show a page without button
        user = g.user
        email = user.email
        if email!=app.config['ADMIN']:
            return self.render_template(
                self.vform_template,
                title="Allocation Strategies(approximate)",
                widgets=widgets,
                appbuilder=self.appbuilder,
                strategies = strategies#.to_html().replace("|","<br>")
            )
        return self.render_template(
            self.form_template,
            title=self.form_title,
            widgets=widgets,
            appbuilder=self.appbuilder,
            strategies = strategies#.to_html().replace("|","<br>")
        )

    def form_get(self,form,costs):
        #print(costs)
        Strategy = ""
        for i in range(len(costs)):
            Strategy += "Cost of Strategy "+str(i+1)+": "+str(costs[i])+" | "
        form.Strategy.description = Strategy

    @expose("/form", methods=["POST"])
    @has_access
    def this_form_post(self):
        self._init_vars()
        #For other instructor, show a page without button
        user = g.user
        email = user.email
        if email!=app.config['ADMIN']:
            #If the user is not admin
            return redirect(appbuilder.get_url_for_index)
        form = self.form.refresh()
        if form.validate_on_submit():
            response = self.form_post(form)
            if not response:
                return redirect(appbuilder.get_url_for_index)
            return response
        else:
            widgets = self._get_edit_widget(form=form)
            return self.render_template(
                self.form_template,
                title=self.form_title,
                widgets=widgets,
                appbuilder=self.appbuilder,
            )

    def form_post(self,form):
        s = [form.Strategy.choices[i][0] for i in range(3)]
        s = s.index(form.Strategy.data)
        _,strategies,index = CalculateFormView.calculator.fetch_result3()
        TermX = self.calculator.config['Term']
        term = "history" #
        U.instructor[term] = ""
        strategy = strategies.iloc[:,s]
        strategyX = strategies.iloc[:,[s]]
        for i in range(strategy.shape[0]):
            c = strategy.index[i].split(" {")[0]
            code = U.course[U.course.Course==c].Code.values[0]
            #print(c)
            teachers = strategy[i]
            if type(teachers) is not str or teachers=="":
                continue
            teachers = teachers.split("|")
            for t in teachers:
                t=t.split("(")
                inst = t[0]
                num = t[1].split(")")[0]
                #if already exists
                if code in U.instructor.loc[U.instructor.name==inst,term].values[0]:
                    continue
                U.lock.acquire()
                if U.instructor.loc[U.instructor.name==inst,term].values[0]!="":
                    U.instructor.loc[U.instructor.name==inst,term] += "/"
                U.instructor.loc[U.instructor.name==inst,term] += code#+"("+num+")"
                U.lock.release()
        #Save
        U.instructor.to_csv(os.path.join(app.config["UPLOAD_FOLDER"],app.config["INSTRUCTOR"]),index=False)
        strategy.to_csv(os.path.join(app.config["UPLOAD_FOLDER"],TermX+"_result.csv"),index=True)
        strategyX.to_html(os.path.join(app.config["FILE_FOLDER"],TermX+"_result.html"),index=True)
        flash(as_unicode(self.message), "info")

appbuilder.add_view(
    CalculateFormView,
    'Allocate',
    label=_('Allocate classes'),
    icon='fa-check-square-o',
    category='Allocation',
    category_label=_('Allocation'),
    category_icon='fa-search')

@app.route('/loading/',methods=['GET'])
def loading():
    flag = 0
    while 1:
        if app.config['CALCULATING'] == False:
            return "Success"
        time.sleep(1)


"""
    Result
"""
class ResultView(BaseView):
    default_view = "result"

    @expose("/result/", methods=["GET"])
    @has_access
    def result(self):
        user = g.user
        email = user.email
        #print(user.roles)
        if email in U.instructor.email.values:
            name = U.instructor[U.instructor.email==email].name.values[0]
        else:
            name = "Not Found"
        sysconfig = U.sysconfig
        TermX = str(int(sysconfig[sysconfig['config']=='Year'].iloc[0,1]))+"-"+str(int(sysconfig[sysconfig['config']=='Term'].iloc[0,1]))
        if os.path.exists(os.path.join(app.config["FILE_FOLDER"],TermX+"_result.html")):
            html = ""
            with open(os.path.join(app.config["FILE_FOLDER"],TermX+"_result.html")) as f:
                html = f.read()
                html = re.sub(name,"<b>"+name+"</b>",html)
                return self.render_template(
                        "result.html", 
                        appbuilder = self.appbuilder, 
                        html = html
                        )
        else:
            flash(as_unicode("The administrator has not generated the result. Please check it later."), "danger")
            return redirect(appbuilder.get_url_for_index)

#appbuilder.add_view(
#    ResultView,
#    'ResultView',
#    label=_('Check Result'),
#    icon='fa-check-square-o',
#    category='Result',
#    category_label=_('Result'),
#    category_icon='fa-columns')

"""
   Overview 
"""
class OverviewView(BaseView):
    default_view = "overview"
    @expose("/overview/", methods=["GET"])
    @has_access
    def overview(self):
        if len(U.course)>0:
            html = U.course[['Course','Code','Act','Ins/Sec']]
            html = html[html['Act']>0]
            html.columns = ['Course','Code','# of Sections','Workload per section']
            html = html.sort_values("Code").to_html(index=False)
            return self.render_template(
                    "overview.html", 
                    appbuilder = self.appbuilder, 
                    html = html
                    )
        else:
            flash(as_unicode("The administrator has not uploaded the course infomation. Please check it later."), "danger")
            return redirect(appbuilder.get_url_for_index)

appbuilder.add_view(
    OverviewView,
    'OverviewView',
    label=_('Course Overview'),
    #icon='fa-align-justify',
    icon='fa-list',
    category='Overview',
    category_label=_('Course Overview'),
    category_icon='fa-list')

"""
    Application wide 404 error handler
"""
@appbuilder.app.errorhandler(404)
def page_not_found(e):
    return (
        render_template(
            "404.html", base_template=appbuilder.base_template, appbuilder=appbuilder
        ),
        404,
    )

db.create_all()

