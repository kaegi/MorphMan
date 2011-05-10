# -*- coding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from anki.hooks import addHook
from ankiqt import mw
import os

import morphemes as M
import util

def getPath( le ):
    path = QFileDialog.getOpenFileName( caption='Open db', directory=util.knownDbPath )
    le.setText( path )

def mkBtn( txt, f, conn, parent ):
    b = QPushButton( txt )
    conn.connect( b, SIGNAL('clicked()'), f )
    parent.addWidget( b )
    return b

def errorMsg( txt ): return QMessageBox.critical( mw, 'Error', txt )

class MorphMan( QDialog ):
    def __init__( self, parent=None ):
        super( MorphMan, self ).__init__( parent )
        self.setWindowTitle( 'Morph Man Title' )
        #self.resize( 640,480 )
        grid = QGridLayout( self )
        vbox = QVBoxLayout()

        # Extract from txt file
        self.exportTxtFileBtn = mkBtn( 'Export morphemes from file', self.onExportTxtFile, self, vbox )

        # DB Paths
        #self.aPathLbl = QLabel( 'db A: ')
        self.aPathLEdit = QLineEdit()
        #vbox.addWidget( self.aPathLbl )
        vbox.addWidget( self.aPathLEdit )
        self.aPathBtn = mkBtn( 'Browse for DB A', lambda le=self.aPathLEdit: getPath( le ), self, vbox )

        #self.bPathLbl = QLabel( 'db B: ')
        self.bPathLEdit = QLineEdit()
        #vbox.addWidget( self.bPathLbl )
        vbox.addWidget( self.bPathLEdit )
        self.bPathBtn = mkBtn( 'Browse for DB B', lambda le=self.bPathLEdit: getPath( le ), self, vbox )

        # Actions
        self.showABtn = mkBtn( 'A', self.onShowA, self, vbox )
        self.AmBBtn = mkBtn( 'A-B', lambda x='A-B': self.onDiff(x), self, vbox )
        self.BmABtn = mkBtn( 'B-A', lambda x='B-A': self.onDiff(x), self, vbox )
        self.symBtn = mkBtn( 'Symmetric Difference', lambda x='sym': self.onDiff(x), self, vbox )
        self.interBtn = mkBtn( 'Intersection', lambda x='inter': self.onDiff(x), self, vbox )
        self.unionBtn = mkBtn( 'Union', lambda x='union': self.onDiff(x), self, vbox )

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

    def onExportTxtFile( self ):
        srcPath = QFileDialog.getOpenFileName( caption='Text file to export from?', directory=util.dbPath )
        if not srcPath: return
        destPath = QFileDialog.getSaveFileName( caption='Save morpheme db to?', directory=util.dbPath + 'textFile.db' )
        if not destPath: return
        ms = M.file2ms( srcPath )
        M.saveDb( M.ms2db( ms ), destPath )
        QMessageBox.information( mw, 'Txt Export', 'Success' )

    def loadA( self ):
        self.aPath = self.aPathLEdit.text()
        self.aDb = M.loadDb ( self.aPath )
    def loadB( self ):
        self.bPath = self.bPathLEdit.text()
        self.bDb = M.loadDb ( self.bPath )
    def loadAB( self ):
        self.loadA()
        self.loadB()

    def onShowA( self ):
        try: self.loadA()
        except: return errorMsg( 'Can\'t load db' )
        self.aSet = set( self.aDb.keys() )
        self.morphemes = self.aSet
        self.updateDisplay()

    def onDiff( self, type='sym' ):
        try: self.loadAB()
        except: return errorMsg( 'Can\'t load dbs' )
        self.aSet = set( self.aDb.keys() )
        self.bSet = set( self.bDb.keys() )
        if type == 'sym': self.morphemes = self.aSet.symmetric_difference( self.bSet )
        elif type == 'A-B': self.morphemes = self.aSet.difference( self.bSet )
        elif type == 'B-A': self.morphemes = self.bSet.difference( self.aSet )
        elif type == 'inter': self.morphemes = self.aSet.intersection( self.bSet )
        elif type == 'union': self.morphemes = self.aSet.union( self.bSet )
        self.updateDisplay()

    def updateDisplay( self ):
        bs = self.blacklist.text().split(',')
        ms = [ m for m in self.morphemes if m[1] not in bs ]
        if self.col4Mode.isChecked():
            self.morphDisplay.setText( M.ms2str( ms ).decode('utf-8') )
        else:
            self.morphDisplay.setText( u'\n'.join( [ e for (e,p,sp,r) in ms ] ) )
        self.analysisDisplay.setText( M.analyze2str( self.morphemes ) )


def onMorphMan():
    mw.mainWin.mm = MorphMan( mw )
    mw.mainWin.mm.show()

def init():
    mw.mainWin.morphMan = QAction( 'MorphMan', mw )
    mw.connect( mw.mainWin.morphMan, SIGNAL('triggered()'), onMorphMan )
    mw.mainWin.toolBar.addAction( mw.mainWin.morphMan )

mw.addHook( 'init', init )
