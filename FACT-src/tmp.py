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
(0.47441785196123837,0.6702719936257919),
(0.0,0.007793565534808211),
(0.32940319472533536,0.5252378736964803),
(0.36578249696495013,0.44176658067904584),
(0.5582334193209543,0.6342175030350499),
(0.0,0.001464154482104635),
(0.10955194474310938,0.41644965123899946),
(0.0,0.02622214234312139),
(0.5820392475716515,0.889417610043999),
(0.9571040576319348,1.0),
(0.0,0.042895942368065154),
(0.9903469510258501,1.0),
(0.0,0.009653048974149918)]
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