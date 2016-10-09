from PyQt4.QtCore import *
from PyQt4.QtGui import *

from aqt.utils import tooltip

from util import errorMsg, infoMsg, mw, jcfg, jcfgUpdate, mkBtn
from morphemes import getAllMorphemizers

# only for jedi-auto-completion
import aqt.main
assert isinstance(mw, aqt.main.AnkiQt)

class PreferencesDialog( QDialog ):
    def __init__( self, parent=None ):
        super( PreferencesDialog, self ).__init__( parent )
        self.rowGui = []
        self.resize(1280, 800)

        self.setWindowTitle( 'MorphMan Preferences' )
        self.vbox = vbox = QVBoxLayout(self)

        self.frame1 = QGroupBox("Note Filter")
        vbox = QVBoxLayout(); self.frame1.setLayout(vbox); vbox.setContentsMargins(0, 20, 0, 50)

        self.tableModel = QStandardItemModel(0, 5)
        self.tableView = QTableView()
        self.tableView.setModel(self.tableModel)
        self.tableView.horizontalHeader().setResizeMode(QHeaderView.Stretch)
        self.tableModel.setHeaderData(0, Qt.Horizontal, "Note type")
        self.tableModel.setHeaderData(1, Qt.Horizontal, "Tags")
        self.tableModel.setHeaderData(2, Qt.Horizontal, "Fields")
        self.tableModel.setHeaderData(3, Qt.Horizontal, "Morphemizer")
        self.tableModel.setHeaderData(4, Qt.Horizontal, "Modify?")

        rowData = jcfg('Filter')
        self.tableModel.setRowCount(len(rowData))
        self.rowGui = [None] * len(rowData)
        for i, row in enumerate(rowData):
            self.setTableRow(i, row)

        label = QLabel("Any card that has the given `Note type` and all of the given `Tags` will have its `Fields` analyzed with the specified `Morphemizer`. A morphemizer specifies how words are extraced from a sentence. `Fields` and `Tags` are both comma-separated lists. If `Tags` is empty, there are no tag restrictions. If `Modify` is deactivated, the note will only be analyzed.\n\nIf a note is matched multple times, the first line will take precedence.")
        label.setWordWrap(True)
        vbox.addWidget(label)
        vbox.addWidget(self.tableView)

        hbox = QHBoxLayout(); vbox.addLayout(hbox)
        self.clone = QPushButton("Clone"); hbox.addWidget(self.clone)
        self.delete = QPushButton("Delete"); hbox.addWidget(self.delete)
        self.up = QPushButton("Up"); hbox.addWidget(self.up)
        self.down = QPushButton("Down"); hbox.addWidget(self.down)

        self.vbox.addWidget(self.frame1)

        self.frame2 = QGroupBox("Extra Fields")
        vbox = QVBoxLayout(); self.frame2.setLayout(vbox); vbox.setContentsMargins(0, 20, 0, 50)

        label = QLabel("This plugin will attempt to change the data in following fields. Every field that has a (*) is REQUIRED IN EVERY NOTE for MorphMan to work correctly. The other fields are optional. Hover your mouse over text entries to see tooltip info.")
        label.setWordWrap(True)
        vbox.addWidget(label)

        grid = QGridLayout(); vbox.addLayout(grid)
        numberOfColumns = 3
        fieldsList = [
                ("Focus morph (*):", "Field_FocusMorph"),
                ("MorphMan Index:", "Field_MorphManIndex"),
                ("Unmatures", "Field_Unmatures"),
                ("Unmatures count:", "Field_UnmatureMorphCount"),
                ("Unknowns:", "Field_Unknowns"),
                ("Unknown count:", "Field_UnknownMorphCount"),
                ("Unknown frequency:", "Field_UnknownFreq")
            ]
        self.fieldEntryList = []
        for i, (name, key) in enumerate(fieldsList):
            entry = QLineEdit(jcfg(key))
            self.fieldEntryList.append((key, entry))

            grid.addWidget(QLabel(name), i / numberOfColumns, (i % numberOfColumns) * 2 + 0)
            grid.addWidget(entry, i / numberOfColumns, (i % numberOfColumns) * 2 + 1)

        self.vbox.addWidget(self.frame2)

        self.frame3 = QGroupBox("Tags")
        vbox = QVBoxLayout(); self.frame3.setLayout(vbox); vbox.setContentsMargins(0, 20, 0, 50)

        label = QLabel("This plugin will add and delete following tags from your matched notes. Hover your mouse over text entries to see tooltip info.")
        label.setWordWrap(True)
        vbox.addWidget(label)

        grid = QGridLayout(); vbox.addLayout(grid)
        tagList  = [
                ("Compehension note:", 'Tag_Comprehension'),
                ("Vocab note:", 'Tag_Vocab'),
                ("Not ready:", 'Tag_NotReady'),
                ("Already known:", 'Tag_AlreadyKnown'),
                ("Priority:", 'Tag_Priority'),
                ("Bad Length:", 'Tag_BadLength'),
                ("Too Long", 'Tag_TooLong'),
            ]
        self.tagEntryList = []
        for i, (name, key) in enumerate(tagList):
            entry = QLineEdit(jcfg(key))
            self.tagEntryList.append((key, entry))

            grid.addWidget(QLabel(name), i / numberOfColumns, (i % numberOfColumns) * 2 + 0)
            grid.addWidget(entry, i / numberOfColumns, (i % numberOfColumns) * 2 + 1)
        self.vbox.addWidget(self.frame3)


        hbox = QHBoxLayout(); self.vbox.addLayout(hbox)
        buttonCancel = QPushButton("&Cancel"); hbox.addWidget(buttonCancel, 1, Qt.AlignRight)
        buttonCancel.setMaximumWidth(150)
        self.connect( buttonCancel, SIGNAL('clicked()'), self.onCancel )

        buttonOkay = QPushButton("&Apply"); hbox.addWidget(buttonOkay, 0)
        buttonOkay.setMaximumWidth(150)
        self.connect( buttonOkay, SIGNAL('clicked()'), self.onOkay )


        self.setLayout(self.vbox)


    # see util.jcfg_default()['Filter'] for type of data
    def setTableRow(self, rowIndex, data):
        rowGui = {}

        modelComboBox = QComboBox()
        active = 0
        modelComboBox.addItem("All note types")
        for i, model in enumerate(mw.col.models.allNames()):
            if model == data['Type']: active = i
            modelComboBox.addItem(model)
        modelComboBox.setCurrentIndex(active + 1)

        active = 1
        morphemizerComboBox = QComboBox()
        for i, m in enumerate(getAllMorphemizers()):
            if m.__class__.__name__ == data['Morphemizer']: active = i
            morphemizerComboBox.addItem(m.getDescription())
        morphemizerComboBox.setCurrentIndex(active)

        item = QStandardItem()
        item.setCheckable(True)
        item.setCheckState(Qt.Checked if data['Modify'] else Qt.Unchecked)

        rowGui['modelComboBox'] = modelComboBox
        rowGui['tagsEntry'] = QLineEdit(', '.join(data['Tags']))
        rowGui['fieldsEntry'] = QLineEdit(', '.join(data['Fields']))
        rowGui['morphemizerComboBox'] = morphemizerComboBox
        rowGui['modifyCheckBox'] = item
        self.tableView.setIndexWidget(self.tableModel.index(rowIndex, 0), rowGui['modelComboBox'])
        self.tableView.setIndexWidget(self.tableModel.index(rowIndex, 1), rowGui['tagsEntry'])
        self.tableView.setIndexWidget(self.tableModel.index(rowIndex, 2), rowGui['fieldsEntry'])
        self.tableView.setIndexWidget(self.tableModel.index(rowIndex, 3), morphemizerComboBox)
        self.tableModel.setItem(rowIndex, 4, item)

        self.rowGui[rowIndex] = rowGui


    def rowGuiToFilter(self, rowGui):
        filter = {}

        if rowGui['modelComboBox'].currentIndex() == 0: filter['Type'] = None # no filter "All note types"
        else: filter['Type'] = rowGui['modelComboBox'].currentText()

        filter['Tags'] = rowGui['tagsEntry'].text().replace(',', ' ').split()
        filter['Fields'] = rowGui['fieldsEntry'].text().replace(',', ' ').split()

        filter['Morphemizer'] = getAllMorphemizers()[rowGui['morphemizerComboBox'].currentIndex()].__class__.__name__
        filter['Modify'] = rowGui['modifyCheckBox'].checkState() != Qt.Unchecked

        return filter



    def readConfigFromGui(self):
        cfg = {}
        for (key, entry) in self.fieldEntryList:
            cfg[key] = entry.text()
        for (key, entry) in self.tagEntryList:
            cfg[key] = entry.text()

        cfg['Filter'] = []
        for i, rowGui in enumerate(self.rowGui):
            cfg['Filter'].append(self.rowGuiToFilter(rowGui))

        return cfg

    def onCancel(self):
        self.close()

    def onOkay(self):
        jcfgUpdate(self.readConfigFromGui())
        self.close()
        tooltip( _( 'Please recalculate your database to avoid unexpected behaviour.') )



def main():
    mw.mm = PreferencesDialog( mw )
    mw.mm.show()
