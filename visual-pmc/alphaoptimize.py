# ProVer-Cert Source Code
# Copyright 2026 Carnegie Mellon University.
# NO WARRANTY. THIS CARNEGIE MELLON UNIVERSITY AND SOFTWARE ENGINEERING INSTITUTE MATERIAL IS FURNISHED ON AN "AS-IS" BASIS. CARNEGIE MELLON UNIVERSITY MAKES NO WARRANTIES OF ANY KIND, EITHER EXPRESSED OR IMPLIED, AS TO ANY MATTER INCLUDING, BUT NOT LIMITED TO, WARRANTY OF FITNESS FOR PURPOSE OR MERCHANTABILITY, EXCLUSIVITY, OR RESULTS OBTAINED FROM USE OF THE MATERIAL. CARNEGIE MELLON UNIVERSITY DOES NOT MAKE ANY WARRANTY OF ANY KIND WITH RESPECT TO FREEDOM FROM PATENT, TRADEMARK, OR COPYRIGHT INFRINGEMENT.
# Licensed under a BSD (SEI)-style license, please see license.txt or contact permission@sei.cmu.edu for full terms.
# [DISTRIBUTION STATEMENT A] This material has been approved for public release and unlimited distribution.  Please see Copyright notice for non-US Government use and distribution.
# This Software includes and/or makes use of Third-Party Software each subject to its own license.
# DM26-0076

import math
import re
import sys
import scipy.optimize as opt
import random


def calculateZscore(aQuantile):
    zero = 0.0
    one = 1.0
    half = 0.5
    split1 = 0.425
    split2 = 5.0
    const1 = 0.180625
    const2 = 1.6

	#coefficients for p close to 0.5 
    a = [ 3.3871327179, 5.0434271938e+01, 1.5929113202e+02, 5.9109374720e+01 ]
    b = [ 0.0, 1.7895169469e+01, 7.8757757664e+01, 6.72E+01 ]

	#hash sum ab 32.3184577772 
	# coefficients for p not close to 0, 0.5 or 1. 
    c = [ 1.4234372777e+00, 2.7568153900e+00, 1.3067284816e+00, 1.7023821103e-01 ]
    d = [ 0.0, 7.3700164250e-01, 1.2021132975e-01 ]

	# hash sum cd 15.7614929821
    # coefficients for p near 0 or 1.
    e = [ 6.6579051150e+00, 3.0812263860e+00, 4.2868294337e-01, 1.7337203997e-02 ]
    f = [ 0.0, 2.4197894225e-01, 1.2258202635e-02 ]

    # hash sum ef 19.4052910204
    q =0.0
    r = 0.0
    ret = 0.0

    q = aQuantile - half
    if abs(q) <= split1:
        r = const1 - q * q
        ret = q * (((a[3] * r + a[2]) * r + a[1]) * r + a[0]) / (((b[3] * r + b[2]) * r + b[1]) * r + one)
        return ret		
	# else 
    if q < zero:
        r = aQuantile
    else:
        r = one - aQuantile
    if r <= zero:
        return zero
		
    r = math.sqrt(-math.log(r))
    if r <= split2:
        r = r - const2
        ret = (((c[3] * r + c[2]) * r + c[1]) * r + c[0]) / ((d[2] * r + d[1]) * r + one)
    else:
        r = r - split2
        ret = (((e[3] * r + e[2]) * r + e[1]) * r + e[0]) / ((f[2] * r + f[1]) * r + one)
    if q < zero:
        ret = -ret
    return ret

# Wilson Score Interval:
# Edwin B. Wilson. "Probable Inference, the Law of Succession, and Statistical Inference". 
# Journal of the American Statistical Association. Vol 22, Num 158 pp 209-212.1927.
def computeWilsonInterval(confidence, parameter, observations): 
    alpha = 1 - confidence
    zscore = calculateZscore(1.0-(alpha / 2.0))
    #left is always zero
    left = 0.0
    right = zscore * zscore /(observations + zscore * zscore)

    return left, right

def computeInterval(confidence, parameter, observations): 
    alpha = 1 - confidence
	#the quantile will be = 1-(alpha/2)
    zscore= calculateZscore(1.0 - (alpha / 2.0))

    firstpart = parameter + (zscore*zscore)/(2.0*observations)
    secondtpart = zscore*math.sqrt( ( parameter*(1.0-parameter) + (zscore*zscore)/(4.0*observations))/observations )
    denom = 1.0+(zscore*zscore)/observations

    left = (firstpart - secondtpart)/denom
    right = (firstpart + secondtpart)/denom

    return left, right

# calculate the probability given:
# eq: equation 
# states with number of observations
def _replace_transition_names(equation, replacements):
    result = equation
    for name in sorted(replacements, key=len, reverse=True):
        pattern = rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])"
        result = re.sub(pattern, replacements[name], result)
    return result


def _contains_transition_name(equation, name):
    pattern = rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])"
    return re.search(pattern, equation) is not None


# calculate the probability given:
# eq: equation
# states with number of observations
def calculateProbability(eq, states):
    transitionProbabilities = {}
    for state in states:
        for transition in state["transitions"]:
            if transition["numObservations"] == 0 or state["numObservations"] == 0:
                transitionProbabilities[transition["name"]] = 0
            else:
                transitionProbabilities[transition["name"]] = (
                    transition["numObservations"] / state["numObservations"]
                )

    replacements = {
        name: f"transitionProbabilities[{name!r}]"
        for name in transitionProbabilities
        if name and not name[0].isdigit()
    }
    probEquation = _replace_transition_names(eq, replacements)
    return eval(probEquation)


def _feasible_state_point(state_bounds):
    lower_sum = sum(left for left, _ in state_bounds)
    upper_sum = sum(right for _, right in state_bounds)
    tolerance = 1e-10

    if lower_sum > 1.0 + tolerance or upper_sum < 1.0 - tolerance:
        raise ValueError(
            "Transition confidence intervals do not contain probabilities "
            f"that sum to one: lower sum={lower_sum}, upper sum={upper_sum}"
        )

    capacity = upper_sum - lower_sum
    if capacity <= tolerance:
        return [left for left, _ in state_bounds]

    fraction = (1.0 - lower_sum) / capacity
    return [
        left + fraction * (right - left)
        for left, right in state_bounds
    ]


def _check_optimization_result(result, constraints, objective_name):
    if not result.success:
        raise RuntimeError(
            f"{objective_name} optimization failed: {result.message}"
        )

    max_constraint_error = max(
        (abs(constraint["fun"](result.x)) for constraint in constraints),
        default=0.0,
    )
    if max_constraint_error > 1e-7:
        raise RuntimeError(
            f"{objective_name} optimization returned an infeasible result; "
            f"maximum constraint error is {max_constraint_error}"
        )


# e.g. req = (-160*w1*y2*x1-160*w1*y2*x2+77*k1*z1*y1+160*y2*x1-77*z1*y1-77*z2*y1+160*w1*y2+160*y1)/160"
# states=[{name: '', numObservations: 0, oneMinusAlpha:0,transitions:[{name:'', numObservations: 0, interval:{left:0,right:0}}]}]
def optimize(req, states):
    equation_names = {
        transition["name"]
        for state in states
        for transition in state["transitions"]
        if transition["name"]
        and not transition["name"][0].isdigit()
        and _contains_transition_name(req, transition["name"])
    }
    active_states = [
        state for state in states
        if any(
            transition["name"] in equation_names
            for transition in state["transitions"]
        )
    ]

    if not active_states:
        value = float(eval(req, {"__builtins__": {}}, {}))
        return value, value

    bounds = []
    initial_point = []
    constraints = []
    transition_indexes = {}

    for state in active_states:
        state_indexes = []
        state_bounds = []
        for transition in state["transitions"]:
            name = transition["name"]
            index = len(bounds)
            state_indexes.append(index)
            interval = transition["interval"]
            transition_bounds = (
                float(interval["left"]),
                float(interval["right"]),
            )
            if transition_bounds[0] > transition_bounds[1]:
                raise ValueError(
                    f"Invalid interval for transition {name}: "
                    f"{transition_bounds}"
                )
            bounds.append(transition_bounds)
            state_bounds.append(transition_bounds)

            if name and not name[0].isdigit():
                if name in transition_indexes:
                    raise ValueError(
                        f"Transition parameter name {name!r} is not unique"
                    )
                transition_indexes[name] = index

        initial_point.extend(_feasible_state_point(state_bounds))
        indexes = tuple(state_indexes)
        constraints.append({
            "type": "eq",
            "fun": lambda x, indexes=indexes: (
                sum(x[index] for index in indexes) - 1.0
            ),
        })

    replacements = {
        name: f"x[{index}]"
        for name, index in transition_indexes.items()
        if name in equation_names
    }
    objective_expression = _replace_transition_names(req, replacements)
    objective_code = compile(
        objective_expression,
        "<probability equation>",
        "eval",
    )

    def objective(x):
        return float(eval(objective_code, {"__builtins__": {}}, {"x": x}))

    solver_options = {"ftol": 1e-12, "maxiter": 1000}
    minres = opt.minimize(
        objective,
        initial_point,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options=solver_options,
    )
    maxres = opt.minimize(
        lambda x: -objective(x),
        initial_point,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options=solver_options,
    )

    _check_optimization_result(minres, constraints, "Minimum")
    _check_optimization_result(maxres, constraints, "Maximum")

    return float(minres.fun), float(-maxres.fun)


def hillClimbing(alphas):
    idx1 = random.randrange(len(alphas))
    idx2 = idx1
    while idx1 == idx2:
        idx2 = random.randrange(len(alphas))
    
    delta = 0.9 + random.random() / 2.5
    while alphas[idx1]['oneMinusAlpha'] * delta > 1.0 or alphas[idx2]['oneMinusAlpha'] / delta > 1.0:
        delta = 0.9 + random.random() / 2.5
    
    alphas[idx1]['oneMinusAlpha'] *= delta
    alphas[idx2]['oneMinusAlpha'] /= delta

# req           : string with algebraic equation
# oneMinusBeta  : lowerbound of confidence interval targeted
# upperBound    : upper bound of confidence interval targeted
# step          : step increment from lower to upper bound
# states        : [{name: '', numObservations: 0, oneMinusAlpha:0,transitions:[{name:'', numObservations: 0, interval:{left:0,right:0}}]}]
#
# The result will be new 'oneMinusAlpha in each state and each transition to maximize the confidence interval
#      These results are in the same input data structure
def optimizeAlphas(maxIterations, req, oneMinusBeta, upperBound,step,states,SmoothZeroFreq):
    lOneMinusBeta = oneMinusBeta
    bestWidth = sys.float_info.max
    bestMin=sys.float_info.max
    bestMax=sys.float_info.min

    while lOneMinusBeta <= upperBound + 0.00002:
        for state in states:
            state['oneMinusAlpha'] = math.pow(lOneMinusBeta, 1.0/len(states))

        bestWidth = sys.float_info.max
        bestMin=sys.float_info.max
        bestMax=sys.float_info.min
        epsilon = 0.005
        for i in range(maxIterations):
            for state in states:
                for transition in state['transitions']:
                    # protect against zero observations
                    #if transition['numObservations'] == 0 or state['numObservations'] == 0:
                    # Dio: we will try only to not calculate the interval if the state has no observations
                    if state['numObservations'] == 0:
                        left = 0.0
                        right = 1.0
                    # elif transition['numObservations'] == 0:
                    #     # Use Wilson Score Interval:
                    #     # Edwin B. Wilson. "Probable Inference, the Law of Succession, and Statistical Inference". 
                    #     # Journal of the American Statistical Association. Vol 22, Num 158 pp 209-212.1927.
                    #     left,right = computeWilsonInterval(state['oneMinusAlpha'],
                    #                             transition['numObservations'] / state['numObservations'],
                    #                             state['numObservations'])
                    else:
                        if SmoothZeroFreq:
                            # Use Laplace Smoothing if we have any zeroFrequencyTransition
                            # Christopher D. Manning, Prabhakar Raghavan, andHinrich Schutze
                            # Introduction to Information Retrieval
                            # Cambridge University Press. 2008.
                            # Chapter 13: Text classification and Naive Bayes 
                            # (section on Naive Bayes and multinomial models and Laplace Smoothing)
                            left,right = computeInterval(state['oneMinusAlpha'],
                                                (transition['numObservations']+1) / (state['numObservations'] + len(state)),
                                                (state['numObservations']+len(state)))
                        else:
                            left,right = computeInterval(state['oneMinusAlpha'],
                                                transition['numObservations'] / state['numObservations'],
                                                state['numObservations'])
                    # if transition['name'] in req:
                    #     print(f"computeInterval: transition({transition['name']}) left({left}) right({right})")
                    if left <0 :
                        left = 0
                    if right >1 :
                        right = 1
                    transition['interval']['left'] = left
                    transition['interval']['right'] = right
            min = 0.0
            max = 1.0 
            width = max-min
            prevMin = min
            prevMax = max
            min, max = optimize(req,states)
            #print(f"\t optimize: min({min}) max({max}) width({(max-min)})")
            # if max-min == 0:
            #     print(f"\t width zero: min:{min}, max:{max}")
            if max == 0:
                min = prevMin
                max = prevMax
            width = max - min

            if width >= bestWidth - epsilon:
                iterationsWithoutImprovement +=1
            else:
                iterationsWithoutImprovement = 0
            if bestWidth > width:
                bestWidth = width
                bestMin = min
                bestMax = max

            hillClimbing(states)

        #print(f"oneMinusBeta:{lOneMinusBeta}, bestMin:{bestMin}, bestMax:{bestMax} (1-alpha):{lOneMinusBeta}")
        lOneMinusBeta += step
    return bestMin,bestMax

###############
# for testing
###############
if __name__ == "__main__":
    req = "(-160*w1*y2*x1-160*w1*y2*x2+77*k1*z1*y1+160*y2*x1-77*z1*y1-77*z2*y1+160*w1*y2+160*y1)/160"
    states = [
        {
            'name':'x',
            'numObservations':5963,
            'oneMinusAlpha':0,
            'transitions': [
                {
                    'name':'x1',
                    'numObservations':3414,
                    'interval':{
                        'left':0.5453245881279799,
                        'right':0.59963354826346
                    }
                },
                {
                    'name':'x2',
                    'numObservations':2,
                    'interval':{
                        'left':0.0,
                        'right':0.0019332785742209935
                    }
                },
                {
                    'name':'x3',
                    'numObservations':2547,
                    'interval':{
                        'left':0.4000339919599058,
                        'right':0.4543375450063819
                    }
                }
            ]
        },
        {
            'name':'y',
            'numObservations':10000,
            'oneMinusAlpha':0,
            'transitions': [
                {
                    'name':'y1',
                    'numObservations':4037,
                    'interval':{
                        'left':0.3745633334944272,
                        'right':0.43295123182480955
                    }
                },
                {
                    'name':'y2',
                    'numObservations':5963,
                    'interval':{
                        'left':0.5670487681751905,
                        'right':0.6254366665055728
                    }
                },
                {
                    'name':'y3',
                    'numObservations':0,
                    'interval':{
                        'left':0.0,
                        'right':0.0010230131869179272
                    }
                }
            ]
        },
        {
            'name':'z',
            'numObservations':1560,
            'oneMinusAlpha':0,
            'transitions': [
                {
                    'name':'z1',
                    'numObservations':407,
                    'interval':{
                        'left':0.18798390453173627,
                        'right':0.33584372838284593
                    }
                },
                {
                    'name':'z2',
                    'numObservations':2,
                    'interval':{
                        'left':0.0,
                        'right':0.011536883651676285
                    }
                },
                {
                    'name':'z3',
                    'numObservations':1151,
                    'interval':{
                        'left':0.6627631957169993,
                        'right':0.8108559683277463
                    }
                }
            ]
        },
        {
            'name':'k',
            'numObservations':407,
            'oneMinusAlpha':0,
            'transitions': [
                {
                    'name':'k1',
                    'numObservations':407,
                    'interval':{
                        'left':0.9781819572512912,
                        'right':1.0
                    }
                },
                {
                    'name':'k2',
                    'numObservations':0,
                    'interval':{
                        'left':0.0,
                        'right':0.021818042748708636
                    }
                }
            ]
        },
        {
            'name':'w',
            'numObservations':2547,
            'oneMinusAlpha':0,
            'transitions': [
                {
                    'name':'w1',
                    'numObservations':2546,
                    'interval':{
                        'left':0.9973109905843301,
                        'right':1.0
                    }
                },
                {
                    'name':'w2',
                    'numObservations':1,
                    'interval':{
                        'left':0.0,
                        'right':0.002689009415669742
                    }
                }
            ]
        }
    ]

    states1 = [
        {
            'name':'x',
            'numObservations':5963,
            'oneMinusAlpha':0,
            'transitions': [
                {
                    'name':'x1',
                    'numObservations':3414,
                    'interval':{
                        'left':0.0,
                        'right':0.0
                    }
                },
                {
                    'name':'x2',
                    'numObservations':2,
                    'interval':{
                        'left':0.0,
                        'right':0.0
                    }
                },
                {
                    'name':'x3',
                    'numObservations':2547,
                    'interval':{
                        'left':0.0,
                        'right':0.0
                    }
                }
            ]
        },
        {
            'name':'y',
            'numObservations':10000,
            'oneMinusAlpha':0,
            'transitions': [
                {
                    'name':'y1',
                    'numObservations':4037,
                    'interval':{
                        'left':0.0,
                        'right':0.0
                    }
                },
                {
                    'name':'y2',
                    'numObservations':5963,
                    'interval':{
                        'left':0.0,
                        'right':0.0
                    }
                },
                {
                    'name':'y3',
                    'numObservations':0,
                    'interval':{
                        'left':0.0,
                        'right':0.0
                    }
                }
            ]
        },
        {
            'name':'z',
            'numObservations':1560,
            'oneMinusAlpha':0,
            'transitions': [
                {
                    'name':'z1',
                    'numObservations':407,
                    'interval':{
                        'left':0.0,
                        'right':0.0
                    }
                },
                {
                    'name':'z2',
                    'numObservations':2,
                    'interval':{
                        'left':0.0,
                        'right':0.0
                    }
                },
                {
                    'name':'z3',
                    'numObservations':1151,
                    'interval':{
                        'left':0.0,
                        'right':0.0
                    }
                }
            ]
        },
        {
            'name':'k',
            'numObservations':407,
            'oneMinusAlpha':0,
            'transitions': [
                {
                    'name':'k1',
                    'numObservations':407,
                    'interval':{
                        'left':0.0,
                        'right':0.0
                    }
                },
                {
                    'name':'k2',
                    'numObservations':0,
                    'interval':{
                        'left':0.0,
                        'right':0.0
                    }
                }
            ]
        },
        {
            'name':'w',
            'numObservations':2547,
            'oneMinusAlpha':0,
            'transitions': [
                {
                    'name':'w1',
                    'numObservations':2546,
                    'interval':{
                        'left':0.0,
                        'right':0.0
                    }
                },
                {
                    'name':'w2',
                    'numObservations':1,
                    'interval':{
                        'left':0.0,
                        'right':0.0
                    }
                }
            ]
        }
    ]

    #optimize(req ,states)
    # 0.85 0.99 0.01
    optimizeAlphas(50, req, 0.85, 0.99,0.01,states1, False)
