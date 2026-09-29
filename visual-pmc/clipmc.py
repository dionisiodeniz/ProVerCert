# ProVer-Cert Source Code
# Copyright 2026 Carnegie Mellon University.
# NO WARRANTY. THIS CARNEGIE MELLON UNIVERSITY AND SOFTWARE ENGINEERING INSTITUTE MATERIAL IS FURNISHED ON AN "AS-IS" BASIS. CARNEGIE MELLON UNIVERSITY MAKES NO WARRANTIES OF ANY KIND, EITHER EXPRESSED OR IMPLIED, AS TO ANY MATTER INCLUDING, BUT NOT LIMITED TO, WARRANTY OF FITNESS FOR PURPOSE OR MERCHANTABILITY, EXCLUSIVITY, OR RESULTS OBTAINED FROM USE OF THE MATERIAL. CARNEGIE MELLON UNIVERSITY DOES NOT MAKE ANY WARRANTY OF ANY KIND WITH RESPECT TO FREEDOM FROM PATENT, TRADEMARK, OR COPYRIGHT INFRINGEMENT.
# Licensed under a BSD (SEI)-style license, please see license.txt or contact permission@sei.cmu.edu for full terms.
# [DISTRIBUTION STATEMENT A] This material has been approved for public release and unlimited distribution.  Please see Copyright notice for non-US Government use and distribution.
# This Software includes and/or makes use of Third-Party Software each subject to its own license.
# DM26-0076

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
    conf = float(argd['confidence'])
    minv,maxv = pmcanalysis.calcConfidenceInterval(g2,eq,conf)
    minp,maxp = alphaoptimize.optimizeAlphas(50, eq, max(0,conf-0.15), conf,0.01,g2, False)

    # This is human readable output
    #print(f"probability: {prob} confidence interval [{min},{max}] equation: {eq}")

    # This is csv style
    print(f"{prob},{minv},{maxv},{eq},{minp},{maxp}")
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

