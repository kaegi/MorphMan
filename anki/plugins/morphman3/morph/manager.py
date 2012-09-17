# -*- coding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import os

import adaptiveSubs
from morphemes import MorphDb
from util import dbsPath, errorMsg, infoMsg, mw, parseWhitelist

def getPath( le ): # LineEdit -> GUI ()
    path = QFileDialog.getOpenFileName( caption='Open db', directory=dbsPath )
    le.setText( path )

def mkBtn( txt, f, conn, parent ):
    b = QPushButton( txt )
    conn.connect( b, SIGNAL('clicked()'), f )
    parent.addWidget( b )
    return b

class AdaptiveSubWin( QDialog ):
    def __init__( self, parent=None ):
        super( AdaptiveSubWin, self ).__init__( parent )
        self.setWindowTitle( 'Adaptive Subs' )
        self.grid = grid = QGridLayout( self )
        self.vbox = vbox = QVBoxLayout()

        self.blacklist  = QLineEdit( u'記号,UNKNOWN' )
        self.whitelist  = QLineEdit( u'' )
        self.matureFmt  = QLineEdit( u'%(jpn)s' )
        self.knownFmt   = QLineEdit( u'%(jpn)s [%(eng)s]' )
        self.unknownFmt = QLineEdit( u'%(eng)s [%(N_k)s] [%(unknowns)s]' )

        self.vbox.addWidget( QLabel( 'POS Blacklist' ) )
        self.vbox.addWidget( self.blacklist )
        self.vbox.addWidget( QLabel( 'POS Whitelist' ) )
        self.vbox.addWidget( self.whitelist )
        self.vbox.addWidget( QLabel( 'Mature Format' ) )
        self.vbox.addWidget( self.matureFmt )
        self.vbox.addWidget( QLabel( 'Known Format' ) )
        self.vbox.addWidget( self.knownFmt )
        self.vbox.addWidget( QLabel( 'Unknown Format' ) )
        self.vbox.addWidget( self.unknownFmt )

        self.goBtn = mkBtn( 'Convert subs', self.onGo, self, vbox )

        grid.addLayout( vbox, 0, 0 )

    def onGo( self ):
        ws = parseWhitelist( self.whitelist.text() )
        bs = parseWhitelist( self.blacklist.text() )
        mFmt = unicode( self.matureFmt.text() )
        kFmt = unicode( self.knownFmt.text() )
        uFmt = unicode( self.unknownFmt.text() )

        inFile = QFileDialog.getOpenFileName( caption='Dueling subs to process', directory=dbsPath )
        if not inFile: return
        outFile = QFileDialog.getSaveFileName( caption='Save adaptive subs to', directory=dbsPath )
        if not outFile: return

        adaptiveSubs.run( inFile, outFile, ws, bs, mFmt, kFmt, uFmt )
        infoMsg( 'Completed successfully' )

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
        self.blacklist = QLineEdit( u'記号,助詞,UNKNOWN' )
        self.whitelist = QLineEdit( u'' )
        vbox.addWidget( self.col4Mode )
        vbox.addWidget( self.col1Mode )
        vbox.addWidget( QLabel( 'POS Blacklist' ) )
        vbox.addWidget( self.blacklist )
        vbox.addWidget( QLabel( 'POS Whitelist' ) )
        vbox.addWidget( self.whitelist )
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
    def loadB( self ):
        self.bPath = self.bPathLEdit.text()
        self.bDb = MorphDb( path=self.bPath )
    def loadAB( self ):
        self.loadA()
        self.loadB()

    def onShowA( self ):
        try: self.loadA()
        except Exception, e: return errorMsg( 'Can\'t load db:\n%s' % e )
        self.db = self.aDb
        self.updateDisplay()

    def onDiff( self, type='sym' ):
        try: self.loadAB()
        except Exception, e: return errorMsg( 'Can\'t load dbs:\n%s' % e )

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
        srcPath = QFileDialog.getOpenFileName( caption='Text file to extract from?', directory=dbsPath )
        if not srcPath: return
        destPath = QFileDialog.getSaveFileName( caption='Save morpheme db to?', directory=dbsPath + os.sep + 'textFile.db' )
        if not destPath: return
        db = MorphDb.mkFromFile( str(srcPath) )
        if db:
            db.save( str(destPath) )
            infoMsg( 'Extracted successfully' )

    def onSaveResults( self ):
        destPath = QFileDialog.getSaveFileName( caption='Save results to?', directory=dbsPath + os.sep + 'results.db' )
        if not destPath: return
        if not hasattr( self, 'db' ): return errorMsg( 'No results to save' )
        self.db.save( str(destPath) )
        infoMsg( 'Saved successfully' )

    def updateDisplay( self ):
        bs = self.blacklist.text().split(',')
        ws = self.whitelist.text().split(',') if self.whitelist.text() else []
        for m in self.db.db.keys():
            if m.pos in bs:
                self.db.db.pop( m )
            elif ws and m.pos not in ws:
                self.db.db.pop( m )
        if self.col4Mode.isChecked():
            self.morphDisplay.setText( self.db.showMs() )
        else:
            self.morphDisplay.setText( u'\n'.join( [ m.base for m in self.db.db ] ) )
        self.analysisDisplay.setText( self.db.analyze2str() )

def main():
    mw.mm = MorphMan( mw )
    mw.mm.show()
