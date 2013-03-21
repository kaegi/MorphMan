#!/usr/bin/env python
#-*- coding: utf-8 -*-

import cPickle as pickle
import codecs
import pyaudio
import wave
import win32clipboard
import win32ui, win32gui, win32con, win32api
import sys, os, time

class AudioRecorder:
    def __init__( self, fileId, hwnd ):
        self.pyaudio = p = pyaudio.PyAudio()
        self.waveFile = None
        self.stream = None

        # t.wav is audio data from txt[n].time to txt[n+1].time
        self.frames = []

        # audio settings
        self.device = p.get_default_input_device_info()[ 'index' ]
        print 'Using sound input device: %s' % p.get_default_input_device_info()[ 'name' ]
        self.fpb = 1024
        self.rate = 44100
        self.channels = 2
        self.format = pyaudio.paInt16

        # screenshots
        self.gameHwnd = hwnd
        print 'Using window with handle %d for screenshots' % hwnd

        # file output
        self.fileId = fileId
        self.count = 0
        def mkdirp( p ):
            try:    os.makedirs( p )
            except: pass
        for p in [ 'media/txt','media/img','media/audio', 'media/misc' ]: mkdirp( p )

    def saveAudio( self, path ):
        'Save all current self.frames to wave file then clear'
        wf = wave.open( path, 'wb' )
        wf.setnchannels( self.channels )
        wf.setsampwidth( self.pyaudio.get_sample_size( self.format ) )
        wf.setframerate( self.rate )
        wf.writeframes( b''.join( self.frames ) )
        wf.close()
        self.frames = []

    def start( self ):
        self.running = True

        # wave file to write audio to
        self.waveFile = wf = wave.open( 'media/misc/all.%s.wav' % self.fileId, 'wb' )
        wf.setnchannels( self.channels )
        wf.setsampwidth( self.pyaudio.get_sample_size( self.format ) )
        wf.setframerate( self.rate )

        # timing data
        self.timingFile = tf = codecs.open( 'media/misc/timing.%s.txt' % self.fileId, 'wb', encoding='utf-16' )
        self.time0 = time.time()
        self.timeData = {}

        # async audio input stream
        self.stream = stream = self.pyaudio.open( format=self.format, channels=self.channels, rate=self.rate, input=True, frames_per_buffer=self.fpb, input_device_index=self.device, stream_callback=self.onAudioInput )
        stream.start_stream()

        # register clipboard monitor
        self.registerClipboardCallback()

    def stop( self ):
        self.running = False

        # async audio input stream
        while self.stream.is_active():
            self.stream.stop_stream()
        self.stream.close()

        # wave file being written
        self.waveFile.close()

        # timing data
        pickle.dump( self.timeData, open( 'media/misc/timing.%s.dat' % self.fileId, 'wb' ), -1 )
        self.timingFile.close()

        # remove clipboard hooks
        win32clipboard.ChangeClipboardChain( self.window.GetSafeHwnd(), self.hPrev )
        self.window.DestroyWindow()

    def loop( self ):
        self.start()
        try:
            while self.stream.is_active():
                win32gui.PumpWaitingMessages()
                #time.sleep( 0.1 )
        finally:
            self.stop()

    def onAudioInput( self, in_data, frame_count, time_info, status_flags ):
        self.waveFile.writeframes( in_data )
        self.frames.append( in_data )
        if not self.running:
            return  ( None, pyaudio.paComplete )
        return ( None, pyaudio.paContinue )

    def printDevices( self ):
        for i in xrange( 0, self.pyaudio.get_device_count() ):
            print i, self.pyaudio.get_device_info_by_index( i )

    def onDrawClipboard( self, *args ):
        t = time.time() - self.time0    # time since start of audio file
        win32clipboard.OpenClipboard()
        txt = win32clipboard.GetClipboardData( win32clipboard.CF_UNICODETEXT )
        '''
        # ideas for cleaning up garbage at end
        print repr(raw)
        txt = raw.split( u'\x00\x00' )[0]
        if txt == raw:
            txt = txt.split( u'\x00' )[0]
        
        # TODO remove everything after string terminator
        #try:    txt = txt.split( u'\x00\x00' )[0]
        #except: pass
        try:
            txt = win32clipboard.GetClipboardData( win32clipboard.CF_UNICODETEXT )
            win32clipboard.EmptyClipboard()
        except TypeError: # no unicode data, probably notification that it was cleared
            h = self.hPrev
            if h:   return win32api.SendMessage( h, *args[-1][1:4] )
            else:   return 1
        '''
        win32clipboard.CloseClipboard()

        # iteratives
        self.timeData[ self.count ] = ( t, txt )
        takeScreenshot( 'media/img/{id}.{n}.bmp'.format( id=self.fileId, n=self.count ), self.gameHwnd )
        codecs.open( 'media/txt/{id}.{n}.txt'.format( id=self.fileId, n=self.count ), 'wb', encoding='utf-16' ).write( txt )
        # save audio for previous text
        if self.count > 0:
            self.saveAudio( 'media/audio/{id}.{n}.wav'.format( id=self.fileId, n=self.count-1 ) )
        self.count += 1

        # big time & txt log
        print t
        line = u'{n} {t} {txt}\r\n'.format( n=self.count, t=t, txt=txt )
        self.timingFile.write( line )

        h = self.hPrev
        if h:   return win32api.SendMessage( h, *args[-1][1:4] )
        else:   return 1

    def onChangeClipboardChain( self, *args ):
        h = self.hPrev
        if h == args[-1][2]:    h = a[-1][3]
        elif h:                 return win32api.SendMessage( h, *args[-1][1:4] )
        else:                   return 0

    def registerClipboardCallback( self ):
        self.hPrev = None

        self.window = win = win32ui.CreateFrame()
        win.CreateWindow( None, '', win32con.WS_OVERLAPPEDWINDOW )
        win.HookMessage( self.onDrawClipboard, win32con.WM_DRAWCLIPBOARD )
        win.HookMessage( self.onChangeClipboardChain, win32con.WM_CHANGECBCHAIN )
        try:
            self.hPrev = win32clipboard.SetClipboardViewer( win.GetSafeHwnd() )
        except win32api.error, err:
            if err.args[0]: raise

def takeScreenshot( path='screenshot.bmp', hwnd=None ):
    if hwnd is None:
        time.sleep(3)
        hwnd = win32gui.GetForegroundWindow()
        return hwnd
    l, t, r, b = win32gui.GetWindowRect( hwnd )
    w = r - l
    h = b - t

    hwndDC = win32gui.GetWindowDC( hwnd )
    mfcDC = win32ui.CreateDCFromHandle( hwndDC )
    saveDC = mfcDC.CreateCompatibleDC()

    bmp = win32ui.CreateBitmap()
    bmp.CreateCompatibleBitmap( mfcDC, w, h )
    saveDC.SelectObject( bmp )
    saveDC.BitBlt( (0,0), (w,h), mfcDC, (0,0), win32con.SRCCOPY )
    bmp.SaveBitmapFile( saveDC, path )

def main():
    if len( sys.argv ) < 2:
        print 'Please specify an identifier to use in file names (for ordering/resuming)'
        return
    print 'Please switch to the game window within 3 seconds in order to identify it for screenshot purposes'
    ar = AudioRecorder( sys.argv[1], takeScreenshot() )
    ar.loop()
main()
