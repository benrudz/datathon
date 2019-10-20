
import requests 
import json
import pprint
pp = pprint.PrettyPrinter()
import pandas as pd
import numpy as np 


file = open("output1-54AM", 'r')
lines = file.readlines()
memo = dict()

for line in lines: 
	if(line == "\n"):
		continue
	data = line.rstrip('\n').split()
	identification = data[0]
	latitude = data[1]
	longitude = data[2]
	areaCode = data[3]
