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
