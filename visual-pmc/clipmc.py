import json
import alphaoptimize
import pmcparser
import pmcanalysis
import sys

def getArgumentDictionary(argv):
    argd = {}
    for arg in argv:
        kv = arg.split(':=')
        if len(kv) == 2:
            argd[kv[0]] = kv[1]
        else:
            print(f"wrong argument: {arg}. Arguments should be formatted as <key>=<value> pairs")
    return argd

def printUsage():
    print("usage: clipmc prismmodelfile:=<filename> obsfile:=<filename> pmcformula:=<formula> confidence:=<confidence>")


#####################
#        MAIN       #
#####################

# Arguments set as list of key=value pairs
# keys:
#  prismmodelfile
#  obsfile
#  pmcformula
#  confidence
if len(sys.argv) < 2:
    printUsage()
    exit(1)

argd = getArgumentDictionary(sys.argv[1:])

print(f"Arguments: {argd}")    

prismmodel=""
try:
    with open(argd['prismmodelfile'], 'r') as file:
        prismmodel = file.read()
except FileNotFoundError:
    print(f"Prism Model File {argd['prismmodelfile']} not found")

graph = pmcparser.extractGraphFromPrism(prismmodel)

g2 = None
try:
    with open(argd['obsfile'], 'r') as file:
        log  = json.load(file)
        g2 = pmcparser.populateTransitionObservations(graph,log)
except FileNotFoundError:
    print(f"Error: The file {argd['obsfile']} was not found.")
except json.JSONDecodeError as e:
    print(f"Error: Failed to decode JSON from the file. Details: {e}")

eq = pmcanalysis.pmcprismanalysis(prismmodel,graph,argd['pmcformula'])
prob = alphaoptimize.calculateProbability(eq,g2)
min,max = pmcanalysis.calcConfidenceInterval(g2,eq,float(argd['confidence']))

print(f"probability: {prob} confidence interval [{min},{max}] equation: {eq}")


