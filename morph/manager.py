# -*- coding: utf-8 -*-
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import os
import sys

from anki.utils import isMac

from . import adaptiveSubs
from .morphemes import MorphDb
from .morphemizer import getAllMorphemizers
from .util import dbsPath, errorMsg, infoMsg, mw, cfg1, mkBtn

def getPath( le ): # LineEdit -> GUI ()
    path = QFileDialog.getOpenFileName( caption='Open db', directory=dbsPath )[0]
    le.setText( path )

def getProgressWidget():
    progressWidget = QWidget(None)
    layout = QVBoxLayout()
    progressWidget.setFixedSize(400, 70)
    progressWidget.setWindowModality(Qt.ApplicationModal)
    bar = QProgressBar(progressWidget)
    if isMac:
        bar.setFixedSize(380, 50)
    else:
        bar.setFixedSize(390, 50)
    bar.move(10,10)
    per = QLabel(bar)
    per.setAlignment(Qt.AlignCenter)
    progressWidget.show()
    return progressWidget, bar;

class AdaptiveSubWin( QDialog ):
    def __init__( self, parent=None ):
        super( AdaptiveSubWin, self ).__init__( parent )
        self.setWindowTitle( 'Adaptive Subs' )
        self.grid = grid = QGridLayout( self )
        self.vbox = vbox = QVBoxLayout()

        self.matureFmt  = QLineEdit( '%(target)s' )
        self.knownFmt   = QLineEdit( '%(target)s [%(native)s]' )
        self.unknownFmt = QLineEdit( '%(native)s [%(N_k)s] [%(unknowns)s]' )
        self.morphemizer = QComboBox()

        for morphemizer in getAllMorphemizers():
            self.morphemizer.addItem(morphemizer.getDescription())

        self.vbox.addWidget( QLabel( 'Mature Format' ) )
        self.vbox.addWidget( self.matureFmt )
        self.vbox.addWidget( QLabel( 'Known Format' ) )
        self.vbox.addWidget( self.knownFmt )
        self.vbox.addWidget( QLabel( 'Unknown Format' ) )
        self.vbox.addWidget( self.unknownFmt )
        self.vbox.addWidget( QLabel( 'Morpheme Engine (Morphemizer)' ) )
        self.vbox.addWidget( self.morphemizer )

        self.goBtn = mkBtn( 'Convert subs', self.onGo, self, vbox )

        grid.addLayout( vbox, 0, 0 )

    def onGo( self ):
        mFmt = str( self.matureFmt.text() )
        kFmt = str( self.knownFmt.text() )
        uFmt = str( self.unknownFmt.text() )
        morphemizer = getAllMorphemizers()[self.morphemizer.currentIndex()]

        inputPaths = QFileDialog.getOpenFileNames( None, 'Dueling subs to process', '', 'Subs (*.ass)' )[0]
        if not inputPaths: return
        outputPath = QFileDialog.getExistingDirectory( None, 'Save adaptive subs to')
        if not outputPath: return

        progWid, bar = getProgressWidget()   
        bar.setMinimum(0)
        bar.setMaximum(len(inputPaths))
        val = 0;  
        for fileNumber, subtitlePath in enumerate(inputPaths, start=1):         
            # MySubtitlesFolder/1 EpisodeSubtitles Episode 1.ass
            outputSubsFileName = outputPath + "/" + str(fileNumber) + " " + subtitlePath.split("/")[-1]
            adaptiveSubs.run( subtitlePath, outputSubsFileName, morphemizer, mFmt, kFmt, uFmt )

            val+=1;
            bar.setValue(val)
            mw.app.processEvents()
        mw.progress.finish()
        mw.reset()   
        infoMsg( "Completed successfully" )

class MorphMan( QDialog ):
    def __init__( self, parent=None ):
        super( MorphMan, self ).__init__( parent )
        self.mw = parent
        self.setWindowTitle( 'Morph Man 3 Manager' )
        self.grid = grid = QGridLayout( self )
        self.vbox = vbox = QVBoxLayout()

        # DB Paths
        self.aPathLEdit = QLineEdit()
        vbox.addWidget( self.aPathLEdit )
        self.aPathBtn = mkBtn( 'Browse for DB A', lambda le: getPath( self.aPathLEdit ), self, vbox )

        self.bPathLEdit = QLineEdit()
        vbox.addWidget( self.bPathLEdit )
        self.bPathBtn = mkBtn( 'Browse for DB B', lambda le: getPath( self.bPathLEdit ), self, vbox )

        # Comparisons
        self.showABtn = mkBtn( 'A', self.onShowA, self, vbox )
        self.AmBBtn = mkBtn( 'A-B', lambda x: self.onDiff('A-B'), self, vbox )
        self.BmABtn = mkBtn( 'B-A', lambda x: self.onDiff('B-A'), self, vbox )
        self.symBtn = mkBtn( 'Symmetric Difference', lambda x: self.onDiff('sym'), self, vbox )
        self.interBtn = mkBtn( 'Intersection', lambda x: self.onDiff('inter'), self, vbox )
        self.unionBtn = mkBtn( 'Union', lambda x: self.onDiff('union'), self, vbox )

        # Creation
        ## language class/morphemizer
        self.db = None
        self.morphemizerComboBox = QComboBox()
        for morphemizer in getAllMorphemizers():
            self.morphemizerComboBox.addItem(morphemizer.getDescription())

        vbox.addSpacing(40)
        vbox.addWidget(self.morphemizerComboBox)
        self.extractTxtFileBtn = mkBtn( 'Extract morphemes from file', self.onExtractTxtFile, self, vbox )
        self.saveResultsBtn = mkBtn( 'Save results to db', self.onSaveResults, self, vbox )


        # Display
        vbox.addSpacing(40)
        self.col4Mode = QRadioButton( 'Results as 4col morpheme' )
        self.col4Mode.setChecked( True )
        self.col1Mode = QRadioButton( 'Results as 1col morpheme' )
        self.col4Mode.clicked.connect(self.colModeButtonListener)
        self.col1Mode.clicked.connect(self.colModeButtonListener)
        vbox.addWidget( self.col4Mode )
        vbox.addWidget( self.col1Mode )
        self.morphDisplay = QTextEdit()
        self.analysisDisplay = QTextEdit()

        # Exporting
        self.adaptiveSubs = mkBtn( 'Adaptive Subs', self.adaptiveSubs, self, vbox )

        # layout
        grid.addLayout( vbox, 0, 0 )
        grid.addWidget( self.morphDisplay, 0, 1 )
        grid.addWidget( self.analysisDisplay, 0, 2 )

    def adaptiveSubs( self ):
        self.hide()
        asw = AdaptiveSubWin( self.mw )
        asw.show()

    def loadA( self ):
        self.aPath = self.aPathLEdit.text()
        self.aDb = MorphDb( path=self.aPath )
        if not self.db:
            self.db = self.aDb
    def loadB( self ):
        self.bPath = self.bPathLEdit.text()
        self.bDb = MorphDb( path=self.bPath )
    def loadAB( self ):
        self.loadA()
        self.loadB()

    def onShowA( self ):
        try: self.loadA()
        except Exception as e: return errorMsg( 'Can\'t load db:\n%s' % e )
        self.db = self.aDb
        self.updateDisplay()

    def onDiff( self, type='sym' ):
        try: self.loadAB()
        except Exception as e: return errorMsg( 'Can\'t load dbs:\n%s' % e )

        aSet = set( self.aDb.db.keys() )
        bSet = set( self.bDb.db.keys() )
        if type == 'sym':       ms = aSet.symmetric_difference( bSet )
        elif type == 'A-B':     ms = aSet.difference( bSet )
        elif type == 'B-A':     ms = bSet.difference( aSet )
        elif type == 'inter':   ms = aSet.intersection( bSet )
        elif type == 'union':   ms = aSet.union( bSet )

        self.db.db = {}
        for m in ms:
            locs = set()
            if m in self.aDb.db: locs.update( self.aDb.db[m] )
            if m in self.bDb.db: locs.update( self.bDb.db[m] )
            self.db.addMLs1( m, locs )

        self.updateDisplay()

    def onExtractTxtFile( self ):
        srcPath = QFileDialog.getOpenFileName( caption='Text file to extract from?', directory=dbsPath )[0]
        if not srcPath: return
        destPath = QFileDialog.getSaveFileName( caption='Save morpheme db to?', directory=dbsPath + os.sep + 'textFile.db' )[0]
        if not destPath: return
        mat = cfg1('text file import maturity')
        db = MorphDb.mkFromFile( str(srcPath), getAllMorphemizers()[self.morphemizerComboBox.currentIndex()], mat )
        if db:
            db.save( str(destPath) )
            infoMsg( 'Extracted successfully' )

    def onSaveResults( self ):
        destPath = QFileDialog.getSaveFileName( caption='Save results to?', directory=dbsPath + os.sep + 'results.db' )[0]
        if not destPath: return
        if not hasattr( self, 'db' ): return errorMsg( 'No results to save' )
        self.db.save( str(destPath) )
        infoMsg( 'Saved successfully' )

    def colModeButtonListener( self ):
        colModeButton = self.sender()
        if colModeButton.isChecked():
            try:
                self.updateDisplay()
            except AttributeError:
                return # User has not selected a db view yet

    def updateDisplay( self ):
        if self.col4Mode.isChecked():
            self.morphDisplay.setText( self.db.showMs() )
        else:
            self.morphDisplay.setText( '\n'.join( [ m.base for m in self.db.db ] ) )
        self.analysisDisplay.setText( self.db.analyze2str() )

def main():
    mw.mm = MorphMan( mw )
    mw.mm.show()
