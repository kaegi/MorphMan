from PyQt4.QtCore import *
from PyQt4.QtGui import *

from aqt.utils import tooltip

from util import errorMsg, infoMsg, mw, jcfg, jcfgUpdate, mkBtn
from morphemizer import getAllMorphemizers

# only for jedi-auto-completion
import aqt.main
assert isinstance(mw, aqt.main.AnkiQt)

class PreferencesDialog( QDialog ):
    def __init__( self, parent=None ):
        super( PreferencesDialog, self ).__init__( parent )
        self.rowGui = []
        self.resize(950, 600)

        self.setWindowTitle( 'MorphMan Preferences' )
        self.vbox = vbox = QVBoxLayout(self)
        self.tabWidget = QTabWidget(); self.vbox.addWidget(self.tabWidget)

        self.createNoteFilterTab()
        self.createExtraFieldsTab()
        self.createTagsTab()
        self.createButtons()
        self.createGeneralTab()

        self.setLayout(self.vbox)

    def createNoteFilterTab(self):
        self.frame1 = QWidget()
        self.tabWidget.addTab(self.frame1, "Note Filter")
        vbox = QVBoxLayout(); self.frame1.setLayout(vbox); vbox.setContentsMargins(0, 20, 0, 0)

        self.tableModel = QStandardItemModel(0, 5)
        self.tableView = QTableView()
        self.tableView.setModel(self.tableModel)
        self.tableView.horizontalHeader().setResizeMode(QHeaderView.Stretch)
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableModel.setHeaderData(0, Qt.Horizontal, "Note type")
        self.tableModel.setHeaderData(1, Qt.Horizontal, "Tags")
        self.tableModel.setHeaderData(2, Qt.Horizontal, "Fields")
        self.tableModel.setHeaderData(3, Qt.Horizontal, "Morphemizer")
        self.tableModel.setHeaderData(4, Qt.Horizontal, "Modify?")

        rowData = jcfg('Filter')
        self.tableModel.setRowCount(len(rowData))
        self.rowGui = []
        for i, row in enumerate(rowData):
            self.setTableRow(i, row)

        label = QLabel("Any card that has the given `Note type` and all of the given `Tags` will have its `Fields` analyzed with the specified `Morphemizer`. A morphemizer specifies how words are extraced from a sentence. `Fields` and `Tags` are both comma-separated lists. If `Tags` is empty, there are no tag restrictions. If `Modify` is deactivated, the note will only be analyzed.\n\nIf a note is matched multple times, only the first filter in this list will be used.")
        label.setWordWrap(True)
        vbox.addWidget(label)
        vbox.addSpacing(20)
        vbox.addWidget(self.tableView)

        hbox = QHBoxLayout(); vbox.addLayout(hbox)

        self.clone = mkBtn("Clone", self.onClone, self, hbox)
        self.delete = mkBtn("Delete", self.onDelete, self, hbox)
        self.up = mkBtn("Up", self.onUp, self, hbox)
        self.down = mkBtn("Down", self.onDown, self, hbox)

    def createExtraFieldsTab(self):
        self.frame2 = QWidget()
        self.tabWidget.addTab(self.frame2, "Extra Fields")
        vbox = QVBoxLayout(); self.frame2.setLayout(vbox); vbox.setContentsMargins(0, 20, 0, 0)

        label = QLabel("This plugin will attempt to change the data in following fields. Every field that has a (*) is REQUIRED IN EVERY NOTE for MorphMan to work correctly. The other fields are optional. Hover your mouse over text entries to see tooltip info.")
        label.setWordWrap(True)
        vbox.addWidget(label)
        vbox.addSpacing(50)

        grid = QGridLayout(); vbox.addLayout(grid)
        numberOfColumns = 2
        fieldsList = [
                ("Focus morph (*):", "Field_FocusMorph", "Stores the unknown morpheme for sentences with one unmature word.\nGets cleared as soon as all works are mature."),
                ("MorphMan Index:", "Field_MorphManIndex", "Difficulty of card. This will be set to `due` time of card."),
                ("Unmatures", "Field_Unmatures", "Comma-separated list of unmature words."),
                ("Unmatures count:", "Field_UnmatureMorphCount", "Number of unmature words on this note."),
                ("Unknowns:", "Field_Unknowns", "Comma-separated list of unknown morphemes."),
                ("Unknown count:", "Field_UnknownMorphCount", "Number of unknown morphemes on this note."),
                ("Unknown frequency:", "Field_UnknownFreq", "Average of how many times the unknowns appear in your collection.")
            ]
        self.fieldEntryList = []
        for i, (name, key, tooltipInfo) in enumerate(fieldsList):
            entry = QLineEdit(jcfg(key))
            entry.setToolTip(tooltipInfo)
            self.fieldEntryList.append((key, entry))

            grid.addWidget(QLabel(name), i // numberOfColumns, (i % numberOfColumns) * 2 + 0)
            grid.addWidget(entry, i // numberOfColumns, (i % numberOfColumns) * 2 + 1)

        vbox.addStretch()


    def createTagsTab(self):
        self.frame3 = QGroupBox("Tags")
        self.tabWidget.addTab(self.frame3, "Tags")
        vbox = QVBoxLayout(); self.frame3.setLayout(vbox); vbox.setContentsMargins(0, 20, 0, 0)

        label = QLabel("This plugin will add and delete following tags from your matched notes. Hover your mouse over text entries to see tooltip info.")
        label.setWordWrap(True)
        vbox.addWidget(label)
        vbox.addSpacing(50)

        grid = QGridLayout(); vbox.addLayout(grid)
        tagList  = [
                ("Vocab note:", 'Tag_Vocab', 'Note that is optimal to learn (one unknown word.)'),
                ("Compehension note:", 'Tag_Comprehension', 'Note that only has mature words (optimal for sentence learning).'),
                ("Fresh vocab note:", 'Tag_Fresh', 'Note that does not contain unknown words, but one or\nmore unmature (card with recently learned morphmes).'),
                ("Not ready:", 'Tag_NotReady', 'Note that has two or more unknown words.'),
                ("Already known:", 'Tag_AlreadyKnown', 'You can add this tag to a note.\nAfter a recalc of the database, all in this sentence words are marked as known.\nPress \'K\' while reviewing to tag current card.'),
                ("Priority:", 'Tag_Priority', 'Morpheme is in priority.db.'),
                ("Too Short:", 'Tag_TooShort', 'Sentence is too short.'),
                ("Too Long:", 'Tag_TooLong', 'Sentence is too long.'),
            ]
        self.tagEntryList = []
        numberOfColumns = 2
        for i, (name, key, tooltipInfo) in enumerate(tagList):
            entry = QLineEdit(jcfg(key))
            entry.setToolTip(tooltipInfo)
            self.tagEntryList.append((key, entry))

            grid.addWidget(QLabel(name), i // numberOfColumns, (i % numberOfColumns) * 2 + 0)
            grid.addWidget(entry, i // numberOfColumns, (i % numberOfColumns) * 2 + 1)

        vbox.addSpacing(50)

        self.checkboxSetNotRequiredTags = QCheckBox("Add tags even if not required")
        self.checkboxSetNotRequiredTags.setCheckState(Qt.Checked if jcfg('Option_SetNotRequiredTags') else Qt.Unchecked)
        vbox.addWidget(self.checkboxSetNotRequiredTags)

        vbox.addStretch()

    def createGeneralTab(self):
        self.frame4 = QGroupBox("General")
        self.tabWidget.addTab(self.frame4, "General")
        vbox = QVBoxLayout(); self.frame4.setLayout(vbox); vbox.setContentsMargins(0, 20, 0, 0)

        label = QLabel("MorphMan will reorder the cards so that the easiest cards are at the front. To avoid getting new cards that are too easy, MorphMan will skip certain new cards. You can customize the skip behavior here:")
        label.setWordWrap(True)
        vbox.addWidget(label)
        vbox.addSpacing(20)

        grid = QVBoxLayout(); vbox.addLayout(grid); grid.setContentsMargins(20, 0, 0, 0)
        optionList  = [
                ("Skip comprehension cards", 'Option_SkipComprehensionCards', 'Note that only has mature words (optimal for sentence learning but not for acquiring new vocabulary).'),
                ("Skip cards with fresh vocabulary", 'Option_SkipFreshVocabCards', 'Note that does not contain unknown words, but one or\nmore unmature (card with recently learned morphmes). Enable to\nskip to first card that has unknown vocabulary.'),
                ("Skip card if focus morph was already seen today", 'Option_SkipFocusMorphSeenToday', 'This improves the \'new cards\'-queue without having to recalculate the databases.'),
            ]
        self.boolOptionList = []
        for i, (name, key, tooltipInfo) in enumerate(optionList):
            checkBox = QCheckBox(name)
            checkBox.setCheckState(Qt.Checked if jcfg(key) else Qt.Unchecked)
            checkBox.setToolTip(tooltipInfo)
            self.boolOptionList.append((key, checkBox))

            grid.addWidget(checkBox)
            grid.addSpacing(15)

        vbox.addStretch()

    def createButtons(self):
        hbox = QHBoxLayout(); self.vbox.addLayout(hbox)
        buttonCancel = QPushButton("&Cancel"); hbox.addWidget(buttonCancel, 1, Qt.AlignRight)
        buttonCancel.setMaximumWidth(150)
        self.connect( buttonCancel, SIGNAL('clicked()'), self.onCancel )

        buttonOkay = QPushButton("&Apply"); hbox.addWidget(buttonOkay, 0)
        buttonOkay.setMaximumWidth(150)
        self.connect( buttonOkay, SIGNAL('clicked()'), self.onOkay )



    # see util.jcfg_default()['Filter'] for type of data
    def setTableRow(self, rowIndex, data):
        assert rowIndex >= 0, "Negative row numbers? Really?"
        assert len(self.rowGui) >= rowIndex, "Row can't be appended because it would leave an empty row"

        rowGui = {}

        modelComboBox = QComboBox()
        active = 0
        modelComboBox.addItem("All note types")
        for i, model in enumerate(mw.col.models.allNames()):
            if model == data['Type']: active = i + 1
            modelComboBox.addItem(model)
        modelComboBox.setCurrentIndex(active)

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

        if len(self.rowGui) == rowIndex:
            self.rowGui.append(rowGui)
        else:
            self.rowGui[rowIndex] = rowGui


    def rowIndexToFilter(self, rowIdx):
        return self.rowGuiToFilter(self.rowGui[rowIdx])

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
        for (key, checkBox) in self.boolOptionList:
            cfg[key] = (checkBox.checkState() == Qt.Checked)

        cfg['Filter'] = []
        for i, rowGui in enumerate(self.rowGui):
            cfg['Filter'].append(self.rowGuiToFilter(rowGui))

        cfg['Option_SetNotRequiredTags'] = self.checkboxSetNotRequiredTags.checkState() != Qt.Unchecked

        return cfg

    def onCancel(self):
        self.close()

    def onOkay(self):
        jcfgUpdate(self.readConfigFromGui())
        self.close()
        tooltip( _( 'Please recalculate your database to avoid unexpected behaviour.') )

    def getCurrentRow(self):
        indexes = self.tableView.selectedIndexes()
        if len(indexes) == 0: return 0
        return indexes[0].row()

    def appendRowData(self, data):
        self.tableModel.setRowCount(len(self.rowGui) + 1)
        self.setTableRow(len(self.rowGui), data)

    def onClone(self):
        row = self.getCurrentRow()
        data = self.rowIndexToFilter(row)
        self.appendRowData(data)

    def onDelete(self):
        # do not allow to delet last row
        if len(self.rowGui) == 1:
            return
        rowToDelete = self.getCurrentRow()
        self.tableModel.removeRow(rowToDelete)
        self.rowGui.pop(rowToDelete)

    def moveRowUp(self, row):
        if not (row > 0 and row < len(self.rowGui)): return # can't move first row up
        data1 = self.rowIndexToFilter(row - 1)
        data2 = self.rowIndexToFilter(row - 0)
        self.setTableRow(row - 1, data2)
        self.setTableRow(row - 0, data1)

    def onUp(self):
        row = self.getCurrentRow()
        self.moveRowUp(row)
        self.tableView.selectRow(row - 1)

    def onDown(self):
        # moving a row down means moving the next row up
        row = self.getCurrentRow()
        self.moveRowUp(row + 1)
        self.tableView.selectRow(row + 1)

def main():
    mw.mm = PreferencesDialog( mw )
    mw.mm.show()
