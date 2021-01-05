from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from anki.lang import _

from aqt.utils import tooltip

from .util import mw, mkBtn
from .preferences import get_preference, update_preferences
from .morphemizer import getAllMorphemizers
from .UI import MorphemizerComboBox

# only for jedi-auto-completion
import aqt.main

assert isinstance(mw, aqt.main.AnkiQt)


class PreferencesDialog(QDialog):
    def __init__(self, parent=None):
        super(PreferencesDialog, self).__init__(parent)
        
        self.setModal(True)
        self.rowGui = []
        self.resize(950, 600)

        self.setWindowTitle('MorphMan Preferences')
        self.vbox = QVBoxLayout(self)
        self.tabWidget = QTabWidget()
        self.vbox.addWidget(self.tabWidget)

        self.createNoteFilterTab()
        self.createExtraFieldsTab()
        self.createTagsTab()
        self.createButtons()
        self.createGeneralTab()

        self.setLayout(self.vbox)

    def createNoteFilterTab(self):
        self.frame1 = QWidget()
        self.tabWidget.addTab(self.frame1, "Note Filter")
        vbox = QVBoxLayout()
        self.frame1.setLayout(vbox)
        vbox.setContentsMargins(0, 20, 0, 0)

        self.tableModel = QStandardItemModel(0, 6)
        self.tableView = QTableView()
        self.tableView.setModel(self.tableModel)
        self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableModel.setHeaderData(0, Qt.Horizontal, "Note type")
        self.tableModel.setHeaderData(1, Qt.Horizontal, "Tags")
        self.tableModel.setHeaderData(2, Qt.Horizontal, "Fields")
        self.tableModel.setHeaderData(3, Qt.Horizontal, "Morphemizer")
        self.tableModel.setHeaderData(4, Qt.Horizontal, "Read?")
        self.tableModel.setHeaderData(5, Qt.Horizontal, "Modify?")

        rowData = get_preference('Filter')
        self.tableModel.setRowCount(len(rowData))
        self.rowGui = []
        for i, row in enumerate(rowData):
            self.setTableRow(i, row)

        label = QLabel(
            "Any card that has the given `Note type` and all of the given `Tags` will have its `Fields` analyzed with the specified `Morphemizer`. " +
            "A morphemizer specifies how words are extraced from a sentence. `Fields` and `Tags` are both comma-separated lists (e.x: \"tag1, tag2, tag3\"). " +
            "If `Tags` is empty, there are no tag restrictions. " +
            "If `Modify` is deactivated, the note will only be analyzed.\n\nIf a note is matched multple times, only the first filter in this list will be used.")
        label.setWordWrap(True)
        vbox.addWidget(label)
        vbox.addSpacing(20)
        vbox.addWidget(self.tableView)

        hbox = QHBoxLayout()
        vbox.addLayout(hbox)

        self.clone = mkBtn("Clone", self.onClone, hbox)
        self.delete = mkBtn("Delete", self.onDelete, hbox)
        self.up = mkBtn("Up", self.onUp, hbox)
        self.down = mkBtn("Down", self.onDown, hbox)

    def createExtraFieldsTab(self):
        self.frame2 = QWidget()
        self.tabWidget.addTab(self.frame2, "Extra Fields")
        vbox = QVBoxLayout()
        self.frame2.setLayout(vbox)
        vbox.setContentsMargins(0, 20, 0, 0)

        label = QLabel(
            "This addon will attempt to change the data in the following fields. " +
            "Every field that has a (*) is REQUIRED IN EVERY NOTE for MorphMan to work correctly. " +
            "The other fields are optional. Hover your mouse over text entries to see tooltip info.")
        label.setWordWrap(True)
        vbox.addWidget(label)
        vbox.addSpacing(50)

        grid = QGridLayout()
        vbox.addLayout(grid)
        numberOfColumns = 2
        fieldsList = [
            ("Focus morph (*):", "Field_FocusMorph",
             "Stores the unknown morpheme for sentences with one unmature word.\nGets cleared as soon as all works are mature."),
            ("MorphMan Index:", "Field_MorphManIndex",
             "Difficulty of card. This will be set to `due` time of card."),
            ("Unmatures", "Field_Unmatures",
             "Comma-separated list of unmature words."),
            ("Unmatures count:", "Field_UnmatureMorphCount",
             "Number of unmature words on this note."),
            ("Unknowns:", "Field_Unknowns",
             "Comma-separated list of unknown morphemes."),
            ("Unknown count:", "Field_UnknownMorphCount",
             "Number of unknown morphemes on this note."),
            ("Unknown frequency:", "Field_UnknownFreq",
             "Average of how many times the unknowns appear in your collection."),
            ("Focus morph POS:", "Field_FocusMorphPos",
             "The part of speech of the focus morph")
        ]
        self.fieldEntryList = []
        for i, (name, key, tooltipInfo) in enumerate(fieldsList):
            entry = QLineEdit(get_preference(key))
            entry.setToolTip(tooltipInfo)
            self.fieldEntryList.append((key, entry))

            grid.addWidget(QLabel(name), i // numberOfColumns,
                           (i % numberOfColumns) * 2 + 0)
            grid.addWidget(entry, i // numberOfColumns,
                           (i % numberOfColumns) * 2 + 1)

        vbox.addStretch()

    def createTagsTab(self):
        self.frame3 = QGroupBox("Tags")
        self.tabWidget.addTab(self.frame3, "Tags")
        vbox = QVBoxLayout()
        self.frame3.setLayout(vbox)
        vbox.setContentsMargins(0, 20, 0, 0)

        label = QLabel(
            "This addon will add and delete following tags from your matched notes. Hover your mouse over text entries to see tooltip info.")
        label.setWordWrap(True)
        vbox.addWidget(label)
        vbox.addSpacing(50)

        grid = QGridLayout()
        vbox.addLayout(grid)
        tagList = [
            ("Vocab note:", 'Tag_Vocab',
             'Note that is optimal to learn (one unknown word.)'),
            ("Compehension note:", 'Tag_Comprehension',
             'Note that only has mature words (optimal for sentence learning).'),
            ("Fresh vocab note:", 'Tag_Fresh',
             'Note that does not contain unknown words, but one or\nmore unmature (card with recently learned morphmes).'),
            ("Not ready:", 'Tag_NotReady',
             'Note that has two or more unknown words.'),
            ("Already known:", 'Tag_AlreadyKnown',
             'You can add this tag to a note.\nAfter a recalc of the database, all in this sentence words are marked as known.\nPress \'K\' while reviewing to tag current card.'),
            ("Priority:", 'Tag_Priority', 'Morpheme is in priority.db.'),
            ("Too Short:", 'Tag_TooShort', 'Sentence is too short.'),
            ("Too Long:", 'Tag_TooLong', 'Sentence is too long.'),
            ("Frequency:", 'Tag_Frequency', 'Morpheme is in frequency.txt'),
        ]
        self.tagEntryList = []
        numberOfColumns = 2
        for i, (name, key, tooltipInfo) in enumerate(tagList):
            entry = QLineEdit(get_preference(key))
            entry.setToolTip(tooltipInfo)
            self.tagEntryList.append((key, entry))

            grid.addWidget(QLabel(name), i // numberOfColumns,
                           (i % numberOfColumns) * 2 + 0)
            grid.addWidget(entry, i // numberOfColumns,
                           (i % numberOfColumns) * 2 + 1)

        vbox.addSpacing(50)

        self.checkboxSetNotRequiredTags = QCheckBox(
            "Add tags even if not required")
        self.checkboxSetNotRequiredTags.setCheckState(
            Qt.Checked if get_preference('Option_SetNotRequiredTags') else Qt.Unchecked)
        vbox.addWidget(self.checkboxSetNotRequiredTags)

        vbox.addStretch()

    def createGeneralTab(self):
        self.frame4 = QGroupBox()
        self.tabWidget.addTab(self.frame4, "General")
        vbox = QVBoxLayout()
        self.frame4.setLayout(vbox)
        vbox.setContentsMargins(10, 10, 10, 10)

        hbox = QHBoxLayout()
        vbox.addLayout(hbox)

        reviews_group = QGroupBox("Review Preferences")
        hbox.addWidget(reviews_group)
        reviews_grid = QVBoxLayout()
        reviews_group.setLayout(reviews_grid)

        parsing_group = QGroupBox("Parsing Preferences")
        hbox.addWidget(parsing_group)
        parsing_grid = QVBoxLayout()
        parsing_group.setLayout(parsing_grid)

        label = QLabel("MorphMan will reorder the cards so that the easiest cards are at the front. To avoid getting "
                "new cards that are too easy, MorphMan will skip certain new cards. You can customize the skip "
                "behavior here:")
        label.setWordWrap(True)
        reviews_grid.addWidget(label)

        optionList = [
            (reviews_grid, "Skip comprehension cards", 'Option_SkipComprehensionCards',
             'Note that only has mature words (optimal for sentence learning but not for acquiring new vocabulary).'),
            (reviews_grid, "Skip cards with fresh vocabulary", 'Option_SkipFreshVocabCards',
             "Note that does not contain unknown words, but one or more unmature (card with recently learned morphmes).\n"
             "Enable to skip to first card that has unknown vocabulary."),
            (reviews_grid, "Skip card if focus morph was already seen today", 'Option_SkipFocusMorphSeenToday',
             "This improves the 'new cards'-queue without having to recalculate the databases."),
            (parsing_grid, "Treat proper nouns as known", 'Option_ProperNounsAlreadyKnown',
             'Treat proper nouns as already known when scoring cards (currently only works for Japanese).'),
            (parsing_grid, "Ignore grammar position", 'Option_IgnoreGrammarPosition',
             'Use this option to ignore morpheme grammar types (noun, verb, helper, etc.).'),
            (parsing_grid, 'Ignore suspended leeches', 'Option_IgnoreSuspendedLeeches',
             'Ignore cards that are suspended and have the tag \'leech\'.'),
            (parsing_grid, "Ignore everything contained within [ ] brackets", 'Option_IgnoreBracketContents',
             'Use this option to ignore content such as furigana readings and pitch.'),
            (parsing_grid, "Ignore everything contained within ( ) brackets", 'Option_IgnoreSlimRoundBracketContents',
             'Use this option to ignore content such as character names and readings in scripts.'),
            (parsing_grid, "Ignore everything contained within Japanese wide （ ） brackets", 'Option_IgnoreRoundBracketContents',
             'Use this option to ignore content such as character names and readings in Japanese scripts.'),
        ]

        self.boolOptionList = []
        for i, (layout, name, key, tooltipInfo) in enumerate(optionList):
            checkBox = QCheckBox(name)
            checkBox.setCheckState(Qt.Checked if get_preference(key) else Qt.Unchecked)
            checkBox.setToolTip(tooltipInfo)
            checkBox.setMinimumSize(0, 30)
            self.boolOptionList.append((key, checkBox))
            layout.addWidget(checkBox)

        reviews_grid.addStretch()
        parsing_grid.addStretch()
        vbox.addStretch()

    def createButtons(self):
        hbox = QHBoxLayout()
        self.vbox.addLayout(hbox)
        buttonCancel = QPushButton("&Cancel")
        hbox.addWidget(buttonCancel, 1, Qt.AlignRight)
        buttonCancel.setMaximumWidth(150)
        buttonCancel.clicked.connect(self.onCancel)

        buttonOkay = QPushButton("&Apply")
        hbox.addWidget(buttonOkay)
        buttonOkay.setMaximumWidth(150)
        buttonOkay.clicked.connect(self.onOkay)

    # see preferences.jcfg_default()['Filter'] for type of data
    def setTableRow(self, rowIndex, data):
        assert rowIndex >= 0, "Negative row numbers? Really?"
        assert len(
            self.rowGui) >= rowIndex, "Row can't be appended because it would leave an empty row"

        rowGui = {}

        modelComboBox = QComboBox()
        active = 0
        modelComboBox.addItem("All note types")
        for i, model in enumerate(mw.col.models.allNames()):
            if model == data['Type']:
                active = i + 1
            modelComboBox.addItem(model)
        modelComboBox.setCurrentIndex(active)

        morphemizerComboBox = MorphemizerComboBox()
        morphemizerComboBox.setMorphemizers(getAllMorphemizers())
        morphemizerComboBox.setCurrentByName(data['Morphemizer'])

        readItem = QStandardItem()
        readItem.setCheckable(True)
        readItem.setCheckState(Qt.Checked if data.get('Read', True) else Qt.Unchecked)

        modifyItem = QStandardItem()
        modifyItem.setCheckable(True)
        modifyItem.setCheckState(Qt.Checked if data.get('Modify', True) else Qt.Unchecked)

        rowGui['modelComboBox'] = modelComboBox
        rowGui['tagsEntry'] = QLineEdit(', '.join(data['Tags']))
        rowGui['fieldsEntry'] = QLineEdit(', '.join(data['Fields']))
        rowGui['morphemizerComboBox'] = morphemizerComboBox
        rowGui['readCheckBox'] = readItem
        rowGui['modifyCheckBox'] = modifyItem

        def setColumn(col, widget):
            self.tableView.setIndexWidget(self.tableModel.index(rowIndex, col), widget)

        setColumn(0, rowGui['modelComboBox'])
        setColumn(1, rowGui['tagsEntry'])
        setColumn(2, rowGui['fieldsEntry'])
        setColumn(3, rowGui['morphemizerComboBox'])
        self.tableModel.setItem(rowIndex, 4, readItem)
        self.tableModel.setItem(rowIndex, 5, modifyItem)

        if len(self.rowGui) == rowIndex:
            self.rowGui.append(rowGui)
        else:
            self.rowGui[rowIndex] = rowGui

    def rowIndexToFilter(self, rowIdx):
        return self.rowGuiToFilter(self.rowGui[rowIdx])

    @staticmethod
    def rowGuiToFilter(row_gui):
        filter = {}

        if row_gui['modelComboBox'].currentIndex() == 0:
            filter['Type'] = None  # no filter "All note types"
        else:
            filter['Type'] = row_gui['modelComboBox'].currentText()

        filter['Tags'] = [x for x in row_gui['tagsEntry'].text().split(', ') if x]
        filter['Fields'] = [
            x for x in row_gui['fieldsEntry'].text().split(', ') if x]

        filter['Morphemizer'] = row_gui['morphemizerComboBox'].getCurrent().getName()
        filter['Read'] = row_gui['readCheckBox'].checkState() != Qt.Unchecked
        filter['Modify'] = row_gui['modifyCheckBox'].checkState() != Qt.Unchecked

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

        cfg['Option_SetNotRequiredTags'] = self.checkboxSetNotRequiredTags.checkState(
        ) != Qt.Unchecked

        return cfg

    def onCancel(self):
        self.close()

    def onOkay(self):
        update_preferences(self.readConfigFromGui())
        self.close()
        tooltip(_('Please recalculate your database to avoid unexpected behaviour.'))

    def getCurrentRow(self):
        indexes = self.tableView.selectedIndexes()
        return 0 if len(indexes) == 0 else indexes[0].row()

    def appendRowData(self, data):
        self.tableModel.setRowCount(len(self.rowGui) + 1)
        self.setTableRow(len(self.rowGui), data)

    def onClone(self):
        row = self.getCurrentRow()
        data = self.rowIndexToFilter(row)
        self.appendRowData(data)

    def onDelete(self):
        # do not allow to delete the last row
        if len(self.rowGui) == 1:
            return
        row_to_delete = self.getCurrentRow()
        self.tableModel.removeRow(row_to_delete)
        self.rowGui.pop(row_to_delete)

    def moveRowUp(self, row):
        # type: (int) -> None
        if not 0 < row < len(self.rowGui):  #
            return

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
    mw.mm = PreferencesDialog(mw)
    mw.mm.show()
