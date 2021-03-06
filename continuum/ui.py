"""
    This file is part of the continuum IDA PRO plugin (see zyantific.com).

    The MIT License (MIT)

    Copyright (c) 2016 Joel Hoener <athre0z@zyantific.com>

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:
    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
"""
from __future__ import absolute_import, print_function, division

import os
import sys
import sip
from PyQt5 import uic
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QFileInfo
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFileDialog, QListWidgetItem, QTreeWidgetItem, QFileIconProvider
from idaapi import PluginForm

from .project import Project


ui_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ui')
Ui_ProjectCreationDialog, ProjectCreationDialogBase = uic.loadUiType(
    os.path.join(ui_dir, 'ProjectCreationDialog.ui')
)
Ui_ProjectExplorerWidget, ProjectExplorerWidgetBase = uic.loadUiType(
    os.path.join(ui_dir, 'ProjectExplorer.ui')
)


class ProjectCreationDialog(ProjectCreationDialogBase):
    """Dialog allowing convenient project creation."""
    def __init__(self, initial_path=None):
        super(ProjectCreationDialog, self).__init__()

        self._ui = Ui_ProjectCreationDialog()
        self._ui.setupUi(self)

        if initial_path:
            self._ui.project_path.setText(os.path.realpath(initial_path))
            self.update_binary_list()

        self._ui.browse_project_path.clicked.connect(self._browse_project_path)
        self._ui.project_path.textChanged.connect(self.update_binary_list)
        self._ui.file_patterns.textChanged.connect(self.update_binary_list)

    def _browse_project_path(self):
        path = QFileDialog.getExistingDirectory()
        path = os.path.realpath(path)
        self._ui.project_path.setText(path)

    def update_binary_list(self, *_):
        binaries = Project.find_project_files(
            self._ui.project_path.text(),
            self._ui.file_patterns.text(),
        )

        self._ui.binary_list.clear()
        for cur_binary in binaries:
            item = QListWidgetItem(cur_binary)
            self._ui.binary_list.addItem(item)

    @property
    def project_path(self):
        return self._ui.project_path.text()

    @property
    def file_patterns(self):
        return self._ui.file_patterns.text()
    

class ProjectExplorerWidget(QObject, PluginForm):
    """Project explorer widget, usually mounted to IDA's "sidebar"."""
    focus_instance_clicked = pyqtSignal([str])  # idb_path: str
    refresh_project_clicked = pyqtSignal()
    open_project_settings_clicked = pyqtSignal()

    def __init__(self, project):
        super(ProjectExplorerWidget, self).__init__()
        self.project = project
        self._tform = None
        self._qwidget = None
        self._ui = None

    def OnCreate(self, form):
        self._tform = form
        self._qwidget = self.FormToPyQtWidget(form, sys.modules[__name__])

        # Setup UI.
        self._ui = Ui_ProjectExplorerWidget()
        self._ui.setupUi(self._qwidget)

        # Load icons.
        self._ui.open_project_settings.setIcon(
            QIcon(os.path.join(ui_dir, 'page_gear.png'))
        )
        self._ui.refresh_project_files.setIcon(
            QIcon(os.path.join(ui_dir, 'arrow_refresh.png'))
        )

        # Subscribe events.
        self._ui.open_project_settings.clicked.connect(
            lambda _: self.open_project_settings_clicked.emit()
        )
        self._ui.refresh_project_files.clicked.connect(
            lambda _: self.refresh_project_clicked.emit()
        )
        self._ui.project_tree.itemDoubleClicked.connect(
            lambda item, _: self.focus_instance_clicked.emit(item.data(0, Qt.UserRole))
        )

        self.update()

    def update(self):
        # Update files.
        self._ui.project_tree.clear()
        items = []
        icon_provider = QFileIconProvider()

        for cur_file in self.project.files:
            file_info = QFileInfo(cur_file)
            item = QTreeWidgetItem(None, [
                os.path.relpath(cur_file, self.project.proj_dir), 
                "N/A",
            ])
            item.setData(0, Qt.UserRole, Project.file_to_idb(cur_file))
            item.setIcon(0, icon_provider.icon(file_info))
            items.append(item)

        self._ui.project_tree.insertTopLevelItems(0, items)

        # Update other stuff.
        self._ui.project_path.setText(self.project.proj_dir)
