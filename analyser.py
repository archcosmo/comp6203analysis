"""
Run this script in the Competition Output Root Directory (same directory as logs folder)
Domain:
	0 = (New_sporthal)
	1 = (Politics)
	2 = (WindFarm)

Uncertainty:
	0 = Low (1-2)
	1 = Medium (3-4)
	2 = High (5-6)
	
"""

from __future__ import print_function
import csv
import os
import xml.etree.ElementTree as ET

"""
Gets the first index of the last tournament that an agent appears in
"""
def getLastTournamentIndex(agent):
	if agent == 0:
		return 0
	else:
		return ((38-agent)*9)+getLastTournamentIndex(agent-1)

"""
Gets the list of tournament numbers where agent_1 plays agent_2
"""
def getTournamentIndicies(agent_1, agent_2=None, domain=None, uncertainty=None):
	if agent_2 == None:
		fullList = []
		for i in range(1, 39):
			if not i == agent_1:
				fullList += getTournamentIndicies(agent_1, i, domain, uncertainty)
		return fullList
	if domain == None:
		fullList = []
		for i in range(0,3):
			fullList += getTournamentIndicies(agent_1, agent_2, i, uncertainty)
		return fullList
	if uncertainty == None:
		fullList = []
		for i in range(0,3):
			fullList += getTournamentIndicies(agent_1, agent_2, domain, i)
		return fullList
	if(
		agent_1 == agent_2
		or agent_1 < 1
		or agent_1 > 38
		or agent_2 < 1
		or agent_2 > 38
		or domain < 0
		or domain > 2
		or uncertainty < 0
		or uncertainty > 2
	):
		return []
	elif(agent_1 < agent_2):
		min_agent = agent_1
		max_agent = agent_2
	else:
		min_agent = agent_2
		max_agent = agent_1
		
	starting = getLastTournamentIndex(min_agent-1)
	firstOccurrence = starting + (max_agent-min_agent)*9 - 8
	firstOccurrence += 3*domain
	firstOccurrence += uncertainty
	return [firstOccurrence]

"""
Runs getTournamentIndicies() for every combination of agents
and tests that the output is correct by checking the tournament
XML files
"""
def testGetTournamentIndicies():
	count = 1
	fullList = []
	for i in range(1, 38):
		for j in range(i+1, 39):
			indicies = getTournamentIndicies(i, j)
			fullList += indicies
			for idx in indicies:
				print("Testing Tournaments:" + str(100 * idx / 6327) + "%", end='\r')
				tree = ET.parse("tournaments/"+str(idx)+".xml")
				parties = tree.getroot()[0][0][2]
				for party in parties.iter('party'):
					if not (party.attrib['classPath'] == "group" + str(i) + ".Agent" + str(i) 
					or party.attrib['classPath'] == "group" + str(j) + ".Agent" + str(j)):
						print(
							"Error Incorrect Agents at Tournament "
							+ str(idx) + " Agents " + str(i) + " and "
							+ str(j) + " expected"
						)
						return False
	for i in range(1, 6328):
		if not fullList[i-1] == i:
			print("Didnt Generate Tournament Indicies Correctly!")
			return False
	print("Tournament Indexes Generated Correctly!")
	return True
	
"""
Checks if a Tournament Printed an Error
"""
def tournamentThrewError(index):
	return not os.stat("syslogs/"+str(index)+"e.log").st_size == 0
	
errored = 0
for i in range(1, 6328):
	if tournamentThrewError(i):
		errored += 1
print(str(errored) + "/6327 Tournaments threw errors")

"""
Checks how many Negotiations were completed in a given tournament
"""
def negotiationsForTournament(index):
	with open("logs/"+str(index)+".log.csv", "rb") as csvfile:
		reader = csv.reader(csvfile, delimiter=';', quotechar='"')
		row_count = sum(1 for row in reader)
		return row_count - 2 #Account for header row and 'sep=;' row


"""
Checks how many agreements were reached in a tournament
"""
def agreementsInTournament(index):
	with open("logs/"+str(index)+".log.csv", "rb") as csvfile:
		reader = csv.reader(csvfile, delimiter=';', quotechar='"')
		rowIdx = 0
		agreements = 0
		for row in reader:
			if rowIdx > 1:
				if row[4] == "Yes":
					agreements += 1
			rowIdx += 1
		return agreements

"""
Checks how many negotiations explicitly disagreed
(not counting ones that were terminated by IRIDIS)
"""		
def disagreementsInTournament(index):
	with open("logs/"+str(index)+".log.csv", "rb") as csvfile:
		reader = csv.reader(csvfile, delimiter=';', quotechar='"')
		rowIdx = 0
		disagreements = 0
		for row in reader:
			if rowIdx > 1:
				if row[4] == "No":
					disagreements += 1
			rowIdx += 1
		return disagreements

"""
Gets an arbitrary column from an tournament file, returns an array
"""
def getColumnForTournament(index, column):
	with open("logs/"+str(index)+".log.csv", "rb") as csvfile:
		reader = csv.reader(csvfile, delimiter=';', quotechar='"')
		rowIdx = 0
		rounds = []
		for row in reader:
			if rowIdx > 1:
				rounds += [row[column]]
			rowIdx += 1
		return rounds

"""
Gets the rounds for a tounament as an array
"""
def getRoundsForTournament(index):
	return getColumnForTournament(index, 1)
	
def getNashDistanceForTournament(index, reserve):
	dists = []
	for dist in getColumnForTournament(index, 10):
		if not dist == "":
			dists += [float(dist)]
		else:
			dists += [float(reserve)]
	return dists

def getLowerAgentUtilityForTournament(index):
	utils = []
	
	agreed = getColumnForTournament(index, 4)
	agent1Util = getColumnForTournament(index, 14)
	agent2Util = getColumnForTournament(index, 15)
	for i in range(0, len(agent1Util), 2):
		if agreed[i] == "Yes":
			utils.append(float(agent1Util[i]))
		else:
			utils.append(float(0))
	for i in range(1, len(agent2Util), 2):
		if agreed[i] == "Yes":
			utils.append(float(agent2Util[i]))
		else:
			utils.append(float(0))
	return utils
	
def getHigherAgentUtilityForTournament(index):
	utils = []
	
	agreed = getColumnForTournament(index, 4)
	agent1Util = getColumnForTournament(index, 14)
	agent2Util = getColumnForTournament(index, 15)
	for i in range(0, len(agent2Util), 2):
		if agreed[i] == "Yes":
			utils.append(float(agent2Util[i]))
		else:
			utils.append(float(0))
	for i in range(1, len(agent1Util), 2):
		if agreed[i] == "Yes":
			utils.append(float(agent1Util[i]))
		else:
			utils.append(float(0))
	return utils
	
failed = 0
for i in range(1,6328):
	negotiationsCompleted = negotiationsForTournament(i)
	if negotiationsCompleted < 10:
		failed += 10-negotiationsCompleted
print(str(failed) + "/63270 negotiations did not finish")

totalFailed = 0
for i in range(1,39):
	if not i == 37:
		for t in getTournamentIndicies(i):
			negotiationsCompleted = negotiationsForTournament(t)
			if negotiationsCompleted < 10:
				totalFailed += 10-negotiationsCompleted
print("Average Negotiations Halted by IRIDIS="+str(totalFailed / 37))

oursFailed = 0
for t in getTournamentIndicies(37):
	negotiationsCompleted = negotiationsForTournament(t)
	if negotiationsCompleted < 10:
		oursFailed += 10-negotiationsCompleted
		
print("Agent 37 Negotiations Halted by IRIDIS="+str(oursFailed))


def getAvgUtilityForDomain(domain):
	utilities = []
	for j in range(1, 39):
		missed = 0
		utils2 = []
		for i in range(1,39):
			if not i == j:
				for t in getTournamentIndicies(agent_1=j, agent_2=i, domain=domain):
					if i < j:
						tournamentUtils = getHigherAgentUtilityForTournament(t)
					else:
						tournamentUtils = getLowerAgentUtilityForTournament(t)
				
					#for x in range(0, 10-len(tournamentUtils)):
						#tournamentUtils.append(0)
					utils2 += tournamentUtils
		utilities.append(sum(utils2)/len(utils2))
	return utilities
		
sportHalUtil = getAvgUtilityForDomain(0)
politicsUtil = getAvgUtilityForDomain(1)
windfarmUtil = getAvgUtilityForDomain(2)

def getAvgNashDistanceForDomain(domain, reserve):
	dists = []
	for j in range(1, 39):
		dist = []
		for i in range(1,39):
			if not i == j:
				for t in getTournamentIndicies(agent_1=j, agent_2=i, domain=domain):
					tournamentNash = getNashDistanceForTournament(t, reserve)
				
					#for x in range(0, 10-len(tournamentNash)):
						#tournamentNash.append(0)
					dist += tournamentNash
		dists.append(sum(dist)/len(dist))
	return dists

sportHalDist = getAvgNashDistanceForDomain(0, 0.2)
politicsDist = getAvgNashDistanceForDomain(1, 0.8)
windfarmDist = getAvgNashDistanceForDomain(2, 0.6)

avgUtil = []
avgDist = []
for x in range(0, 38):
	avgUtil.append((sportHalUtil[x]+politicsUtil[x]+windfarmUtil[x])/3)
	avgDist.append((sportHalDist[x]+politicsDist[x]+windfarmDist[x])/3)


with open("analysis.out.csv", "wb") as csvfile:
		writer = csv.writer(csvfile, delimiter=',', quotechar='"')
		writer.writerow(['SportHall'] + ['']*2 + ['Politics'] + ['']*2 + ['WindFarm'] + ['']*2)
		writer.writerow(['Agent'] +['Avg Utility', 'Avg Nash Dist'] * 3 + ['Overall Avg Utility', 'Overall Avg Nash Dist', 'Max Utility', 'Min Utility', 'Max Dist', 'Min Dist', 'Utility Score', 'Dist Score', 'Overall Score'])
		for x in range(0, 38):
			writer.writerow([
				x+1,
				sportHalUtil[x],
				sportHalDist[x],
				politicsUtil[x],
				politicsDist[x],
				windfarmUtil[x],
				windfarmDist[x],
				avgUtil[x],
				avgDist[x],
				max(avgUtil), 
				min(avgUtil),
				max(avgDist),
				min(avgDist),
				(avgUtil[x] - min(avgUtil))/(max(avgUtil) - min(avgUtil)),
				(max(avgDist)-avgDist[x])/(max(avgDist)-min(avgDist)),
				((avgUtil[x] - min(avgUtil))/(max(avgUtil) - min(avgUtil)) + (max(avgDist)-avgDist[x])/(max(avgDist)-min(avgDist)))/2
			])