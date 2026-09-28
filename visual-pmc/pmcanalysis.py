import subprocess
import pmcparser
import math
import sys
import alphaoptimize

def pmcprismanalysis(model,graph,pmcformula):
    vars = graph['vars']
    params = ''
    sep=''
    for v in vars:
        params += sep+v+'=0.0:1.0'
        sep=','
    with open("prism-model.pm", "w") as file:
        file.write(model)
    with open ("prism-properties.pctl","w") as file:
        file.write(pmcformula)

    result = subprocess.run(['prism','prism-model.pm', 'prism-properties.pctl','-param',params], shell=False,capture_output=True, text=True)
    #print(f"prism result: {result}")

    # Old algebraic equation for prism 4.8X
    #algebraicExpression = pmcparser.getAlgebraicExpression(result.stdout)
    
    # new algebraic expression parsing for prism 4.10
    algebraicExpression = pmcparser.extract_algebraic_equation(result.stdout)
    #print(f"Algebraic Expression: {algebraicExpression}")
    
    # prism 4.10 does not need normalization
    # eq = pmcparser.normalizeAlgebraicEquation(algebraicExpression)
    return algebraicExpression

def isNumber(str):
  try:
    float(str)
    return True
  except ValueError:
    return False

def getMean(varOrLiteral,varMeans):
  if (isNumber(varOrLiteral)):
    return 1
  else:
    return varMeans[varOrLiteral]
  
# if is a number it should be always 1 and we return 1
# so that the frequency will be 1/1
def getNumSamples(varOrLiteral,varNumSamples):
  if isNumber(varOrLiteral):
    return 1
  else:
    return varNumSamples[varOrLiteral]

# Calculate the variance of the product of n factors
# parameters:
# varMeans   [ name: mean]
# varNumSamples [ name: numsamples]
# product x*y*z*... as [{'sign': 1/-1, 'name':'x'},{'sign': 1/-1, 'name':'y'},{'sign': 1/-1, 'name':'z'},...]
def getVarianceOfProduct(varMeans,varNumSamples,product):
  part1= 1.0
  part2 = 1.0
  if len(product) == 1:
    if isNumber(product[0]['name']):
      part1=product[0]['sign']*float(product[0]['name'])
      part2=0
    else:
      part1 = product[0]['sign']*(getMean(product[0]['name'],varMeans)*(1-getMean(product[0]['name'],varMeans)))/getNumSamples(product[0]['name'],varNumSamples)
      part2=0
  else:
    for i in range(len(product)):
      part1 *= product[i]['sign']*((getMean(product[i]['name'],varMeans)*(1-getMean(product[i]['name'],varMeans))/getNumSamples(product[i]['name'],varNumSamples))+(getMean(product[i]['name'],varMeans)**2))
      part2 *= product[i]['sign']*(getMean(product[i]['name'],varMeans)**2)
  return part1 - part2

def getMeansNumSamples(states):
  transmeans={}
  transNsamples={}
  for state in states:
    for transition in state['transitions']:
      if transition['numObservations'] == 0 or state['numObservations'] == 0:
        transmeans[transition['name']] = 0    
      else:
        transmeans[transition['name']] = transition['numObservations'] / state['numObservations']
      transNsamples[transition['name']] = state['numObservations']
  return transmeans,transNsamples

def getSampleSizeFromProducts(products,varNumSamples):
  n=0
  for prod in products:
    p = 1.0
    for v in prod:
      p *= getNumSamples(v['name'],varNumSamples)
    n += p
  return n

def getVariance(var, varMeans,varNumSamples):
  # (p*(1-p))/n
  p = getMean(var,varMeans)
  n = getNumSamples(var,varNumSamples)
  return (p*(1-p) / n)

def getCovariance(v1,v2, varMeans, varNumSamples):
  p1 = getMean(v1,varMeans)
  p2 = getMean(v2,varMeans)
  n = getNumSamples(v1,varNumSamples)
  return -(p1*p2/n)

def hasSameSourceState(v1,v2, states):
  s1 = ""
  s2 = ""
  for state in states:
    for transition in state['transitions']:
      if transition['name'] == v1:
        s1 = transition['source']
      elif transition['name'] == v2:
        s2 = transition['source']
  return s1 == s2

def getProductOfMeansExcept(v1,v2,product1,products2, varMeans):
  p = 1
  for v11 in product1:
    if v11['name'] != v1['name'] and v11['name'] != v2['name']:
      p *= getMean(v11['name'],varMeans)
  for v22 in products2:
    if v22['name'] != v1['name'] and v22['name'] != v2['name']:
      p *= getMean(v22['name'],varMeans)
  return p

def getCovarianceOfSumOfProducts(states, varMeans,varNumSamples, products):
  cov=0
  for i in range(0,len(products)-1):
    for j in range (i+1,len(products)-1):
      for v1 in products[i]:
        cv = 0
        for v2 in products[j]:
          if v1['name'] == v2['name']:
            cv = getVariance(v1['name'],varMeans,varNumSamples)
          elif hasSameSourceState(v1,v2,states):
            cv = getCovariance(v1['name'],v2['name'],varMeans,varNumSamples)
          if cv != 0:
            #pairwise covariances
            cov += 2* cv * getProductOfMeansExcept(v1,v2,products[i],products[j], varMeans) 
  return cov

def calcConfidenceInterval(states, equation, confidence):
    transition_values = {
        transition["name"]: (
            transition["numObservations"] / state["numObservations"]
        )
        for state in states
        if state["numObservations"] > 0
        for transition in state["transitions"]
        if transition["name"] and not transition["name"][0].isdigit()
    }
    active_names = {
        name for name in transition_values
        if alphaoptimize._contains_transition_name(equation, name)
    }
    replacements = {
        name: f"transition_values[{name!r}]"
        for name in active_names
    }
    probability_expression = alphaoptimize._replace_transition_names(
        equation,
        replacements,
    )
    probability_code = compile(
        probability_expression,
        "<probability equation>",
        "eval",
    )

    def evaluate(values):
        return float(eval(
            probability_code,
            {"__builtins__": {}},
            {"transition_values": values},
        ))

    gradient_step = math.sqrt(sys.float_info.epsilon)
    gradients = {}
    for name in active_names:
        parameter = transition_values[name]
        step = gradient_step * max(1.0, abs(parameter))
        values_above = dict(transition_values)
        values_below = dict(transition_values)
        values_above[name] = parameter + step
        values_below[name] = parameter - step
        gradients[name] = (
            evaluate(values_above) - evaluate(values_below)
        ) / (2.0 * step)

    total_variance = 0.0
    for state in states:
        observations = state["numObservations"]
        if observations <= 0:
            continue

        active_transitions = [
            transition for transition in state["transitions"]
            if transition["name"] in active_names
        ]
        for first_index, first in enumerate(active_transitions):
            first_name = first["name"]
            first_probability = transition_values[first_name]
            for second_index, second in enumerate(active_transitions):
                second_name = second["name"]
                second_probability = transition_values[second_name]
                if first_index == second_index:
                    covariance = (
                        first_probability * (1.0 - first_probability)
                        / observations
                    )
                else:
                    covariance = (
                        -first_probability * second_probability / observations
                    )
                total_variance += (
                    gradients[first_name]
                    * gradients[second_name]
                    * covariance
                )

    if total_variance < -1e-12:
        raise ValueError(
            f"Calculated probability variance is negative: {total_variance}"
        )

    probability = evaluate(transition_values)
    alpha = 1.0 - confidence
    zscore = alphaoptimize.calculateZscore(1.0 - (alpha / 2.0))
    error = zscore * math.sqrt(max(0.0, total_variance))
    return max(0.0, probability - error), min(1.0, probability + error)
