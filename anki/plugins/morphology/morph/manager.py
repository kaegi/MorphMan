# -*- coding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from anki.hooks import addHook
from ankiqt import mw
import os

import morphemes as M
import util
from util import errorMsg, infoMsg

def getPath( le ):
    path = QFileDialog.getOpenFileName( caption='Open db', directory=util.knownDbPath )
    le.setText( path )

def mkBtn( txt, f, conn, parent ):
    b = QPushButton( txt )
    conn.connect( b, SIGNAL('clicked()'), f )
    parent.addWidget( b )
    return b

class MorphMan( QDialog ):
    def __init__( self, parent=None ):
        super( MorphMan, self ).__init__( parent )
        self.setWindowTitle( 'Morph Man Title' )
        grid = QGridLayout( self )
        vbox = QVBoxLayout()

        # DB Paths
        self.aPathLEdit = QLineEdit()
        vbox.addWidget( self.aPathLEdit )
        self.aPathBtn = mkBtn( 'Browse for DB A', lambda le=self.aPathLEdit: getPath( le ), self, vbox )

        self.bPathLEdit = QLineEdit()
        vbox.addWidget( self.bPathLEdit )
        self.bPathBtn = mkBtn( 'Browse for DB B', lambda le=self.bPathLEdit: getPath( le ), self, vbox )

        # Comparisons
        self.showABtn = mkBtn( 'A', self.onShowA, self, vbox )
        self.AmBBtn = mkBtn( 'A-B', lambda x='A-B': self.onDiff(x), self, vbox )
        self.BmABtn = mkBtn( 'B-A', lambda x='B-A': self.onDiff(x), self, vbox )
        self.symBtn = mkBtn( 'Symmetric Difference', lambda x='sym': self.onDiff(x), self, vbox )
        self.interBtn = mkBtn( 'Intersection', lambda x='inter': self.onDiff(x), self, vbox )
        self.unionBtn = mkBtn( 'Union', lambda x='union': self.onDiff(x), self, vbox )

        # Creation
        self.extractTxtFileBtn = mkBtn( 'Extract morphemes from file', self.onExtractTxtFile, self, vbox )
        self.saveResultsBtn = mkBtn( 'Save results to db', self.onSaveResults, self, vbox )

        # Display
        self.col4Mode = QRadioButton( 'Results as 4col morpheme' )
        self.col4Mode.setChecked( True )
        self.col1Mode = QRadioButton( 'Results as 1col morpheme' )
        self.blacklist = QLineEdit( u'記号,助詞' )
        vbox.addWidget( self.col4Mode )
        vbox.addWidget( self.col1Mode )
        vbox.addWidget( self.blacklist )
        self.morphDisplay = QTextEdit()
        self.analysisDisplay = QTextEdit()

        # layout
        grid.addLayout( vbox, 0, 0 )
        grid.addWidget( self.morphDisplay, 0, 1 )
        grid.addWidget( self.analysisDisplay, 0, 2 )

    def loadA( self ):
        self.aPath = self.aPathLEdit.text()
        self.aDb = M.MorphDb( path=self.aPath )
    def loadB( self ):
        self.bPath = self.bPathLEdit.text()
        self.bDb = M.MorphDb( path=self.bPath )
    def loadAB( self ):
        self.loadA()
        self.loadB()

    def onShowA( self ):
        try: self.loadA()
        except: return errorMsg( 'Can\'t load db' )
        self.db = self.aDb
        self.updateDisplay()

    def onDiff( self, type='sym' ):
        try: self.loadAB()
        except: return errorMsg( 'Can\'t load dbs' )

        aSet = set( self.aDb.db.keys() )
        bSet = set( self.bDb.db.keys() )
        if type == 'sym':       ms = aSet.symmetric_difference( bSet )
        elif type == 'A-B':     ms = aSet.difference( bSet )
        elif type == 'B-A':     ms = bSet.difference( aSet )
        elif type == 'inter':   ms = aSet.intersection( bSet )
        elif type == 'union':   ms = aSet.union( bSet )
        print type,len(ms)

        self.db.db = {}
        for m in ms:
            locs = set()
            if m in self.aDb.db: locs.update( self.aDb.db[m] )
            if m in self.bDb.db: locs.update( self.bDb.db[m] )
            self.db.addMLs1( m, locs )

        self.updateDisplay()

    def onExtractTxtFile( self ):
        srcPath = QFileDialog.getOpenFileName( caption='Text file to extract from?', directory=util.dbPath )
        if not srcPath: return
        destPath = QFileDialog.getSaveFileName( caption='Save morpheme db to?', directory=util.dbPath + 'textFile.db' )
        if not destPath: return
        db = M.MorphDb.mkFromFile( str(srcPath) )
        db.save( str(destPath) )
        infoMsg( 'Success', 'Txt Extract' )

    def onSaveResults( self ):
        destPath = QFileDialog.getSaveFileName( caption='Save results to?', directory=util.dbPath + 'results.db' )
        if not destPath: return
        self.db.save( destPath )
        infoMsg( 'Success', 'Save db' )

    def updateDisplay( self ):
        bs = self.blacklist.text().split(',')
        for m in self.db.db.keys():
            if m.pos in bs:
                self.db.db.pop( m )
        if self.col4Mode.isChecked():
            self.morphDisplay.setText( self.db.showMs() )
        else:
            self.morphDisplay.setText( u'\n'.join( [ m.base for m in self.db.db ] ) )
        self.analysisDisplay.setText( self.db.analyze2str() )

def onMorphMan():
    mw.mainWin.mm = MorphMan( mw )
    mw.mainWin.mm.show()

def init():
    mw.mainWin.morphMan = QAction( 'MorphMan', mw )
    mw.connect( mw.mainWin.morphMan, SIGNAL('triggered()'), onMorphMan )
    mw.mainWin.toolBar.addAction( mw.mainWin.morphMan )

mw.addHook( 'init', init )
