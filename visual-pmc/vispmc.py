import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import networkx as nx
from netgraph import EditableGraph
import tkinter as tk
import re
import subprocess
import json
import alphaoptimize
from tkinter import filedialog
from tkinter import ttk

plot_instance = None
log = None
g2 = None

def extractGraphFromPrism(prismModel):
  tokens = re.findall(r'\w+[\']?|d+|[-][>]|[\[][\]]|[()\[\]\-+=;:.]', prismModel)
  state = '' 
  graph ={'vars':[],'transitions':[],'states':[],'transitionLabels':{}}
  transitionLabels={}
  transitions = []
  vars = []
  source_state = -1
  target_state = -1
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
        else:
          if len(transitionName) != 0:
            # FIXME: this is a temporary fix --- find a comprehensive solution
            transitionName = transitionName[0]+str(int(transitionName[1])+1)
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
         
def getAlgebraicExpression(output):
  tokens = re.findall(r'\w+[\']?|\d+|[-][>]|[[][]]|[()\[\]\-+=;{}]', output)
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

def normalizeAlgebraicEquation(eq):
  # find out if two vars are next to each other
  newstring = ""
  for i in range(0,len(eq)-1):
    newstring += eq[i]
    if eq[i].isdigit() and eq[i+1].isalpha():
      newstring += "*"
  newstring += eq[len(eq)-1]
  return newstring

def executePrism(model,graph):
  vars = graph['vars']
  params = ''
  sep=''
  for v in vars:
    params += sep+v+'=0.0:1.0'
    sep=','
  with open("prism-model.pm", "w") as file:
    file.write(model)
  with open ("prism-properties.pctl","w") as file:
    #file.write('P=? [ !(s=3 | s=5) U (s=11) ]')
    # file.write('P=? [ !(s=2 | s=5) U (s=9) ]')
    file.write(formulaField.get())

  result = subprocess.run(['prism','prism-model.pm', 'prism-properties.pctl','-param',params], shell=False,capture_output=True, text=True)
  algebraicExpression = getAlgebraicExpression(result.stdout)
  eq = normalizeAlgebraicEquation(algebraicExpression)
  min,max = alphaoptimize.optimizeAlphas(50,eq,0.2, 0.5,0.01,g2)
  intervalField.insert(0,"["+str(min)+","+str(max)+"]")

def analyzemodel():
  prismModel = txt.get('1.0',tk.END)
  graph = extractGraphFromPrism(prismModel)
  executePrism(prismModel,graph)

def updatePlot(g,transitionLabels):
    global plot_instance
    global ax
    global fig
    global canvas
    ax.clear()
    plot_instance = EditableGraph(
            g,
            node_size=2,
            node_labels=True,
            node_label_offset=0.1,
            node_label_fontdict=dict(size=20),
            edge_width=1,
            arrows=True,
            edge_labels=transitionLabels,
            ax=ax)
    canvas.draw()

def drawmodel():
  global graph
  graph = extractGraphFromPrism(txt.get('1.0',tk.END))
  updatePlot(graph['transitions'],graph['transitionLabels'])


def loadlog():
  global g2
  file_path = filedialog.askopenfilename()
  logField.insert(0,file_path)
  try:
    with open(file_path, 'r') as file:
        log  = json.load(file)
        g2 = populateTransitionObservations(graph,log)
  except FileNotFoundError:
    print("Error: The file 'data.json' was not found.")
  except json.JSONDecodeError as e:
    print(f"Error: Failed to decode JSON from the file. Details: {e}")

def zoomin():
  factor = 0.8
  xlim = ax.get_xlim()
  ylim = ax.get_ylim()
  ax.set_xlim(xlim[0] * factor, xlim[1] * factor)
  ax.set_ylim(ylim[0] * factor, ylim[1] * factor)
  canvas.draw()

def zoomout():
  factor = 1.2
  xlim = ax.get_xlim()
  ylim = ax.get_ylim()
  ax.set_xlim(xlim[0] * factor, xlim[1] * factor)
  ax.set_ylim(ylim[0] * factor, ylim[1] * factor)
  canvas.draw()

def moveLeft():
  box = ax.get_position() 

  # Shift the subplot to the right by 0.1 (fraction of figure width)
  box.x0 = box.x0 - 0.1
  box.x1 = box.x1 - 0.1

  # Set the new position
  ax.set_position(box) 
  canvas.draw()


def moveRight():
  box = ax.get_position() 

  # Shift the subplot to the right by 0.1 (fraction of figure width)
  box.x0 = box.x0 + 0.1
  box.x1 = box.x1 + 0.1

  # Set the new position
  ax.set_position(box) 
  canvas.draw()


def moveUp():
  box = ax.get_position() 

  # Shift the subplot to the right by 0.1 (fraction of figure width)
  box.y0 = box.y0 + 0.1
  box.y1 = box.y1 + 0.1

  # Set the new position
  ax.set_position(box) 
  canvas.draw()


def moveDown():
  box = ax.get_position() 

  # Shift the subplot to the right by 0.1 (fraction of figure width)
  box.y0 = box.y0 - 0.1
  box.y1 = box.y1 - 0.1

  # Set the new position
  ax.set_position(box) 
  canvas.draw()



root = tk.Tk()
root.title("Model Editor 0.2")

graph = [
    (0,1),
    (0,2)]

fig, ax = plt.subplots(figsize=(10, 10))

node_labels = {
  0 : 'zero',
  1 : 'one',
  2 : 'two'
}

edge_labels = {
  (0,1) : 'edge01',
  (0,2) : 'edge02'
}

plot_instance = EditableGraph(
    graph,
    node_size=2,
    node_labels=node_labels,
    edge_labels=edge_labels,
    node_label_offset=0.1,
    node_label_fontdict=dict(size=20),
    edge_width=1,
    arrows=True,
    ax=ax)

graphframe = tk.Frame(root, pady=10,padx=10)
graphframe.pack(side=tk.RIGHT,fill=tk.BOTH)

canvas = FigureCanvasTkAgg(fig, master=graphframe)
canvas.draw()
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

zoomFrame = tk.Frame(graphframe, pady=5,padx=5)
zoomFrame.pack(fill=tk.X)

zoomInButton = tk.Button(zoomFrame, text="Zoom In", command=zoomin)
zoomInButton.pack(side=tk.RIGHT,padx=10)
zoomOutButton = tk.Button(zoomFrame, text="Zoom Out", command=zoomout)
zoomOutButton.pack(side=tk.RIGHT,padx=10)

rightButton = tk.Button(zoomFrame, text="Right", command=moveLeft)
rightButton.pack(side=tk.RIGHT,padx=10)
leftButton = tk.Button(zoomFrame, text="Left", command=moveRight)
leftButton.pack(side=tk.RIGHT, padx=10)

upButton = tk.Button(zoomFrame, text = "Up", command=moveUp)
upButton.pack(side=tk.RIGHT, padx=10)
downButton = tk.Button(zoomFrame, text="Down", command=moveDown)
downButton.pack(side=tk.RIGHT, padx=10)


frame = tk.Frame(root, pady=10, padx=10)
frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
txt = tk.Text(frame, wrap=tk.WORD, undo=True, padx=5, pady=5, fg='black', bg='white', font='Calibri 10')
txt.pack(fill=tk.BOTH, expand=True)
scrollbar = tk.Scrollbar(txt, command=txt.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
txt.config(yscrollcommand=scrollbar.set)

fieldsFrame = tk.Frame(frame,pady=10)
fieldsFrame.pack(fill=tk.X)
tk.Label(fieldsFrame, text="Formula: ").grid(row=0, column=0, padx=10,pady=5)
tk.Label(fieldsFrame, text="Log: ").grid(row=1, column=0,padx=10,pady=5)
tk.Label(fieldsFrame, text="Interval: ").grid(row=2,column=0, padx=10,pady=5)

formulaField = tk.Entry(fieldsFrame,width=50)
logField = tk.Entry(fieldsFrame,width=50)
intervalField = tk.Entry(fieldsFrame,width=50)

formulaField.grid(row=0, column=1,padx=10, pady=5)
logField.grid(row=1,column=1,padx=10,pady=5)
intervalField.grid(row=2,column=1,padx=10,pady=5)

buttonFrame = tk.Frame(frame,pady=10)
buttonFrame.pack(fill=tk.X)
drawButton = tk.Button(buttonFrame, text="Draw",command=drawmodel)
drawButton.pack(side=tk.RIGHT,padx=5)
analyzeButton = tk.Button(buttonFrame, text="Analyze", command = analyzemodel)
analyzeButton.pack(side=tk.RIGHT, padx=5)
loadLogButton = tk.Button(buttonFrame, text="Load Log",command=loadlog)
loadLogButton.pack(side=tk.RIGHT,padx=5)


root.mainloop()

