# ProVer-Cert Source Code
# Copyright 2026 Carnegie Mellon University.
# NO WARRANTY. THIS CARNEGIE MELLON UNIVERSITY AND SOFTWARE ENGINEERING INSTITUTE MATERIAL IS FURNISHED ON AN "AS-IS" BASIS. CARNEGIE MELLON UNIVERSITY MAKES NO WARRANTIES OF ANY KIND, EITHER EXPRESSED OR IMPLIED, AS TO ANY MATTER INCLUDING, BUT NOT LIMITED TO, WARRANTY OF FITNESS FOR PURPOSE OR MERCHANTABILITY, EXCLUSIVITY, OR RESULTS OBTAINED FROM USE OF THE MATERIAL. CARNEGIE MELLON UNIVERSITY DOES NOT MAKE ANY WARRANTY OF ANY KIND WITH RESPECT TO FREEDOM FROM PATENT, TRADEMARK, OR COPYRIGHT INFRINGEMENT.
# Licensed under a BSD (SEI)-style license, please see license.txt or contact permission@sei.cmu.edu for full terms.
# [DISTRIBUTION STATEMENT A] This material has been approved for public release and unlimited distribution.  Please see Copyright notice for non-US Government use and distribution.
# This Software includes and/or makes use of Third-Party Software each subject to its own license.

# DM26-0076


import math
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import networkx as nx
from netgraph import EditableGraph
import tkinter as tk
import re
import subprocess
import json
import alphaoptimize
import pmcparser
import pmcanalysis
from tkinter import filedialog
from PIL import Image, ImageTk


plot_instance = None
log = None
g2 = None
  
def executePrism(model,graph):
  pmcformula = formulaField.get()
  eq = pmcanalysis.pmcprismanalysis(model,graph,pmcformula)
  equationField.delete(0,tk.END)
  equationField.insert(0,eq)
  print(f"Normalized equation: {eq}")
  prob = alphaoptimize.calculateProbability(eq,g2)
  probabilityField.delete(0,tk.END)
  probabilityField.insert(0,str(prob))
  alpha = float(alphaField.get())
  #min,max = alphaoptimize.optimizeAlphas(50,eq,alpha, alpha,0.01,g2) #alphaoptimize.optimizeAlphas(50,eq,0.2, 0.5,0.01,g2)
  # SmoothZeroFrequencyTransition = False
  # for state in g2:
  #     for transition in state['transitions']:
  #         if transition['numObservations'] == 0:
  #             SmoothZeroFrequencyTransition = True
  #             break
  #     if SmoothZeroFrequencyTransition:
  #         break

  #min,max = alphaoptimize.optimizeAlphas(50,eq,0.7, alpha,0.01,g2,SmoothZeroFrequencyTransition) 
  min,max = pmcanalysis.calcConfidenceInterval(g2,eq,alpha)
  intervalField.delete(0,tk.END)
  intervalField.insert(0,"["+str(min)+","+str(max)+"]")

def analyzemodel():
  prismModel = txt.get('1.0',tk.END)
  graph = pmcparser.extractGraphFromPrism(prismModel)
  executePrism(prismModel,graph)

def updatePlot(g,transitionLabels):
    global plot_instance
    global ax
    global fig
    global canvas
    ax.clear()

    # Define font properties using the axis data transformation
    font_properties = {
      'size': 12,
      'transform': ax.transData  # Forces text to scale with data zooming
    }

    plot_instance = EditableGraph(
            g,
            node_size=2,
            node_labels=True,
            node_label_offset=0.1,
            node_label_fontdict=font_properties,
            edge_width=1,
            arrows=True,
            edge_labels=transitionLabels,
            ax=ax)
    canvas.draw()

def compilemodel():
  global graph
  graph = pmcparser.extractGraphFromPrism(txt.get('1.0',tk.END))
  updatePlot(graph['transitions'],graph['transitionLabels'])

def createTemplate():
  pmcparser.createTemplate("obsTemplate.json",graph)

def populateTemplate():
  datapath = filedialog.askopenfilename(title="Observations File")
  if not datapath:
    return
  file_path = filedialog.askopenfilename(title="Log Template File")
  if not file_path:
    return
  pmcparser.addTransitionObservations(file_path,datapath, replace=True)

def loadlog():
  global g2
  file_path = filedialog.askopenfilename(title="Log File")
  logField.delete(0,tk.END)
  logField.insert(0,file_path)
  try:
    with open(file_path, 'r') as file:
        log  = json.load(file)
        g2 = pmcparser.populateTransitionObservations(graph,log)
  except FileNotFoundError:
    print("Error: The file 'data.json' was not found.")
  except json.JSONDecodeError as e:
    print(f"Error: Failed to decode JSON from the file. Details: {e}")

def loadmodel():
  global modelfilename
  file_path = filedialog.askopenfilename()
  modelfilename = file_path

  global root
  root.title(file_path)
  try:
    with open(file_path, 'r') as file:
        txt.delete("1.0", tk.END)
        txt.insert("1.0", file.read())
  except FileNotFoundError:
    print(f"Error: The file {file_path} was not found.")

def savemodel():
  global modelfilename
  if modelfilename == "" :
    modelfilename = filedialog.asksaveasfilename()  
  if modelfilename:
    with open(modelfilename, "w") as file:
      file.write(txt.get('1.0',tk.END))

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


modelfilename=""

root = tk.Tk()
root.title("Model Editor 0.2")
icon_image = Image.open("approved-icon.png")
icon_photo = ImageTk.PhotoImage(icon_image)
root.icon_photo = icon_photo 
root.wm_iconbitmap()
root.iconphoto(False, root.icon_photo)


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
tk.Label(fieldsFrame, text="1-Alpha: ").grid(row=2, column=0,padx=10,pady=5)
tk.Label(fieldsFrame, text="Equation").grid(row=3,column=0, padx=10,pady=5)
tk.Label(fieldsFrame, text="Interval: ").grid(row=4,column=0, padx=10,pady=5)
tk.Label(fieldsFrame, text="Probability: ").grid(row=5, column=0,padx=10,pady=5)

formulaField = tk.Entry(fieldsFrame,width=50)
logField = tk.Entry(fieldsFrame,width=50)
alphaField = tk.Entry(fieldsFrame, width=50)
equationField = tk.Entry(fieldsFrame, width=50)
intervalField = tk.Entry(fieldsFrame,width=50)
probabilityField = tk.Entry(fieldsFrame,width=50)
alphaField = tk.Entry(fieldsFrame, width=50)

formulaField.grid(row=0, column=1,padx=10, pady=5)
logField.grid(row=1,column=1,padx=10,pady=5)
alphaField.grid(row=2,column=1,padx=10,pady=5)
equationField.grid(row=3,column=1,padx=10,pady=5)
intervalField.grid(row=4,column=1,padx=10,pady=5)
probabilityField.grid(row=5,column=1,padx=10,pady=5)

buttonFrame = tk.Frame(frame,pady=10)
buttonFrame.pack(fill=tk.X)
buttonFrame1 = tk.Frame(frame,pady=10)
buttonFrame1.pack(fill=tk.X)
compileButton = tk.Button(buttonFrame, text="Compile",command=compilemodel)
compileButton.pack(side=tk.RIGHT,padx=5)
analyzeButton = tk.Button(buttonFrame, text="Analyze", command = analyzemodel)
analyzeButton.pack(side=tk.RIGHT, padx=5)
createTemplateButton = tk.Button(buttonFrame, text="Create Log Template", command=createTemplate)
createTemplateButton.pack(side=tk.RIGHT,padx=5)
populateTemplateButton = tk.Button(buttonFrame, text="Populate Template", command=populateTemplate)
populateTemplateButton.pack(side=tk.RIGHT, padx=5)

loadLogButton = tk.Button(buttonFrame1, text="Load Log",command=loadlog)
loadLogButton.pack(side=tk.RIGHT,padx=5)
saveModelButton = tk.Button(buttonFrame1, text="Save Model",command=savemodel)
saveModelButton.pack(side=tk.RIGHT, padx=5)
loadModelButton = tk.Button(buttonFrame1, text="Load Model", command=loadmodel)
loadModelButton.pack(side=tk.RIGHT, padx=5)


root.mainloop()

