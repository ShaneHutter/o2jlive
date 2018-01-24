#!/bin/python
'''
O2J Transport
    o2jtransport
      Written By:  Shane Hutter

        This sowftware is licensed under the GNU GPL version 3

        required Dependencies: python >= 3.5, liblo, cython, pyliblo, JACK-Client, cifi, and jack

    This software controls the jack playhead with OSC messages.
    It can start stop and relocate the jack playhead.
    It is intended to be controlled remotely with either O2J Live or
    any other OSC client.
'''

import jack, liblo, sys

#PROGRAM CONST
CLEAN=0
ERROR=255

#JACK CONST
PREVIOUS_FRAME_INDEX=0
CURRENT_FRAME_INDEX=1
JACK_TRANSPORT_DATA_INDEX=1
JACK_TRANSPORT_LOCATION_INDEX='frame'
FRAME_ZERO=0

#OSC CONST

#program vars
mainLoop=True

#config vars
configFileName='o2jlive.conf'
configLines=open(configFileName,'r').read().split('\n')

#jack vars
jackClientName='O2J Transport'
trackFrame=[0]*2
transportMoved=False
preferedLatency=5

#osc vars


#load Config file
#CONFIG CONST
CONFIG_PROPERTY_ARG=0
CONFIG_VALUE_ARG=1
for lineRead in configLines:
    if (lineRead!="") and (lineRead.strip()[0:1]!='#'):
        #verbosity settings
        if lineRead.split()[CONFIG_PROPERTY_ARG]=='o2jtransport.verbose_osc_listen_port':
            global verboseOscListenPort
            verboseOscListenPort=bool(int(lineRead.split()[CONFIG_VALUE_ARG]))
        if lineRead.split()[CONFIG_PROPERTY_ARG]=='o2jtransport.verbose_latency':
            global verboseLatency
            verboseLatency=bool(int(lineRead.split()[CONFIG_VALUE_ARG]))
        
        #osc settings
        if lineRead.split()[CONFIG_PROPERTY_ARG]=='o2jtransport.osc_listen_port':
            global oscListenPort
            oscListenPort=int(lineRead.split()[CONFIG_VALUE_ARG]) 

#start osc server
try:
    osc_server=liblo.Server(oscListenPort)
    #verbose listen port
    if verboseOscListenPort==True:
        print('Listening for OSC messages on port', end=' ')
        print(oscListenPort)
except liblo.ServerError as  error:
    print(str(error))
    sys.exit(ERROR)

#create jack client
jack_client = jack.Client(jackClientName)
jack_client.activate()
jack_client.transport_stop()
jackLatency=int((jack_client.blocksize*2/jack_client.samplerate)*1000)
if verboseLatency==True:
    print('JACK latency detected at:', end=' ')
    print(jackLatency, end='')
    print('ms')
if jackLatency>preferedLatency:
    print('Warning:  JACK is not setup for very low latency!')
    print('          Errors may occur during looping.')
    print('          To prevent this use a smaller Frames/Period')

def moveTransport(location):
    #use this function to both move the transport, and confirm that
    #the transport is actually at that location
    jack_client.transport_locate(location)
    currentLoc=jack_client.transport_query()[JACK_TRANSPORT_DATA_INDEX][JACK_TRANSPORT_LOCATION_INDEX]
    while currentLoc!=location:
        if currentLoc>location:
            jack_client.transport_locate(location)
        currentLoc=jack_client.transport_query()[JACK_TRANSPORT_DATA_INDEX][JACK_TRANSPORT_LOCATION_INDEX]
    trackFrame[PREVIOUS_FRAME_INDEX]=currentLoc-jack_client.blocksize
    trackFrame[CURRENT_FRAME_INDEX]=currentLoc
    global transportMoved
    transportMoved=True
    return

#reposition playhead to start upon startup
moveTransport(FRAME_ZERO)
transportMoved=False

def trackTransport():
    #track the transport
    global trackFrame
    trackFrame[PREVIOUS_FRAME_INDEX]=trackFrame[CURRENT_FRAME_INDEX]
    trackFrame[CURRENT_FRAME_INDEX]=jack_client.transport_query()[JACK_TRANSPORT_DATA_INDEX][JACK_TRANSPORT_LOCATION_INDEX]
    return


#main loop
print('Ready...')
while mainLoop!=False:
    
    trackTransport()    
    #recieve OSC
    osc_server.recv(jackLatency)
    
#shutdown
jack_client.transport_stop()
jack_client.deactivate()
sys.exit(CLEAN)