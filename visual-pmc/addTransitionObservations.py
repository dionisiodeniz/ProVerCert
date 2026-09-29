# ProVer-Cert Source Code
# Copyright 2026 Carnegie Mellon University.
# NO WARRANTY. THIS CARNEGIE MELLON UNIVERSITY AND SOFTWARE ENGINEERING INSTITUTE MATERIAL IS FURNISHED ON AN "AS-IS" BASIS. CARNEGIE MELLON UNIVERSITY MAKES NO WARRANTIES OF ANY KIND, EITHER EXPRESSED OR IMPLIED, AS TO ANY MATTER INCLUDING, BUT NOT LIMITED TO, WARRANTY OF FITNESS FOR PURPOSE OR MERCHANTABILITY, EXCLUSIVITY, OR RESULTS OBTAINED FROM USE OF THE MATERIAL. CARNEGIE MELLON UNIVERSITY DOES NOT MAKE ANY WARRANTY OF ANY KIND WITH RESPECT TO FREEDOM FROM PATENT, TRADEMARK, OR COPYRIGHT INFRINGEMENT.
# Licensed under a BSD (SEI)-style license, please see license.txt or contact permission@sei.cmu.edu for full terms.
# [DISTRIBUTION STATEMENT A] This material has been approved for public release and unlimited distribution.  Please see Copyright notice for non-US Government use and distribution.
# This Software includes and/or makes use of Third-Party Software each subject to its own license.
# DM26-0076

import sys
import json

def getObservations(tnumber,obsfile):
    for o in obsfile:
        if o["transition_number"] == tnumber:
            return o["count"]
    return 0


if len(sys.argv) != 3:
    print(" need <transitions file> <transition observations file>")
    exit(1)

try:
    with open(sys.argv[1], 'r') as file:
        transfile  = json.load(file)
except FileNotFoundError:
    print("Error: The file  trans.json' was not found.")
    exit(1)
except json.JSONDecodeError as e:
    print(f"Error: Failed to decode JSON from the trans file. Details: {e}")
    exit(1)

try:
    with open(sys.argv[2],'r') as file1:
        obsfile = json.load(file1)
except FileNotFoundError:
    print("Error: The file 'obs.json' was not found.")
    exit(1)
except json.JSONDecodeError as e:
    print(f"Error: Failed to decode JSON from the obs file. Details: {e}")
    exit(1)

for t in transfile:
    n = getObservations(t["transition_number"],obsfile)
    t["numObservations"] = n

try:
    with open(sys.argv[1],"w") as file:
        json.dump(transfile,file)
except FileNotFoundError:
    print("error writing file")
