# -*- coding: utf-8 -*-
import os

from aqt.qt import *
from anki.utils import is_mac
from .UI import MorphemizerComboBox

from . import adaptiveSubs
from .morphemes import MorphDb
from .morphemizer import getAllMorphemizers
from .util import errorMsg, infoMsg, mw, mkBtn
from .preferences import get_preference as cfg


def getPath(le):  # LineEdit -> GUI ()
    path = QFileDialog.getOpenFileName(caption='Open db', directory=cfg('path_dbs'))[0]
    le.setText(path)


def getProgressWidget():
    progressWidget = QWidget()
    progressWidget.setFixedSize(400, 70)
    progressWidget.setWindowModality(Qt.ApplicationModal)
    bar = QProgressBar(progressWidget)
    if is_mac:
        bar.setFixedSize(380, 50)
    else:
        bar.setFixedSize(390, 50)
    bar.move(10, 10)
    per = QLabel(bar)
    per.setAlignment(Qt.AlignCenter)
    progressWidget.show()
    return progressWidget, bar


class AdaptiveSubWin(QDialog):
    def __init__(self, parent=None):
        super(AdaptiveSubWin, self).__init__(parent)
        self.setWindowTitle('Adaptive Subs')
        self.grid = grid = QGridLayout(self)
        self.vbox = vbox = QVBoxLayout()

        self.matureFmt = QLineEdit('%(target)s')
        self.knownFmt = QLineEdit('%(target)s [%(native)s]')
        self.unknownFmt = QLineEdit('%(native)s [%(N_k)s] [%(unknowns)s]')
        self.morphemizerComboBox = MorphemizerComboBox()
        self.morphemizerComboBox.setMorphemizers(morphemizers=getAllMorphemizers())

        self.vbox.addWidget(QLabel('Mature Format'))
        self.vbox.addWidget(self.matureFmt)
        self.vbox.addWidget(QLabel('Known Format'))
        self.vbox.addWidget(self.knownFmt)
        self.vbox.addWidget(QLabel('Unknown Format'))
        self.vbox.addWidget(self.unknownFmt)
        self.vbox.addWidget(QLabel('Morpheme Engine (Morphemizer)'))
        self.vbox.addWidget(self.morphemizerComboBox)

        self.goBtn = mkBtn('Convert subs', self.onGo, vbox)

        grid.addLayout(vbox, 0, 0)

    def onGo(self):
        mFmt = str(self.matureFmt.text())
        kFmt = str(self.knownFmt.text())
        uFmt = str(self.unknownFmt.text())
        morphemizer = self.morphemizerComboBox.getCurrent()

        inputPaths = QFileDialog.getOpenFileNames(caption='Dueling subs to process', filter='Subs (*.ass)')[0]
        if not inputPaths:
            return
        outputPath = QFileDialog.getExistingDirectory(caption='Save adaptive subs to')
        if not outputPath:
            return

        progWid, bar = getProgressWidget()
        bar.setMinimum(0)
        bar.setMaximum(len(inputPaths))
        val = 0
        for fileNumber, subtitlePath in enumerate(inputPaths, start=1):
            # MySubtitlesFolder/1 EpisodeSubtitles Episode 1.ass
            outputSubsFileName = outputPath + "/" + str(fileNumber) + " " + subtitlePath.split("/")[-1]
            adaptiveSubs.run(subtitlePath, outputSubsFileName, morphemizer, mFmt, kFmt, uFmt)

            val += 1
            bar.setValue(val)
            mw.app.processEvents()
        mw.progress.finish()
        mw.reset()
        infoMsg("Completed successfully")


class MorphMan(QDialog):
    def __init__(self, parent=None):
        super(MorphMan, self).__init__(parent)
        self.mw = parent
        self.setWindowTitle('Morph Man 3 Manager')
        self.grid = grid = QGridLayout(self)
        self.vbox = vbox = QVBoxLayout()

        # DB Paths
        self.aPathLEdit = QLineEdit()
        vbox.addWidget(self.aPathLEdit)
        self.aPathBtn = mkBtn('Browse for DB A', lambda le: getPath(self.aPathLEdit), vbox)

        self.bPathLEdit = QLineEdit()
        vbox.addWidget(self.bPathLEdit)
        self.bPathBtn = mkBtn('Browse for DB B', lambda le: getPath(self.bPathLEdit), vbox)

        # Comparisons
        self.showABtn = mkBtn('A', self.onShowA, vbox)
        self.AmBBtn = mkBtn('A-B', lambda x: self.onDiff('A-B'), vbox)
        self.BmABtn = mkBtn('B-A', lambda x: self.onDiff('B-A'), vbox)
        self.symBtn = mkBtn('Symmetric Difference', lambda x: self.onDiff('sym'), vbox)
        self.interBtn = mkBtn('Intersection', lambda x: self.onDiff('inter'), vbox)
        self.unionBtn = mkBtn('Union', lambda x: self.onDiff('union'), vbox)

        # Creation
        # language class/morphemizer
        self.db = None
        self.morphemizerComboBox = MorphemizerComboBox()
        self.morphemizerComboBox.setMorphemizers(getAllMorphemizers())

        vbox.addSpacing(40)
        vbox.addWidget(self.morphemizerComboBox)
        self.extractTxtFileBtn = mkBtn('Extract morphemes from file', self.onExtractTxtFile, vbox)
        self.saveResultsBtn = mkBtn('Save results to db', self.onSaveResults, vbox)

        # Display
        vbox.addSpacing(40)
        self.col_all_Mode = QRadioButton('All result columns')
        self.col_all_Mode.setChecked(True)
        self.col_one_Mode = QRadioButton('One result column')
        self.col_all_Mode.clicked.connect(self.colModeButtonListener)
        self.col_one_Mode.clicked.connect(self.colModeButtonListener)
        vbox.addWidget(self.col_all_Mode)
        vbox.addWidget(self.col_one_Mode)
        self.morphDisplay = QTextEdit()
        self.analysisDisplay = QTextEdit()

        # Exporting
        self.adaptiveSubs = mkBtn('Adaptive Subs', self.adaptiveSubsMethod, vbox)

        # layout
        grid.addLayout(vbox, 0, 0)
        grid.addWidget(self.morphDisplay, 0, 1)
        grid.addWidget(self.analysisDisplay, 0, 2)

    def adaptiveSubsMethod(self):
        self.hide()
        asw = AdaptiveSubWin(self.mw)
        asw.show()

    def loadA(self):
        self.aPath = self.aPathLEdit.text()
        self.aDb = MorphDb(path=self.aPath)
        if not self.db:
            self.db = self.aDb

    def loadB(self):
        self.bPath = self.bPathLEdit.text()
        self.bDb = MorphDb(path=self.bPath)

    def loadAB(self):
        self.loadA()
        self.loadB()

    def onShowA(self):
        try:
            self.loadA()
        except Exception as e:
            return errorMsg('Can\'t load db:\n%s' % e)
        self.db = self.aDb
        self.updateDisplay()

    def onDiff(self, kind):
        try:
            self.loadAB()
        except Exception as e:
            return errorMsg('Can\'t load dbs:\n%s' % e)

        a_set = set(self.aDb.db.keys())
        b_set = set(self.bDb.db.keys())
        if kind == 'sym':
            ms = a_set.symmetric_difference(b_set)
        elif kind == 'A-B':
            ms = a_set.difference(b_set)
        elif kind == 'B-A':
            ms = b_set.difference(a_set)
        elif kind == 'inter':
            ms = a_set.intersection(b_set)
        elif kind == 'union':
            ms = a_set.union(b_set)
        else:
            raise ValueError("'kind' must be one of [sym, A-B, B-A, inter, union], it was actually '%s'" % kind)

        self.db.clear()
        for m in ms:
            locs = set()
            if m in self.aDb.db:
                locs.update(self.aDb.db[m])
            if m in self.bDb.db:
                locs.update(self.bDb.db[m])
            self.db.addMLs1(m, locs)

        self.updateDisplay()

    def onExtractTxtFile(self):
        srcPath = QFileDialog.getOpenFileName(caption='Text file to extract from?', directory=cfg('path_dbs'))[0]
        if not srcPath:
            return

        destPath = QFileDialog.getSaveFileName(
                   caption='Save morpheme db to?', directory=cfg('path_dbs') + os.sep + 'textFile.db')[0]
        if not destPath:
            return

        mat = cfg('text file import maturity')
        db = MorphDb.mkFromFile(str(srcPath), self.morphemizerComboBox.getCurrent(), mat)
        if db:
            db.save(str(destPath))
            infoMsg('Extracted successfully')

    def onSaveResults(self):
        dir_path = cfg('path_dbs') + os.sep + 'results.db'
        destPath = QFileDialog.getSaveFileName(caption='Save results to?', directory=dir_path)[0]
        if not destPath:
            return
        if not hasattr(self, 'db'):
            return errorMsg('No results to save')
        self.db.save(str(destPath))
        infoMsg('Saved successfully')

    def colModeButtonListener(self):
        colModeButton = self.sender()
        if colModeButton.isChecked():
            try:
                self.updateDisplay()
            except AttributeError:
                return  # User has not selected a db view yet

    def updateDisplay(self):
        if self.col_all_Mode.isChecked():
            self.morphDisplay.setText(self.db.showMs())
        else:
            self.morphDisplay.setText('\n'.join(sorted(list(set([m.norm for m in self.db.db])))))
        self.analysisDisplay.setText(self.db.analyze2str())


def main():
    mw.mm = MorphMan(mw)
    mw.mm.show()
