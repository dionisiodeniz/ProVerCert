import matplotlib.pyplot as plt
import networkx as nx
from netgraph import EditableGraph
import tkinter as tk
from multiprocessing import Process
from multiprocessing.connection import Client, Listener
import threading
import time
import re
import subprocess

def extractGraphFromPrism(prismModel):
  tokens = re.findall(r'\w+[\']?|\d+|[-][>]|[[][]]|[()\[\]\-+=;]', prismModel)
  state = '' 
  graph ={'vars':[],'transitions':[]}
  transitions = []
  vars = []
  source_state = -1
  target_state = -1
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
       state = 'next-target-state'
    elif state == 'next-target-state':
      if s == '=':
        state = 'target-state'
      elif s == ';':
         state = ''
    elif state == 'target-state':
      target_state = int(s)
      transitions.append((source_state,target_state))
      state = 'next-target-state'
  graph['transitions'] = transitions
  graph['vars'] = vars
  return graph
         
def drawmodel():
  graph = extractGraphFromPrism(txt.get('1.0',tk.END))
  print(f"vars:{graph['vars']}")
  conn.send(graph['transitions'])

def executePrism(model,graph):
  vars = graph['vars']
  params = ''#'-param '
  sep=''
  for v in vars:
    params += sep+v+'=0.0:1.0'
    sep=','
  with open("prism-model.pm", "w") as file:
    file.write(model)
  with open ("prism-properties.pctl","w") as file:
    file.write('P=? [ !(s=2 | s=5) U (s=9) ]')

  print("command : prism prism-model.pm prism-properties.pctl ",params)
  result = subprocess.run(['prism','prism-model.pm', 'prism-properties.pctl','-param',params], shell=False,capture_output=True, text=True)
  print(f"stdout: {result.stdout}")

def analyzemodel():
  prismModel = txt.get('1.0',tk.END)
  graph = extractGraphFromPrism(prismModel)
  executePrism(prismModel,graph)
  
def editor():
  global conn
  global txt
  address = ('localhost',6000)
  conn = Client(address,authkey=b'secret')
  root = tk.Tk()
  root.title("Model Editor")
  root.geometry('600x400')
  frame = tk.Frame(root, pady=10, padx=10)
  frame.pack(fill=tk.BOTH, expand=True)
  txt = tk.Text(frame, wrap=tk.WORD, undo=True, padx=5, pady=5, fg='black', bg='white', font='Calibri 10')
  txt.pack(fill=tk.BOTH, expand=True)
  scrollbar = tk.Scrollbar(txt, command=txt.yview)
  scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
  txt.config(yscrollcommand=scrollbar.set)
  buttonFrame = tk.Frame(frame,pady=10)
  buttonFrame.pack(fill=tk.X)
  drawButton = tk.Button(buttonFrame, text="Draw",command=drawmodel)
  drawButton.pack(side=tk.RIGHT,padx=5)
  analyzeButton = tk.Button(buttonFrame, text="Analyze", command = analyzemodel)
  analyzeButton.pack(side=tk.RIGHT, padx=5)
  exitButton = tk.Button(buttonFrame, text="Exit",command=root.destroy)
  exitButton.pack(side=tk.RIGHT,padx=5)
  root.mainloop()

graph = [
    (0,1),
    (0,2)]

fig, ax = plt.subplots(figsize=(10, 10))


plot_instance = EditableGraph(
    graph,
    node_size=2,
    node_labels=True,
    node_label_offset=0.1,
    node_label_fontdict=dict(size=20),
    edge_width=1,
    arrows=True,
    ax=ax)

def updatePlot():
    global plot_instance
    global ax
    address = ('localhost',6000)
    listener = Listener(address,authkey=b'secret')
    conn = listener.accept()
    while True:
        g = conn.recv()
        ax.clear()
        plot_instance = EditableGraph(
            g,
            node_size=2,
            node_labels=True,
            node_label_offset=0.1,
            node_label_fontdict=dict(size=20),
            edge_width=1,
            arrows=True,
            ax=ax)
        fig.canvas.draw()

updateThread = threading.Thread(target=updatePlot)
updateThread.start()
time.sleep(1)
    
proc = Process(target=editor)
proc.start()

plt.show()

updateThread.join()
proc.join()

