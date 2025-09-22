#!/usr/bin/env python3
"""A simple gui interface"""
import sys
import traceback
import webbrowser

import config
from pmca.commands.usb import *
from pmca.platform.backend.senser import *
from pmca.platform.backend.usb import *
from pmca.platform.tweaks import *
from pmca.ui import *
from pmca.i18n import i18n_manager, _

if getattr(sys, 'frozen', False):
 from frozenversion import version
else:
 version = None

class PrintRedirector(object):
 """Redirect writes to a function"""
 def __init__(self, func, parent=None):
  self.func = func
  self.parent = parent
 def write(self, str):
  if self.parent:
   self.parent.write(str)
  self.func(str)
 def flush(self):
  self.parent.flush()


class AppLoadTask(BackgroundTask):
 def doBefore(self):
  self.ui.setAppList([])
  self.ui.appLoadButton.config(state=DISABLED)

 def do(self, arg):
  try:
   print('')
   return list(listApps().values())
  except Exception:
   traceback.print_exc()

 def doAfter(self, result):
  if result:
   self.ui.setAppList(result)
  self.ui.appLoadButton.config(state=NORMAL)


class InfoTask(BackgroundTask):
 """Task to run infoCommand()"""
 def doBefore(self):
  self.ui.infoButton.config(state=DISABLED)

 def do(self, arg):
  try:
   print('')
   infoCommand()
  except Exception:
   traceback.print_exc()

 def doAfter(self, result):
  self.ui.infoButton.config(state=NORMAL)


class InstallTask(BackgroundTask):
 """Task to run installCommand()"""
 def doBefore(self):
  self.ui.installButton.config(state=DISABLED)
  return self.ui.getMode(), self.ui.getSelectedApk(), self.ui.getSelectedApp()

 def do(self, args):
  (mode, apkFilename, app) = args
  try:
   print('')
   if mode == self.ui.MODE_APP and app:
    installCommand(appPackage=app.package)
   elif mode == self.ui.MODE_APK and apkFilename:
    with open(apkFilename, 'rb') as f:
     installCommand(apkFile=f)
   else:
    installCommand()
  except Exception:
   traceback.print_exc()

 def doAfter(self, result):
  self.ui.installButton.config(state=NORMAL)


class FirmwareUpdateTask(BackgroundTask):
 """Task to run firmwareUpdateCommand()"""
 def doBefore(self):
  self.ui.fwUpdateButton.config(state=DISABLED)
  return self.ui.getSelectedDat()

 def do(self, datFile):
  try:
   if datFile:
    print('')
    with open(datFile, 'rb') as f:
     firmwareUpdateCommand(f)
  except Exception:
   traceback.print_exc()

 def doAfter(self, result):
  self.ui.fwUpdateButton.config(state=NORMAL)


class StartPlatformShellTask(BackgroundTask):
 def doBefore(self):
  self.ui.startUpdaterShellButton.config(state=DISABLED)
  self.ui.startSenserShellButton.config(state=DISABLED)

 def do(self, arg):
  try:
   print('')
   self.start()
  except Exception:
   traceback.print_exc()

 def start(self):
  pass

 def launchShell(self, backend):
  backend.start()
  tweaks = TweakInterface(backend)

  if next(tweaks.getTweaks(), None):
   endFlag = threading.Event()
   root = self.ui.master
   root.run(lambda: root.after(0, lambda: TweakDialog(root, tweaks, endFlag)))
   endFlag.wait()
  else:
   print(_('no_tweaks_available'))

  backend.stop()

 def doAfter(self, result):
  self.ui.startUpdaterShellButton.config(state=NORMAL)
  self.ui.startSenserShellButton.config(state=NORMAL)


class StartUpdaterShellTask(StartPlatformShellTask):
 """Task to run updaterShellCommand() and open TweakDialog"""
 def start(self):
  updaterShellCommand(complete=lambda dev: self.launchShell(UsbPlatformBackend(dev)))


class StartSenserShellTask(StartPlatformShellTask):
 """Task to run senserShellCommand() and open TweakDialog"""
 def start(self):
  senserShellCommand(complete=lambda dev: self.launchShell(SenserPlatformBackend(dev)))


class ExportBackupTask(BackgroundTask):
 """Task to export backup data from camera"""
 def doBefore(self):
  self.ui.exportBackupButton.config(state=DISABLED)

 def do(self, arg):
  try:
   print(_('exporting_backup_data'))
   from pmca.commands.usb import senserShellCommand
   from pmca.platform.backend.senser import SenserPlatformBackend
   from pmca.platform.backup import BackupPatchDataInterface
   from tkinter.filedialog import asksaveasfilename
   import json
   
   # Use senserShellCommand to switch to service mode and get device
   def complete(dev):
    backend = SenserPlatformBackend(dev)
    try:
     # Get backup interface
     backupInterface = BackupPatchDataInterface(backend)
     
     # Read all backup properties
     print(_('reading_backup_data'))
     backupData = {}
     for propId, prop in backupInterface.backup.listProperties():
      propKey = f"0x{propId:08x}"
      backupData[propKey] = {
       'id': propId,
       'attr': prop.attr,
       'data': list(prop.data) if prop.data else [],
       'resetData': list(prop.resetData) if prop.resetData else None
      }
     
     # Show save dialog in main thread
     def showSaveDialog():
      return asksaveasfilename(
       defaultextension='.json',
       filetypes=[(_('json_files'), '*.json'), (_('all_files'), '*.*')],
       title=_('save_backup_data')
      )
     
     # Get save path from main thread
     import threading
     result = {}
     event = threading.Event()
     
     def getSavePath():
      result['path'] = showSaveDialog()
      event.set()
     
     # Run save dialog in main thread
     self.ui.master.after(0, getSavePath)
     event.wait()
     
     if result.get('path'):
      # Save backup data to file
      print(_('saving_backup_file'))
      with open(result['path'], 'w', encoding='utf-8') as f:
       json.dump(backupData, f, indent=2, ensure_ascii=False)
      
      print(_('backup_export_success', filename=os.path.basename(result['path'])))
      print(_('total_properties_exported', count=len(backupData)))
     else:
      print(_('export_cancelled'))
      
    except Exception as e:
     print(f"Error during backup export: {e}")
     import traceback
     traceback.print_exc()
   
   # Start the service mode shell command
   senserShellCommand(complete=complete)
   
  except Exception as e:
   print(f"Error: {e}")
   import traceback
   traceback.print_exc()

 def doAfter(self, result):
  self.ui.exportBackupButton.config(state=NORMAL)


class TweakApplyTask(BackgroundTask):
 """Task to run TweakInterface.apply()"""
 def doBefore(self):
  self.ui.setState(DISABLED)

 def do(self, arg):
  try:
   print(_('applying_tweaks'))
   self.ui.tweakInterface.apply()
  except Exception:
   traceback.print_exc()

 def doAfter(self, result):
  self.ui.setState(NORMAL)
  self.ui.cancel()


class MainUi(UiRoot):
 """Main window"""
 def __init__(self, title):
  UiRoot.__init__(self)

  self.title(title)
  self.geometry('450x500')
  self['menu'] = Menu(self)

  tabs = Notebook(self, padding=5)
  tabs.pack(fill=X)

  tabs.add(InfoFrame(self, padding=10), text=_('camera_info'))
  tabs.add(InstallerFrame(self, padding=10), text=_('install_app'))
  tabs.add(UpdaterShellFrame(self, padding=10), text=_('tweaks'))
  tabs.add(FirmwareFrame(self, padding=10), text=_('update_firmware'))
  tabs.add(SettingsFrame(self, padding=10), text=_('settings'))

  docsLink = Label(self, text=_('camera_compatibility'), foreground='blue', cursor='hand2')
  docsLink.bind('<Button-1>', lambda e: webbrowser.open_new(config.docsUrl + '/devices.html'))
  docsLink.pack(pady=(0, 5))

  self.logText = ScrollingText(self)
  self.logText.text.configure(state=DISABLED)
  self.logText.pack(fill=BOTH, expand=True)

  self.redirectStreams()

 def log(self, msg):
  self.logText.text.configure(state=NORMAL)
  self.logText.text.insert(END, msg)
  self.logText.text.configure(state=DISABLED)
  self.logText.text.see(END)

 def redirectStreams(self):
  for stream in ['stdout', 'stderr']:
   setattr(sys, stream, PrintRedirector(lambda str: self.run(lambda: self.log(str)), getattr(sys, stream)))

 def refresh_ui(self):
  """Refresh UI text with current language"""
  # Update window title (keep original for now)
  # self.title('OpenMemories: pmca-gui' + (' ' + version if version else ''))
  
  # Update tab text - this requires recreating the notebook or updating tab text
  # For now, we'll show a message that restart is needed
  from tkinter import messagebox
  messagebox.showinfo(_("settings"), _("restart_to_apply_changes"))


class InfoFrame(UiFrame):
 def __init__(self, parent, **kwargs):
  UiFrame.__init__(self, parent, **kwargs)

  self.infoButton = Button(self, text=_('get_camera_info'), command=InfoTask(self).run, padding=5)
  self.infoButton.pack(fill=X)


class InstallerFrame(UiFrame):
 MODE_APP = 0
 MODE_APK = 1

 def __init__(self, parent, **kwargs):
  UiFrame.__init__(self, parent, **kwargs)

  self.modeVar = IntVar(value=self.MODE_APP)

  appFrame = Labelframe(self, padding=5)
  appFrame['labelwidget'] = Radiobutton(appFrame, text=_('select_app_from_list'), variable=self.modeVar, value=self.MODE_APP)
  appFrame.columnconfigure(0, weight=1)
  appFrame.pack(fill=X)

  self.appCombo = Combobox(appFrame, state='readonly')
  self.appCombo.bind('<<ComboboxSelected>>', lambda e: self.modeVar.set(self.MODE_APP))
  self.appCombo.grid(row=0, column=0, sticky=W+E)
  self.setAppList([])

  self.appLoadButton = Button(appFrame, text=_('refresh'), command=AppLoadTask(self).run)
  self.appLoadButton.grid(row=0, column=1)

  appListLink = Label(appFrame, text=_('source'), foreground='blue', cursor='hand2')
  appListLink.bind('<Button-1>', lambda e: webbrowser.open_new('https://github.com/' + config.githubAppListUser + '/' + config.githubAppListRepo))
  appListLink.grid(columnspan=2, sticky=W)

  apkFrame = Labelframe(self, padding=5)
  apkFrame['labelwidget'] = Radiobutton(apkFrame, text=_('select_apk'), variable=self.modeVar, value=self.MODE_APK)
  apkFrame.columnconfigure(0, weight=1)
  apkFrame.pack(fill=X)

  self.apkFile = Entry(apkFrame)
  self.apkFile.grid(row=0, column=0, sticky=W+E)

  self.apkSelectButton = Button(apkFrame, text=_('open_apk'), command=self.openApk)
  self.apkSelectButton.grid(row=0, column=1)

  self.installButton = Button(self, text=_('install_selected_app'), command=InstallTask(self).run, padding=5)
  self.installButton.pack(fill=X, pady=(5, 0))

  self.run(AppLoadTask(self).run)

 def getMode(self):
  return self.modeVar.get()

 def openApk(self):
  fn = askopenfilename(filetypes=[(_('apk_files'), '.apk'), (_('all_files'), '.*')])
  if fn:
   self.apkFile.delete(0, END)
   self.apkFile.insert(0, fn)
   self.modeVar.set(self.MODE_APK)

 def getSelectedApk(self):
  return self.apkFile.get()

 def setAppList(self, apps):
  self.appList = apps
  self.appCombo['values'] = [''] + [app.name for app in apps]
  self.appCombo.current(0)

 def getSelectedApp(self):
  if self.appCombo.current() > 0:
   return self.appList[self.appCombo.current() - 1]


class FirmwareFrame(UiFrame):
 def __init__(self, parent, **kwargs):
  UiFrame.__init__(self, parent, **kwargs)

  datFrame = Labelframe(self, padding=5)
  datFrame['labelwidget'] = Label(datFrame, text=_('firmware_file'))
  datFrame.pack(fill=X)

  self.datFile = Entry(datFrame)
  self.datFile.pack(side=LEFT, fill=X, expand=True)

  self.datSelectButton = Button(datFrame, text=_('open'), command=self.openDat)
  self.datSelectButton.pack()

  self.fwUpdateButton = Button(self, text=_('update_firmware'), command=FirmwareUpdateTask(self).run, padding=5)
  self.fwUpdateButton.pack(fill=X, pady=(5, 0))

 def openDat(self):
  fn = askopenfilename(filetypes=[(_('firmware_files'), '.dat'), (_('all_files'), '.*')])
  if fn:
   self.datFile.delete(0, END)
   self.datFile.insert(0, fn)

 def getSelectedDat(self):
  return self.datFile.get()


class UpdaterShellFrame(UiFrame):
 def __init__(self, parent, **kwargs):
  UiFrame.__init__(self, parent, **kwargs)

  self.startUpdaterShellButton = Button(self, text=_('start_tweaking_updater'), command=StartUpdaterShellTask(self).run, padding=5)
  self.startUpdaterShellButton.pack(fill=X)

  self.startSenserShellButton = Button(self, text=_('start_tweaking_service'), command=StartSenserShellTask(self).run, padding=5)
  self.startSenserShellButton.pack(fill=X, pady=(5, 0))

  self.exportBackupButton = Button(self, text=_('export_backup_data'), command=ExportBackupTask(self).run, padding=5)
  self.exportBackupButton.pack(fill=X, pady=(5, 0))


class SettingsFrame(UiFrame):
 def __init__(self, parent, **kwargs):
  UiFrame.__init__(self, parent, **kwargs)
  
  # Language settings section
  langFrame = Labelframe(self, padding=10)
  langFrame['labelwidget'] = Label(langFrame, text=_('language_settings'))
  langFrame.pack(fill=X, pady=(0, 10))

  Label(langFrame, text=_('select_language')).pack(anchor=W, pady=(0, 5))
  
  self.langVar = StringVar(value=i18n_manager.get_language())
  
  # Create radio buttons for each supported language
  for lang_code, lang_name in i18n_manager.get_supported_languages().items():
   rb = Radiobutton(langFrame, text=lang_name, variable=self.langVar, value=lang_code, command=self.on_language_change)
   rb.pack(anchor=W, pady=2)
  
  # Apply button
  self.applyButton = Button(self, text=_('apply'), command=self.apply_settings, padding=5)
  self.applyButton.pack(fill=X, pady=(10, 0))
  
 def on_language_change(self):
  """Called when language selection changes"""
  pass
  
 def apply_settings(self):
  """Apply the selected settings"""
  new_language = self.langVar.get()
  if i18n_manager.set_language(new_language):
   # Show message that restart is needed
   from tkinter import messagebox
   messagebox.showinfo(_("settings"), _("restart_required"))


class TweakDialog(UiDialog):
 def __init__(self, parent, tweakInterface, endFlag=None):
  self.tweakInterface = tweakInterface
  self.endFlag = endFlag
  UiDialog.__init__(self, parent, _("tweaks"))

 def body(self, top):
  tweakFrame = Labelframe(top, padding=5)
  tweakFrame['labelwidget'] = Label(tweakFrame, text=_('tweaks'))
  tweakFrame.pack(fill=X)

  self.boxFrame = Frame(tweakFrame)
  self.boxFrame.pack(fill=BOTH, expand=True)

  self.applyButton = Button(top, text=_('apply'), command=TweakApplyTask(self).run, padding=5)
  self.applyButton.pack(fill=X)

  self.updateStatus()

 def updateStatus(self):
  for child in self.boxFrame.winfo_children():
   child.destroy()
  for id, desc, status, value in self.tweakInterface.getTweaks():
   var = IntVar(value=status)
   c = Checkbutton(self.boxFrame, text=desc + '\n' + value, variable=var, command=lambda id=id, var=var: self.setTweak(id, var.get()))
   c.pack(fill=X)

 def setTweak(self, id, enabled):
  self.tweakInterface.setEnabled(id, enabled)
  self.updateStatus()

 def setState(self, state):
  for widget in self.boxFrame.winfo_children() + [self.applyButton]:
   widget.config(state=state)

 def cancel(self, event=None):
  UiDialog.cancel(self, event)
  if self.endFlag:
   self.endFlag.set()


class SettingsDialog(UiDialog):
 def __init__(self, parent):
  UiDialog.__init__(self, parent, _("language_settings"))

 def body(self, top):
  # Language selection frame
  langFrame = Labelframe(top, padding=10)
  langFrame['labelwidget'] = Label(langFrame, text=_("select_language"))
  langFrame.pack(fill=X, pady=(0, 10))

  self.langVar = StringVar(value=i18n_manager.get_language())
  
  # Create radio buttons for each supported language
  for lang_code, lang_name in i18n_manager.get_supported_languages().items():
   rb = Radiobutton(langFrame, text=lang_name, variable=self.langVar, value=lang_code)
   rb.pack(anchor=W, pady=2)

 def apply(self):
  # Apply language change
  new_language = self.langVar.get()
  if i18n_manager.set_language(new_language):
   # Refresh the main window to apply new language
   self.parent.master.refresh_ui()
  return True


class SettingsDialog(UiDialog):
 def __init__(self, parent):
  UiDialog.__init__(self, parent, _("language_settings"))

 def body(self, top):
  # Language selection frame
  langFrame = Labelframe(top, padding=10)
  langFrame['labelwidget'] = Label(langFrame, text=_("select_language"))
  langFrame.pack(fill=X, pady=(0, 10))

  self.langVar = StringVar(value=i18n_manager.get_language())
  
  # Create radio buttons for each supported language
  for lang_code, lang_name in i18n_manager.get_supported_languages().items():
   rb = Radiobutton(langFrame, text=lang_name, variable=self.langVar, value=lang_code)
   rb.pack(anchor=W, pady=2)

 def apply(self):
  # Apply language change
  new_language = self.langVar.get()
  if i18n_manager.set_language(new_language):
   # Refresh the main window to apply new language
   self.parent.master.refresh_ui()
  return True


def main():
 """Gui main"""
 ui = MainUi('OpenMemories: pmca-gui' + (' ' + version if version else ''))
 ui.mainloop()


if __name__ == '__main__':
 main()
