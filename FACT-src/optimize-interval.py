import numpy as np
import scipy.optimize as opt

varnum = {
'x1': 0,
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
'w2':12
}

#(-160*w1*y2*x1
# -160*w1*y2*x2
# +77*k1*z1*y1
# +160*y2*x1
# -77*z1*y1
# -77*z2*y1
# +160*w1*y2
# +160*y1)/160
def minPatheq(x):
    return ((-160*x[varnum['w1']]*x[varnum['y2']]*x[varnum['x1']]
            -160*x[varnum['w1']]*x[varnum['y2']]*x[varnum['x2']]
            +77*x[varnum['k1']]*x[varnum['z1']]*x[varnum['y1']]
            +160*x[varnum['y2']]*x[varnum['x1']]
            -77*x[varnum['z1']]*x[varnum['y1']]
            -77*x[varnum['z2']]*x[varnum['y1']]
            +160*x[varnum['w1']]*x[varnum['y2']]
            +160*x[varnum['y1']])/160)

def maxPatheq(x):
    return -((-160*x[varnum['w1']]*x[varnum['y2']]*x[varnum['x1']]
            -160*x[varnum['w1']]*x[varnum['y2']]*x[varnum['x2']]
            +77*x[varnum['k1']]*x[varnum['z1']]*x[varnum['y1']]
            +160*x[varnum['y2']]*x[varnum['x1']]
            -77*x[varnum['z1']]*x[varnum['y1']]
            -77*x[varnum['z2']]*x[varnum['y1']]
            +160*x[varnum['w1']]*x[varnum['y2']]
            +160*x[varnum['y1']])/160)

#x1+x2+x3==1,
#y1+y2+y3==1,
#z1+z2+z3==1,
#k1+k2==1,
#w1+w2==1];

def xs (x):
    return x[varnum['x1']] + x[varnum['x2']] + x[varnum['x3']] - 1

def ys (x):
    return x[varnum['y1']] + x[varnum['y2']] + x[varnum['y3']] - 1

def zs (x):
    return x[varnum['z1']] + x[varnum['z2']]+x[varnum['z3']] - 1

def ks (x):
    return x[varnum['k1']] + x[varnum['k2']] - 1

def ws (x):
    return x[varnum['w1']] + x[varnum['w2']] - 1

cons = ({'type': 'eq', 'fun': xs},
        {'type': 'eq', 'fun': ys},
        {'type': 'eq', 'fun': zs},
        {'type': 'eq', 'fun': ks},
        {'type': 'eq', 'fun': ws},
        )


#0.5430191829158383<=x1<=0.6019302225071174,
#0.0<=x2<=0.0020882824829826854,
#0.39773756681830374<=x3<=0.456642741490889,
#0.38118231246871154<=y1<=0.42630623326401834,
#0.5736937667359818<=y2<=0.6188176875312885,
#0.0<=y3<=7.22858116771622E-4,
#0.21051621509332116<=z1<=0.312684452050381,
#0.0<=z2<=0.007963430595049076,
#0.6859566468870907<=z3<=0.7882861211817741,
#0.9824297505817186<=k1<=1.0,
#0.0<=k2<=0.017570249418281406,
#0.9960639826475133<=w1<=1.0,
#0.0<=w2<=0.003936017352486731,

bounds =[(0.5430191829158383,0.6019302225071174),   # x1
         (0.0,0.0020882824829826854),               # x2
         (0.39773756681830374,0.456642741490889),   # x3
         (0.38118231246871154,0.42630623326401834), # y1
         (0.5736937667359818,0.6188176875312885),   # y2
         (0.0,0.000722858116771622),                # y3
         (0.21051621509332116,0.312684452050381),   # z1
         (0.0,0.007963430595049076),                # z2
         (0.6859566468870907,0.7882861211817741),   # z3
         (0.9824297505817186,1.0),                  # k1
         (0.0,0.017570249418281406),                # k2
         (0.9960639826475133,1.0),                  # w1
         (0.0,0.003936017352486731)                 # w2
         ]

minres = opt.shgo(minPatheq, bounds, n=150, constraints=cons)
print("min fun = ",minres['fun']," res[x]=",minres['x'])

maxres = opt.shgo(maxPatheq, bounds, n=150, constraints=cons)
print("max fun = ",abs(maxres['fun'])," res[x]=",maxres['x'])
