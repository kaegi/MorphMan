from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from .util import mw

class CustomTableWidget(QTableWidget):
    def __init__(self, parent):
        super(CustomTableWidget, self).__init__(parent)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Copy):
            text = ''
            sel_range = self.selectionModel().selection().first()

            for y in range(sel_range.top(), sel_range.bottom()+1):
                for x in range(sel_range.left(), sel_range.right()+1):
                    if x != sel_range.left(): text += '\t'
                    text += str(self.item(y,x).text())
                    pass
                text += '\n'

            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            event.accept()
            return
        super(CustomTableWidget, self).keyPressEvent(event)
