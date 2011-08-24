# -*- coding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from anki.hooks import addHook
from ankiqt import mw
import datetime, glob, gzip, pickle, os
from threading import ThreadError

import auto
import morphemes as M
import util
from util import errorMsg, infoMsg, deckDbPath

def getPath( le ):
    path = QFileDialog.getOpenFileName( caption='Open db', directory=util.knownDbPath )
    le.setText( path )

def mkBtn( txt, f, conn, parent ):
    b = QPushButton( txt )
    conn.connect( b, SIGNAL('clicked()'), f )
    parent.addWidget( b )
    return b

class MorphManAuto( QDialog ):
    def __init__( self, parent=None ):
        super( MorphManAuto, self ).__init__( parent )
        self.setWindowTitle( 'Morph Man 2 - Auto' )
        self.grid = grid = QGridLayout( self )
        self.vbox = vbox = QVBoxLayout()
        self.keyBox = keyBox = QVBoxLayout()
        self.valueBox = valBox = QVBoxLayout()

        # Config
        self.cfgWidgets = []
        self.cfg = {}
        self.cfgPath = None
        self.mkDeckChooserBox( vbox )
        self.saveCfgBtn = mkBtn( 'Save cfg', self.saveCfg, self, vbox )

        # Start/stop
        self.restartAuto = mkBtn( 'Restart auto', self.restartAuto, self, vbox )
        self.stopAuto = mkBtn( 'Stop auto', self.stopAuto, self, vbox )
        lastUpMsg = "Updater hasn't finished since starting Anki" if not util.lastUpdate else \
            "Last update @ %s" % datetime.datetime.fromtimestamp( util.lastUpdate )
        self.vbox.addWidget( QLabel( lastUpMsg ) )

        # layout
        grid.addLayout( vbox, 0, 0 )
        grid.addLayout( keyBox, 0, 1 )
        grid.addLayout( valBox, 0, 2 )

    def saveCfg( self ):
        try:
            morphFields = eval(str( self.fieldsV.text() ))
            ints = eval(str( self.intsV.text() ))
        except SyntaxError:
            raise Exception('Invalid intervals or fields list')
        assert type(morphFields) == list, "Fields to check must be a python list of strings. eg ['Expression','Context()1']"
        assert type(ints) == list, "Intervals must be a python list of integers. eg [1, 4, 28, 3, 18, 402]"
        d = {
            'mature threshold': int(self.matV.text()),
            'learnt threshold': int(self.learntV.text()),
            'known threshold': int(self.knownV.text()),

            'vocab rank field': str(self.vrV.text()),
            'i+N field': str(self.ipnV.text()),
            'unknowns field': str(self.unkV.text()),
            'morph man index field': str(self.mmiV.text()),
            'enabled': str(self.enabledV.text()),

            'morph fields': morphFields,
            'interval dbs to make': ints,
        }
        self.cfg.update( d )
        f = gzip.open( self.cfgPath, 'wb' )
        pickle.dump( self.cfg, f )
        f.close()

    def loadCfg( self, dcbIndex ):
        def mkKey( txt ):
            l = QLabel( txt )
            self.keyBox.addWidget( l )
            return l
        def mkLE():
            le = QLineEdit( '' )
            self.valueBox.addWidget( le )
            return le

        # Load
        self.cfgPath = str( self.dcb.itemData( dcbIndex ).toPyObject() )
        f = gzip.open( self.cfgPath, 'rb' )
        self.cfg = d = pickle.load( f )
        f.close()

        # if first load, create the widgets
        if not hasattr( self, 'vrK' ):
            self.vrK, self.vrV = mkKey( 'Vocab Rank field' ), mkLE()
            self.ipnK, self.ipnV = mkKey( 'i+N field' ), mkLE()
            self.unkK, self.unkV = mkKey( 'Unknowns field' ), mkLE()
            self.mmiK, self.mmiV = mkKey( 'Morph Man Index field' ), mkLE()

            self.matK, self.matV = mkKey( 'Mature threshold' ), mkLE()
            self.knownK, self.knownV = mkKey( 'Known threshold' ), mkLE()
            self.learntK, self.learntV = mkKey( 'Learnt threshold' ), mkLE()
            self.fieldsK, self.fieldsV = mkKey( 'Fields to check' ), mkLE()
            self.intsK, self.intsV = mkKey( 'Intervals to make dbs for' ), mkLE()
            self.enabledK, self.enabledV = mkKey( 'Enabled?' ), mkLE()

            self.deckUp, self.dbUp = QLabel(), QLabel()
            self.vbox.addWidget( self.deckUp )
            self.vbox.addWidget( self.dbUp )

        # now set data
        self.vrV.setText( d['vocab rank field'] )
        self.ipnV.setText( d['i+N field'] )
        self.unkV.setText( d['unknowns field'] )
        self.mmiV.setText( d['morph man index field'] )

        self.matV.setText( str(d['mature threshold']) )
        self.knownV.setText( str(d['known threshold']) )
        self.learntV.setText( str(d['learnt threshold']) )
        self.enabledV.setText( str(d['enabled']) )

        self.fieldsV.setText( str(d['morph fields']) )
        self.intsV.setText( str(d['interval dbs to make']) )

        f = datetime.datetime.fromtimestamp
        self.deckUp.setText( 'Deck last updated @\n%s\nin %0.2f sec' % ( f( d['last deck update'] ), d['last deck update took'] ) )
        self.dbUp.setText( 'Db last updated in %0.2f sec' % ( d['last all.db update took'] ) )

    def mkDeckChooserBox( self, parent ):
        self.dcb = QComboBox()
        parent.addWidget( self.dcb )
        self.connect( self.dcb, SIGNAL('currentIndexChanged(int)'), self.loadCfg )

        ps = glob.glob( deckDbPath + os.sep + '*' + os.sep + 'config' )
        for p in ps:
            x, _ = os.path.split( p )
            _, deckName = os.path.split( x )
            self.dcb.addItem( deckName, p )

    def restartAuto( self ):
        try:
            util.updater.term()
        except ValueError: pass # bad tid => already stopped
        except ThreadError: pass # not active
        except SystemError: # async exc failed
            errorMsg( 'Unable to stop auto' )
        auto.main()
        infoMsg( 'Restarted' )

    def stopAuto( self ):
        try:
            util.updater.term()
            infoMsg( 'Auto stopping' )
        except ValueError: # bad tid
            infoMsg( 'Auto already stopped' )
        except ThreadError: # not active
            infoMsg( 'Auto already stopped' )
        except SystemError: # async exc failed
            errorMsg( 'Unable to stop auto' )

class MorphMan( QDialog ):
    def __init__( self, parent=None ):
        super( MorphMan, self ).__init__( parent )
        self.mw = parent
        self.setWindowTitle( 'Morph Man 2' )
        self.grid = grid = QGridLayout( self )
        self.vbox = vbox = QVBoxLayout()

        # Automatic updater
        self.controlAuto = mkBtn( 'Control auto', self.controlAuto, self, vbox )
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

    def controlAuto( self ):
        self.hide()
        mma = MorphManAuto( self.mw )
        mma.show()

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
