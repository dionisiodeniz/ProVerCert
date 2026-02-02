import numpy as np
import scipy.optimize as opt

varnum = {
'x1':0,
'x2':1,
'x3':2,
'y1':3,
'y2':4,
'y3':5,
'z1':6,
'z2':7,
'z3':8,
'k1':9,
'k2':10,
'w1':11,
'w2':12}
bounds=[
(0.5453245881279799,0.59963354826346),
(0.0,0.0019332785742209935),
(0.4000339919599058,0.4543375450063819),
(0.3745633334944272,0.43295123182480955),
(0.5670487681751905,0.6254366665055728),
(0.0,0.0010230131869179272),
(0.18798390453173627,0.33584372838284593),
(0.0,0.011536883651676285),
(0.6627631957169993,0.8108559683277463),
(0.9781819572512912,1.0),
(0.0,0.021818042748708636),
(0.9973109905843301,1.0),
(0.0,0.002689009415669742)]
def maxPathEq(x):
	return -((-160*x[varnum['w1']]*x[varnum['y2']]*x[varnum['x1']]-160*x[varnum['w1']]*x[varnum['y2']]*x[varnum['x2']]+77*x[varnum['k1']]*x[varnum['z1']]*x[varnum['y1']]+160*x[varnum['y2']]*x[varnum['x1']]-77*x[varnum['z1']]*x[varnum['y1']]-77*x[varnum['z2']]*x[varnum['y1']]+160*x[varnum['w1']]*x[varnum['y2']]+160*x[varnum['y1']])/160)
def minPathEq(x):
	return (-160*x[varnum['w1']]*x[varnum['y2']]*x[varnum['x1']]-160*x[varnum['w1']]*x[varnum['y2']]*x[varnum['x2']]+77*x[varnum['k1']]*x[varnum['z1']]*x[varnum['y1']]+160*x[varnum['y2']]*x[varnum['x1']]-77*x[varnum['z1']]*x[varnum['y1']]-77*x[varnum['z2']]*x[varnum['y1']]+160*x[varnum['w1']]*x[varnum['y2']]+160*x[varnum['y1']])/160
def c0(x):
	return x[varnum['x1']]+x[varnum['x2']]+x[varnum['x3']]- 1
def c1(x):
	return x[varnum['y1']]+x[varnum['y2']]+x[varnum['y3']]- 1
def c2(x):
	return x[varnum['z1']]+x[varnum['z2']]+x[varnum['z3']]- 1
def c3(x):
	return x[varnum['k1']]+x[varnum['k2']]- 1
def c4(x):
	return x[varnum['w1']]+x[varnum['w2']]- 1

cons = ({'type': 'eq', 'fun': c0},
{'type': 'eq', 'fun': c1},
{'type': 'eq', 'fun': c2},
{'type': 'eq', 'fun': c3},
{'type': 'eq', 'fun': c4})
minres = opt.shgo(minPathEq, bounds, n=150, constraints=cons)
maxres = opt.shgo(maxPathEq, bounds, n=150, constraints=cons)
print('ok:',minres['fun'],',',abs(maxres['fun']))