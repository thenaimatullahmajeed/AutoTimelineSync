"""D1/D2 review integration on the actual ATS windows and import worker."""
import json,re
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QDialog,QVBoxLayout,QPlainTextEdit,QPushButton,QLabel,QApplication,QHBoxLayout
from .sync_diagnostics import validate_all,copy_message,COPY_HEADER
from .sync_modes import utilization
_applied=False

def report_dialog(parent,diagnostics,usage=None):
    d=QDialog(parent);d.setWindowTitle('ATS validation and utilization');d.resize(940,610)
    layout=QVBoxLayout(d)
    errors=sum(x['severity']=='ERROR' for x in diagnostics['diagnostics'])
    layout.addWidget(QLabel(f'{errors} errors · {sum(x["severity"]=="WARN" for x in diagnostics["diagnostics"])} warnings · {sum(x["severity"]=="SKIP" for x in diagnostics["diagnostics"])} skipped items'))
    text=QPlainTextEdit();text.setReadOnly(True);text.setPlainText(copy_message(diagnostics));layout.addWidget(text)
    d.copy_errors=QPushButton('Copy errors for ChatGPT');d.copy_errors.clicked.connect(lambda:QApplication.clipboard().setText(copy_message(diagnostics)));layout.addWidget(d.copy_errors)
    if usage:
        line=QLabel(usage['utilization_line']);line.setWordWrap(True);layout.addWidget(line)
        usage_text=QPlainTextEdit();usage_text.setReadOnly(True);usage_text.setPlainText(json.dumps(usage,ensure_ascii=False,indent=2));layout.addWidget(usage_text)
        d.copy_utilization=QPushButton('Copy utilization');d.copy_utilization.clicked.connect(lambda:QApplication.clipboard().setText(usage['utilization_line']));layout.addWidget(d.copy_utilization)
    close=QPushButton('Close');close.clicked.connect(d.accept);layout.addWidget(close)
    return d

def accepted_report(project,spec):
    report=validate_all(project.script)
    # Actual Project.validate/build_spec/choose_cues are the acceptance oracle.
    # A secondary diagnostic must not invent a new rejection rule.
    for item in report['diagnostics']:
        if item['severity']=='ERROR':
            item.update(severity='WARN',rule='diagnostic_oracle_disagreement',expected='Production import accepted. '+item['expected'])
    report['valid']=True
    for message in spec.warnings:
        if not any(x['message']==message for x in report['diagnostics']):report['diagnostics'].append({'path':'$.scenes','rule':'render_clamp','value':None,'expected':message,'message':message,'severity':'WARN','app_path':None})
    for message in spec.changes.get('moment_notices',[]):
        if not any(x['message']==message for x in report['diagnostics']):report['diagnostics'].append({'path':'$.moments','rule':'moment_crop','value':None,'expected':message,'message':message,'severity':'SKIP','app_path':None})
    return report

def apply():
    global _applied
    if _applied:return
    _applied=True
    from .ui_parts import dialogs
    from .ui import MainWindow
    from .pro_spec import build_spec
    from .pro_audio import choose_cues

    def worker_run(self):
        try:
            p=self.project.validate();spec=build_spec(p.effective_package(),p.images,p.settings())
            choose_cues(spec,0,p.package.pro.get('direction',{}).get('sfx_enabled',True))
            p.sync_diagnostics=accepted_report(p,spec)
            p.sync_utilization=utilization(p.effective_package(),p.images,p.settings(),spec)
            if not self.isInterruptionRequested():self.ready.emit(p,spec)
        except Exception as exc:
            try:report=validate_all(self.project.script)
            except Exception as diagnostic_exc:
                report={'valid':False,'diagnostics':[{'path':'$','rule':'diagnostic_internal','value':None,'expected':str(diagnostic_exc),'message':str(diagnostic_exc),'severity':'WARN','app_path':None}]}
            message=str(exc)
            if not any(x['severity']=='ERROR' for x in report['diagnostics']):
                match=re.match(r'(\$[^:]*):\s*(.*)',message)
                path,expected=match.groups() if match else ('$',message)
                report['diagnostics'].append({'path':path,'rule':'production_import','value':None,'expected':expected,'message':message,'severity':'ERROR','app_path':path if match else None})
            report['valid']=False;self.diagnostics=report
            if not self.isInterruptionRequested():self.failed.emit(copy_message(report))
    dialogs.ImportWorker.run=worker_run

    original_init=dialogs.LaunchDialog.__init__
    def launch_init(self,*args,**kwargs):
        original_init(self,*args,**kwargs)
        self.copy.setText('Copy errors for ChatGPT')
        self.all_errors=QPushButton('Validate all',self)
        row=self.rows['script'];row.layout().addWidget(self.all_errors)
        self.all_errors.clicked.connect(lambda:self.open_sync_validation())
    dialogs.LaunchDialog.__init__=launch_init
    def open_validation(self):
        report=validate_all(self.script_text);self.sync_report_dialog=report_dialog(self,report)
        self.sync_report_dialog.open()
    dialogs.LaunchDialog.open_sync_validation=open_validation
    def show_error(self,message):
        if not message.startswith(COPY_HEADER):
            try:report=validate_all(self.script_text)
            except Exception:report={'valid':False,'diagnostics':[]}
            if not any(item.get('message')==message for item in report['diagnostics']):
                match=re.match(r'(\$[^:]*):\s*(.*)',message)
                path,expected=match.groups() if match else ('$',message)
                report['diagnostics'].append({'path':path,'rule':'production_import','value':None,'expected':expected,
                    'message':message,'severity':'ERROR','app_path':path if match else None})
            message=copy_message(report)
        self.error=message;count=sum(line.endswith(' | ERROR') for line in message.splitlines()[2:])
        self.summary.setText(f'{count} errors found. Use Validate all or Copy errors for ChatGPT.');self.summary.setWordWrap(True);self.summary.setMaximumHeight(70);self.copy.show();self.create.setEnabled(False)
    dialogs.LaunchDialog.show_error=show_error

    original_apply=MainWindow.apply_project
    def apply_project(self,project,spec=None):
        original_apply(self,project,spec)
        project.sync_diagnostics=accepted_report(project,self.spec)
        project.sync_utilization=utilization(project.effective_package(),project.images,project.settings(),self.spec)
        QTimer.singleShot(0,lambda:show_report(self) if not getattr(self,'closing',False) else None)
    MainWindow.apply_project=apply_project
    original_notices=MainWindow.show_notices
    def show_report(self):
        p=getattr(self,'project',None)
        if not p or not hasattr(p,'sync_utilization'):return original_notices(self)
        self.sync_report_dialog=report_dialog(self,p.sync_diagnostics,p.sync_utilization);self.sync_report_dialog.open()
    MainWindow.show_notices=show_report
