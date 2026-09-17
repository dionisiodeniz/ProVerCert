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
            print(f"wrong argument: {arg}. Arguments should be formatted as <key>:=<value> pairs")
            return {}
    return argd

def printUsage():
    print("usage: clipmc has three commands: analyze, create_template, and populate_template. These are used as follows:")
    print("python clipmc.py analyze prismmodelfile:=<filename> obsfile:=<filename> pmcformula:=<formula> confidence:=<confidence>")
    print("python clipmc.py create_template prismmodelfile:=<filename> templatefile:=<filename>")
    print("python clipmc.py populate_template templatefile:=<filename> logfile:=<filename>")
    print("python clipmc.py add_observations templatefile:=<filename> logfile:=<filename>")
    print("\twith logfile as the file obtained from running the PX4 simulation")


#####################
#        MAIN       #
#####################

# Arguments set as list of key=value pairs
# keys:
#  prismmodelfile
#  obsfile
#  pmcformula
#  confidence
#  templatefile
#  logfile
if len(sys.argv) < 2:
    printUsage()
    exit(1)

command = sys.argv[1]

argd = getArgumentDictionary(sys.argv[2:])

if command == "analyze":
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

    # This is human readable output
    #print(f"probability: {prob} confidence interval [{min},{max}] equation: {eq}")

    # This is csv style
    print(f"{prob},{min},{max},{eq}")
elif command == "create_template":
    prismmodel=""
    try:
        with open(argd['prismmodelfile'], 'r') as file:
            prismmodel = file.read()
    except FileNotFoundError:
        print(f"Prism Model File {argd['prismmodelfile']} not found")

    graph = pmcparser.extractGraphFromPrism(prismmodel)
    pmcparser.createTemplate(argd['templatefile'],graph)
elif command == "populate_template":
    pmcparser.addTransitionObservations(argd['templatefile'],argd['logfile'], replace=True)
elif command == "add_observations":
    pmcparser.addTransitionObservations(argd['templatefile'],argd['logfile'], replace=False)
else:
    print(f"invalid command: {command}")
    printUsage()

