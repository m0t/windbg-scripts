'''
vtsearch.py
by _m0t but massively copied from:

vtfinder.py
Nicolas Guigo
iSECPartners
07/2104 <- note that he wrote this almost a century in the future, you'd think pykd would be better by then...
'''

from pykd import *
import optparse
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

def die(msg):
    sys.stderr.write("[ERROR] " + msg + "\n")
    sys.exit(-1)

def parse_args():
    parser = optparse.OptionParser("%prog [some opts] [-L filelist]|[-D fuzzdir]")
    parser.add_option("-L", "--log", help="write to logfile, default: vtsearch.log", dest="logfile", default="vtsearch.log")
    parser.add_option("-H", "--heap", help="specify heap", dest="heap", default=None)
    return parser.parse_args() 

def printModules():
    for module in modules:
        dprintln("%s" % str((module.name())))

def printCommand(command):
    dprintln("%s" % (dbgCommand(command)))

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

def getEntries(heap):
    lines = dbgCommand("!heap -h %s" % hex(heap)).splitlines()
    entries = []
    start = -1
    end = len(lines)-1
    for l in lines:
        #find start
        if l.find("Heap entries for Segment") > 0:
            start = lines.index(l)+2 #remember the additional line
            break
    i = start
    while i <= end:
        #the lines we dont want, remove, case by case, do we care about busy/freed? boh
        if lines[i].find("Heap entries for Segment") > 0:
            i+=2
            continue
        if lines[i].find("uncommitted bytes") > 0:
            i += 1
            continue
        #get only the entry address
        if lines[i]:
            entries.append( " ".join(lines[i].split()).split()[0].replace(":", "") )
        i+=1
    return entries


def findVtables(heap):
    found = False
    for entry in getEntries(heap):
        address = ptrDWord(int(entry,16)+8) #looks about right
        #print("searching address %s" % hex(address))
        if isAddressWithinLoadedModules(address):
            found = True
            dprintln("================> FOUND %s (%#x) ON HEAP CHUNK %s" % (findSymbol(address), address, entry))
            printCommand("!heap -x %s" % (entry))
    return found

def start_log(logfile):
    if dbgCommand(".logopen /d %s" % logfile).find("could not be opened"):
        return False
    return True

def close_log(logfile)
    dbgCommand(".logclose")

def main():
    global heapRequested

    opts, args = parse_args()
    if opts.heap:
        heapRequested = opts.heap
    else:
        die("specify an heap, see help")
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
    #heapRequested = int(sys.argv[1], 16) if len(sys.argv)>1 else 0
    #printModules()
    if not arch32:
        print("dont know if this works on x64")
    if opts.logfile:
        if not start_log(opts.logfile):
            die("Could not open requested logfile")
    if (findVtables(heapRequested) == False ):
        print("Sorry, nothing found! :(")

    if opts.logfile:
        if not close_log(opts.logfile):
            die("wtf? error closing log, this odd")


if __name__ == '__main__' :
    main()
