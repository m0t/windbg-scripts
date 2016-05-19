'''
vtfinder.py
Nicolas Guigo
iSECPartners
07/2104
'''

from pykd import *
import sys

modules = []
heapRequested = 0

class fvtEventHandler(eventHandler):
    def onModuleLoad(self, arg2, moduleName):
        global modules
        modules.append(module(moduleName))
        dprintln("Added %s in module list:" % (moduleName))
        printModules()
        return eventResult.NoChange

def printModules():
    for module in modules:
        dprintln("%s" % str((module.name())))

def printCommand(command):
    dprintln("%s" % (dbgCommand(command)))

def breakhandler64(bp):
    chunkUserAddress = reg('r8')
    heap = reg('rcx')
    if chunkUserAddress!=0 and (heapRequested==0 or heap==heapRequested):
        address = ptrQWord(chunkUserAddress)
        if isAddressWithinLoadedModules(address):
            dprintln("================> FOUND %s (%#x) ON HEAP CHUNK %#x" % (findSymbol(address), address, chunkUserAddress))
            printCommand("!heap -x %x" % (chunkUserAddress))
#        else:
#            dprintln("%#x not in any loaded modules" % (address))
    return False

def breakhandler32(bp):
    print("HeapAlloc break")
    chunkUserAddress = ptrDWord(reg('esp')+0x0C)
    heap = ptrDWord(reg('esp')+0x04)
    if chunkUserAddress!=0 and (heapRequested==0 or heap==heapRequested):
        address = ptrDWord(chunkUserAddress)
        if isAddressWithinLoadedModules(address):
            dprintln("================> FOUND %s (%#x) ON HEAP CHUNK %#x" % (findSymbol(address), address, chunkUserAddress))
            printCommand("!heap -x %x" % (chunkUserAddress))
#        else:
#            dprintln("%#x not in any loaded modules)" % (address))
    return False

def getInitialModules():
    global modules
    cmd = dbgCommand('lm').split('\n')[1:-1]
    for line in cmd:
        substrings = " ".join(line.split()).split()
        if len(substrings) > 2:
            modulename = str(substrings[2])
            modules.append(module(modulename))

def isAddressWithinLoadedModules(address):
    ret = False
    for mod in modules:
        if address>mod.begin() and address<mod.end():
                ret = True
    return ret

def isX86():
    if dbgCommand(".effmach").find("x86 compatible (x86)") > 0:
        return True
    else: 
        return False

def main():
    global heapRequested
    # Fix symbols
    dbgCommand('.symfix')
    dbgCommand('.reload')
    # Populate already loaded modules
    getInitialModules()
    # Setup handler for delay loaded modules
    myEventHandler= fvtEventHandler()
    # Get arch and heap params
    #arch32 = (sys.argv[1].lower()=='X86'.lower()) if len(sys.argv)>1 else False
    arch32 = isX86()
    heapRequested = int(sys.argv[1], 16) if len(sys.argv)>1 else 0
    # Run x86 or x64 version
    if arch32:
        setBp(module('ntdll').offset('RtlFreeHeap'), breakhandler32)
    else:
        setBp(module('ntdll').offset('RtlFreeHeap'), breakhandler64)
    dprintln("Arch is %s and heap is %#x %s" % ("X86" if arch32 else "X64", heapRequested, "(any)" if heapRequested == 0 else ""))
    dprintln("Monitoring started")
    #dprintln("Currently monitored modules:")
    #printModules()
    go()

if __name__ == '__main__' :
    main()
