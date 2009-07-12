### Copyright (C) 2002-2006 Stephen Kennedy <stevek@gnome.org>

### This program is free software; you can redistribute it and/or modify
### it under the terms of the GNU General Public License as published by
### the Free Software Foundation; either version 2 of the License, or
### (at your option) any later version.

### This program is distributed in the hope that it will be useful,
### but WITHOUT ANY WARRANTY; without even the implied warranty of
### MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
### GNU General Public License for more details.

### You should have received a copy of the GNU General Public License
### along with this program; if not, write to the Free Software
### Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import gobject
import task
import undo
import gtk
import os
from gettext import gettext as _

# Use these to ensure consistent return values.
RESULT_OK, RESULT_ERROR = (0,1)

class MeldDoc(gobject.GObject):
    """Base class for documents in the meld application.
    """

    __gsignals__ = {
        'label-changed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        'file-changed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        'create-diff': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        'status-changed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
    }

    def __init__(self, prefs):
        gobject.GObject.__init__(self)
        self.undosequence = undo.UndoSequence()
        self.undosequence_busy = 0
        self.scheduler = task.FifoScheduler()
        self.prefs = prefs
        self.prefs.notify_add(self.on_preference_changed)
        self.num_panes = 0
        self.label_text = _("untitled")

    def save(self):
        pass

    def save_as(self):
        pass

    def stop(self):
        if self.scheduler.tasks_pending():
            self.scheduler.remove_task(self.scheduler.get_current_task())

    def _open_files(self, selected):
        files = [f for f in selected if os.path.isfile(f)]
        dirs =  [d for d in selected if os.path.isdir(d)]
        if len(files):
            if self.prefs.edit_command_type == "internal":
                for f in files:
                    self.emit("create-diff", (f,))
            elif self.prefs.edit_command_type == "gnome":
                cmd = self.prefs.get_gnome_editor_command(files)
                os.spawnvp(os.P_NOWAIT, cmd[0], cmd)
            elif self.prefs.edit_command_type == "custom":
                cmd = self.prefs.get_custom_editor_command(files)
                os.spawnvp(os.P_NOWAIT, cmd[0], cmd)
        for d in dirs:
            cmd = ["xdg-open", d]
            os.spawnvp(os.P_NOWAIT, cmd[0], cmd)

    def on_undo_activate(self):
        if self.undosequence.can_undo():
            self.undosequence_busy = 1
            try:
                self.undosequence.undo()
            finally:
                self.undosequence_busy = 0

    def on_redo_activate(self):
        if self.undosequence.can_redo():
            self.undosequence_busy = 1
            try:
                self.undosequence.redo()
            finally:
                self.undosequence_busy = 0
            self.undosequence_busy = 0

    def on_refresh_activate(self, *extra):
        self.on_reload_activate(self, *extra)
    def on_reload_activate(self, *extra):
        pass
    def on_find_activate(self, *extra):
        pass
    def on_find_next_activate(self, *extra):
        pass
    def on_find_previous_activate(self, *extra):
        pass
    def on_replace_activate(self, *extra):
        pass

    def on_preference_changed(self, key, value):
        pass

    def on_file_changed(self, filename):
        pass

    def label_changed(self):
        self.emit("label-changed", self.label_text)

    def set_labels(self, lst):
        pass

    def on_container_switch_in_event(self, uimanager):
        """Called when the container app switches to this tab.
        """
        self.ui_merge_id = uimanager.add_ui_from_file(self.ui_file)
        uimanager.insert_action_group(self.actiongroup, -1)
        self.popup_menu = uimanager.get_widget("/Popup")
        uimanager.ensure_update()

    def on_container_switch_out_event(self, uimanager):
        """Called when the container app switches away from this tab.
        """
        uimanager.remove_action_group(self.actiongroup)
        uimanager.remove_ui(self.ui_merge_id)

    def on_delete_event(self, appquit=0):
        """Called when the docs container is about to close.
           A doc normally returns gtk.RESPONSE_OK but may return
           gtk.RESPONSE_CANCEL which requests the container
           to not delete it. In the special case when the
           app is about to quit, gtk.RESPONSE_CLOSE may be returned
           which instructs the container to quit without any
           more callbacks.
        """
        return gtk.RESPONSE_OK

    def on_quit_event(self):
        """Called when the docs container is about to close.
           There is no way to interrupt the quit event.
        """
        pass

