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
from .form import *
from flask_appbuilder.baseviews import BaseCRUDView, BaseFormView, BaseView, expose, expose_api
from flask_appbuilder._compat import as_unicode
import logging
from werkzeug.utils import secure_filename
from .calculation import Calculator
import re

log = logging.getLogger(__name__)
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
            getChoices()
            flash(as_unicode(self.message), "info")


#appbuilder.add_view_no_menu(UploadView)
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
        course = pd.read_csv(os.path.join(app.config["UPLOAD_FOLDER"],name))
        choices = course.iloc[:,1].tolist()
        choices = [(i,choices[i]) for i in range(len(choices))]
        U.course = course
        U.choices = choices
    if os.path.exists(os.path.join(app.config["UPLOAD_FOLDER"],app.config["INSTRUCTOR"])):
        U.instructor = pd.read_csv(os.path.join(app.config["UPLOAD_FOLDER"],app.config["INSTRUCTOR"]))
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


class FillupView(SimpleFormView):
    form = FillupForm
    form_title = _('Please complete the following options')
    message = "Submitted Successfully"
    user_info = ""

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
        #log.debug(U.instructor)
        user_info = U.instructor[U.instructor.email==user.email]
        courses = U.course
        log.debug(user_info)
        if user_info.shape[0]<=0:
            return True
        columns = user_info.columns[2:10]
        prechoice = user_info.iloc[0,2:10]
        #pd.isna(prechoice[0])
        for j,i in enumerate(columns):
            if not pd.isna(prechoice[j]) and prechoice[j] in courses['Code'].values:
                form.listoffield[i].description = "You have chose "+prechoice[j]+"."

    def form_post(self,form):
        user = g.user
        user_info = U.instructor[U.instructor.email==user.email]#read the index
        #if user_info.shape[0]<=0:#if user is not in the list
        #    flash(as_unicode("You are not in the list of valid users."), "danger")
        #    return redirect(appbuilder.get_url_for_index)    
        index = user_info.index[0]
        columns = U.instructor.columns[2:10]
        for i in columns:
            U.lock.acquire()
            U.instructor.loc[index,i] = form.listoffield[i].data
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
    form_title = _("Please choose the allocation strategy")
    form_template = "edit.html"
    message = "Saved successfully"
    @expose("/form", methods=["GET"])
    @has_access
    def this_form_get(self):
        self._init_vars()
        form = self.form.refresh()
        if len(U.course)==0 or len(U.sysconfig)==0 or len(U.instructor)==0:
            flash(as_unicode(self.error_message), "danger")
            return redirect(appbuilder.get_url_for_index)
        self.calculator = Calculator(U.instructor,U.course,U.sysconfig)
        self.calculator.calculate() 
        costs,strategies,index = self.calculator.fetch_result2()
        self.form_get(form,costs)
        widgets = self._get_edit_widget(form=form)
        self.update_redirect()
        #print(self.form_template)
        return self.render_template(
            self.form_template,
            title=self.form_title,
            widgets=widgets,
            appbuilder=self.appbuilder,
            strategies = strategies.to_html()
        )
    def form_get(self,form,costs):
        #print(costs)
        Strategy = ""
        for i in range(len(costs)):
            Strategy += "Cost of Strategy "+str(i+1)+": "+str(costs[i])+" | "
        form.Strategy.description = Strategy

    def form_post(self,form):
        s = [form.Strategy.choices[i][0] for i in range(3)]
        s = s.index(form.Strategy.data)
        _,strategies,index = self.calculator.fetch_result2()
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
            teachers = teachers.split("/")
            for t in teachers:
                t=t.split("(")
                #print(c,t)
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
    category_icon='fa-list')
        #read result csv

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
                #return self.render_template(
                #        self.form_template,
                #        title=self.form_title,
                #        widgets=widgets,
                #        appbuilder=self.appbuilder,
                #        strategies = strategies.to_html()
                #    )
        else:
            flash(as_unicode("The administrator has not generated the result. Please check it later."), "danger")
            return redirect(appbuilder.get_url_for_index)

appbuilder.add_view(
    ResultView,
    'ResultView',
    label=_('Check Result'),
    icon='fa-check-square-o',
    category='Result',
    category_label=_('Result'),
    category_icon='fa-list')
#appbuilder.add_link(
#    href = "/Result",
#    name = "Result",
#    category='Result',
#    category_label=_('Result'),
#    category_icon='fa-table')
        


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

