from aqt.qt import QApplication, QTableWidget, QKeySequence

class CustomTableWidget(QTableWidget):

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.StandardKey.Copy):
            text = ''
            sel_range = self.selectionModel().selection().first()

            for y in range(sel_range.top(), sel_range.bottom()+1):
                for x in range(sel_range.left(), sel_range.right()+1):
                    if x != sel_range.left(): text += '\t'
                    text += str(self.item(y,x).text())
                text += '\n'

            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            event.accept()
            return
        super(CustomTableWidget, self).keyPressEvent(event)
