import re
import json


# This should return a list of lists. Each internal list represent the variables (or constants) that multiple together to create each product
# the list of the products are supposed to be added together
# e.g., (a*b)+(c*d) -> [[{'sign': -1/1, 'name':'a'},{'sign': -1/1, 'name':'b'}],
#                      [{'sign': -1/1, 'name':'c'},{'sign': -1/1, 'name':'d'}]]
# It is worth noting that factors over the whole sum could be applied in the equation:
# e.g., ((a*b)+(c*d))/16 -- However this only happens if we have precalculated transition probabilities which we will not have
def getSumOfProducts(equation):
    tokens = re.findall(r'[A-Za-z0-9]+|\*|\+|\-|\(|\)', equation)
    #print(f"tokens: {tokens}")
    sumprods = []
    prod=[]
    var = ""
    sign = 1
    for token in tokens:
        if token == '(' or token == ')':
            continue # just skip we don't expect complex equations
        if token == '-' or token == '+':
            if len(var) != 0:
                prod.append({'sign':sign, 'name':var})
                var = ""
                sumprods.append(prod)
                prod=[]
            if token == '-':
                sign = -1 # for the next product
            elif token == '+':
                sign = 1 # for the next product
        elif token == '*':
            if len(var) != 0:
                prod.append({'sign':sign, 'name':var})
                var =""
        else:
            var = token
    if len(var) != 0:
        prod.append({'sign':sign, 'name':var})
    if len(prod) != 0:
        sumprods.append(prod)
    return sumprods

def getAlgebraicExpression(output):
  tokens = re.findall(r'\w+[\']?|\d+|[-][>]|\[\]|[()\[\]\-+=;{}]', output)
  state = '' 
  result =''
  for s in tokens:
    if state == '':
      if s == "Result":
        state = 'result-row'
    elif state == 'result-row':
      if s == '{':
        state = 'result'
    elif state == 'result':
      if s != '}':
        result += s
      else:
        state = ''
  return result

def normalizeAlgebraicEquation(eq):
  # find out if two vars are next to each other
  newstring = ""
  for i in range(0,len(eq)-1):
    newstring += eq[i]
    if eq[i].isdigit() and eq[i+1].isalpha(): # variable followed by variable
      newstring += "*"
    if eq[i].isdigit() and eq[i+1] == "(": # variable followed by opening parenthesis
      newstring += "*"
    if eq[i] == ")" and eq[i+1].isalpha(): # closing parenthesis followed by variable
      newstring += "*"
  newstring += eq[len(eq)-1]
  return newstring


def extractGraphFromPrism(prismModel):
  tokens = re.findall(r'\w+[\']?|d+|[-][>]|[\[][\]]|[()\[\]\-+=;:.]', prismModel)
  state = '' 
  graph ={'vars':[],'transitions':[],'states':[],'transitionLabels':{}}
  transitionLabels={}
  transitions = []
  vars = []
  source_state = -1
  target_state = -1
  largestTransitionVarNumber=0
  transitionName=''
  prevtoken=''
  prev1token=''
  for s in tokens:
    if state == '':
      if s == "[]" :
        state = 'start-transition'
      elif s == 'const':
        state = 'var-start'
    elif state == 'var-start':
      state = 'next-var-name'
    elif state == 'next-var-name':
      state = ''
      vars.append(s)
    elif state == 'start-transition':
      if s == "=":
        state = 'source-state'
    elif state == 'source-state':
       source_state = int(s)
       gstate = {'name':'','numObservations':0,'oneMinusAlpha':0,'transitions':[]}
       state = 'next-target-state'
    elif state == 'next-target-state':
      if s ==':':
        if prev1token != "-":
          transitionName = prevtoken
          # This is limited to variable names with letters followed by numbers
          varNumber = int(re.findall(r'\d+',transitionName)[0])
          if varNumber > largestTransitionVarNumber:
            largestTransitionVarNumber = varNumber
        else:
          if len(transitionName) != 0:
            # This is limited to variable names with letters followed by numbers
            transitionName = re.findall(r'[a-zA-Z]+',transitionName)[0]+str(largestTransitionVarNumber+1)
          else:
            transitionName =''
      elif s == '=':
        state = 'target-state'
      elif s == ';':
         graph['states'].append(gstate)
         state = ''
    elif state == 'target-state':
      target_state = int(s)
      transitions.append((source_state,target_state))
      gstate['transitions'].append({'source':source_state,'target':target_state,'name':transitionName,'numObservations':0,'interval':{'left':0,'right':0}})
      transitionLabels[(source_state,target_state)] = transitionName
      state = 'next-target-state'
    prev1token = prevtoken
    prevtoken = s
  graph['transitions'] = transitions
  graph['vars'] = vars
  graph['transitionLabels'] = transitionLabels

  for gstate in graph['states']:
    stateName = gstate['name']
    i=1
    for transition in gstate['transitions']:
      if transition['name'] != '':
        stateName = transition['name'][0]
        gstate['name']=stateName
      else:
        transition['name'] = stateName + str(i)
      i += 1

  return graph

def getUniqueTransitionTemplateFromTarget(g, target):
  unique = None
  for t in g:
    if t['transitionTarget'] == target:
      if unique != None:
        # This is not unique return None
        return None
      else:
        unique = t
  return unique


def createTemplate(filename,graph):
  nexttrans = 1
  transnum = 0
  jsonTemplate = []
  for transition, label in graph["transitionLabels"].items():
    if label == "1":
      t = getUniqueTransitionTemplateFromTarget(jsonTemplate,transition[0])
      if t != None:
        transnum = t['transition_number']
      else:
        transnum = nexttrans
        nexttrans += 1
    else:
      transnum = nexttrans
      nexttrans += 1
    jsonTemplate.append({
      "name": label,
      "transition_number": transnum,
      "transitionSource": transition[0],
      "transitionTarget" : transition[1],
      "numObservations" : 0
    })

  with open(filename, "w") as file:
    json.dump(jsonTemplate, file, indent=4)

def getObservations(tnumber,obsfile):
    for o in obsfile:
        if o["transition_number"] == tnumber:
            return o["count"]
    return 0

def addTransitionObservations(templatefile, observationsfile, replace):
  try:
    with open(templatefile, 'r') as file:
      transfile  = json.load(file)
  except FileNotFoundError:
    print("Error: The file  trans.json' was not found.")
    exit(1)
  except json.JSONDecodeError as e:
    print(f"Error: Failed to decode JSON from the trans file. Details: {e}")
    exit(1)

  try:
    with open(observationsfile,'r') as file1:
      obsfile = json.load(file1)
  except FileNotFoundError:
    print(f"Error: The file '{observationsfile}' was not found.")
    exit(1)
  except json.JSONDecodeError as e:
    print(f"Error: Failed to decode JSON from the obs file. Details: {e}")
    exit(1)

  for t in transfile:
    n = getObservations(t["transition_number"],obsfile)
    if replace:
      t["numObservations"] = n
    else:
      t["numObservations"] += n

  try:
    with open(templatefile,"w") as file:
      json.dump(transfile,file)
  except FileNotFoundError:
    print("error writing file")

def getTransitionNumObservations(src,tgt,log):
  for t in log:
    if t["transitionSource"] == src and t["transitionTarget"] == tgt:
      return t['name'],t["numObservations"]
  return '',0

def populateTransitionObservations(graph,log):
  states2 = []
  for state in graph['states']:
    numobs = 0
    n=''
    for transition in state["transitions"]:
      n, tobs = getTransitionNumObservations(transition["source"],
                                          transition["target"],
                                          log)
      transition["numObservations"] = tobs
      transition['name'] = n
      numobs += tobs
    state["numObservations"] = numobs
    if numobs != 0:
      states2.append(state)
  return states2

###############
# for testing
###############
if __name__ == "__main__":
    equation = "(r1*q1)-r1+1"
    print(f"equation: {equation}")
    sop = getSumOfProducts(equation)
    print(f"SOP: {sop}")
