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
    def __init__( self ):
        self.pyaudio = p = pyaudio.PyAudio()
        self.waveFile = None
        self.stream = None

        # t.wav is audio data from txt[n].time to txt[n+1].time
        self.frames = []
        self.lastTextTime = None

        # settings
        self.device = p.get_default_input_device_info()[ 'index' ]
        self.fpb = 1024
        self.rate = 44100
        self.channels = 2
        self.format = pyaudio.paInt16

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
        self.waveFile = wf = wave.open( 'all.wav', 'wb' )
        wf.setnchannels( self.channels )
        wf.setsampwidth( self.pyaudio.get_sample_size( self.format ) )
        wf.setframerate( self.rate )

        # timing data
        self.timingFile = tf = codecs.open( 'timing.txt', 'wb', encoding='utf-16' )
        #self.timingFile = tf = open( 'timing.txt', 'wb' )
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
        pickle.dump( self.timeData, open( 'timing.dat', 'wb' ), -1 )
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
        win32clipboard.CloseClipboard()

        # iteratives
        self.timeData[ t ] = txt
        takeScreenshot( '%f.bmp' % t )
        codecs.open( '%f.txt' % t, 'wb', encoding='utf-16' ).write( txt )
        # save audio for previous text
        if self.lastTextTime:
            self.saveAudio( '%f.wav' % self.lastTextTime )
            self.lastTextTime = t

        # big time & txt log
        print t
        line = u'%f %s\r\n' % ( t, txt )
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

def takeScreenshot( path='screenshot.bmp' ):
    hwnd = win32gui.GetForegroundWindow()
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
    ar = AudioRecorder()
    #ar.printDevices()
    ar.loop()
main()
