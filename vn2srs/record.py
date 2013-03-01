#!/usr/bin/env python
#-*- coding: utf-8 -*-

import pyaudio
import wave
import win32clipboard
import win32ui, win32gui, win32con, win32api
import sys, os, time

################################################################################
## Audio recording
################################################################################

class AudioRecorder:
    def __init__( self ):
        self.pyaudio = p = pyaudio.PyAudio()
        self.waveFile = None
        self.stream = None

        # settings
        self.device = p.get_default_input_device_info()[ 'index' ]
        #self.device = p.get_default_output_device_info()[ 'index' ]
        self.fpb = 1024
        self.rate = 44100
        self.channels = 2
        self.format = pyaudio.paInt16

    def start( self ):
        self.running = True
        self.waveFile = wf = wave.open( 'output.wav', 'wb' )
        wf.setnchannels( self.channels )
        wf.setsampwidth( self.pyaudio.get_sample_size( self.format ) )
        wf.setframerate( self.rate )

        self.stream = stream = self.pyaudio.open( format=self.format, channels=self.channels, rate=self.rate, input=True, frames_per_buffer=self.fpb, input_device_index=self.device, stream_callback=self.onAudioInput )
        stream.start_stream()

    def stop( self ):
        self.running = False
        while self.stream.is_active():
            self.stream.stop_stream()
        self.stream.close()
        self.waveFile.close()

    def loop( self ):
        self.start()
        try:
            while self.stream.is_active():
                time.sleep( 0.1 )
        finally:
            self.stop()

    def onAudioInput( self, in_data, frame_count, time_info, status_flags ):
        self.waveFile.writeframes( in_data )
        if not self.running:
            return  ( None, pyaudio.paComplete )
        return ( None, pyaudio.paContinue )

    def devices( self ):
        for i in xrange( 0, self.pyaudio.get_device_count() ):
            print i, self.pyaudio.get_device_info_by_index( i )

################################################################################
## Clipboard monitor
################################################################################
hPrev = 0
nCbcs = 0

def onDrawCb( *args ):
    global nCbcs
    t = time.time()
    nCbcs += 1
    #print 'onDrawCb', nCbcs, args
    win32clipboard.OpenClipboard()
    txt = win32clipboard.GetClipboardData()
    win32clipboard.CloseClipboard()
    print t, txt
    if hPrev: return win32api.SendMessage( hPrev, *args[-1][1:4] )
    else: return 1

def onCcbc( *args ):
    global hPrev
    #print 'onCcbc', args
    if hPrev == args[-1][2]: hPrev = a[-1][3]
    elif hPrev: return win32api.SendMessage( hPrev, *a[-1][1:4] )
    else: return 0

def wait(timeout_msec=5000, need_changes=1):
    global hPrev, nCbcs
    win=win32ui.CreateFrame()
    win.CreateWindow(None,'',win32con.WS_OVERLAPPEDWINDOW)
    win.HookMessage(onDrawCb,win32con.WM_DRAWCLIPBOARD)
    win.HookMessage(onCcbc,win32con.WM_CHANGECBCHAIN)
    try:
        hPrev=win32clipboard.SetClipboardViewer(win.GetSafeHwnd())
    except win32api.error, err:
        if err.args[0]: raise
    nCbcs=0
    if timeout_msec:
        timid = win.SetTimer(1,20)
        curtime = win32api.GetTickCount()
        endtime = timeout_msec + curtime

    while nCbcs<need_changes:
        win32gui.PumpWaitingMessages()
        if timeout_msec and win32api.GetTickCount()>endtime: break

    if timeout_msec:
        win.KillTimer(timid)
    win32clipboard.ChangeClipboardChain(win.GetSafeHwnd(), hPrev)
    win.DestroyWindow()
    return nCbcs

# start clipboard daemon
#wait( timeout_msec=None, need_changes = sys.maxint )

################################################################################
## Driver
################################################################################

def main():
    ar = AudioRecorder()
    #ar.devices()
    #ar.loop()
    ar.start()
    #wait( None, sys.maxint )
main()
