# Librarys
import time
import math
import argparse
import random
import copy
import os.path
import datetime
import numpy as np
from os import path
from tkinter import *

def isInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def int2Hex(x):
    val = hex(x)[2:]  # returns something like '0x15', so we remove the '0x'
    val = "0" + val if len(val) < 2 else val  # make sure 2 digits
    return val


class Solution(object):

    def __init__(self, puzzle, edgesHorizontal, edgesVertical, iStart, jStart, iEnd, jEnd):
        self.puzzle = puzzle
        self.edgesHorizontal = edgesHorizontal
        self.edgesVertical = edgesVertical
        self.returnToStart = iStart == iEnd and jStart == jEnd
        self.distanceFromStart = abs(iEnd - iStart) + abs(jEnd - jStart)

    def getFitness(self, update):

        originalEdgesHorizontal = copy.deepcopy(self.puzzle.edgesHorizontal)
        originalEdgesVertical = copy.deepcopy(self.puzzle.edgesVertical)

        self.puzzle.edgesHorizontal = self.edgesHorizontal
        self.puzzle.edgesVertical = self.edgesVertical

        # Total number of boxes complete
        totalBoxesComplete = 0.0
        totalBoxesNumbers = 0.0
        for i in range(0, self.puzzle.gridNumberY):
            for j in range(0, self.puzzle.gridNumberX):
                if self.puzzle.checkBoxComplete(i, j):
                    totalBoxesComplete += 1
                if not self.puzzle.blocks[i][j] == None:
                    totalBoxesNumbers += 1

        completeProp = 0.5
        if totalBoxesNumbers != 0:
            completeProp = totalBoxesComplete * 1.0 / totalBoxesNumbers * 1.0

        # Total number of starting points hit
        self.puzzle.findSinglePoints()
        singlePointsNum = len(self.puzzle.singlePoints)
        pointsNum = self.puzzle.gridNumberX * self.puzzle.gridNumberY
        singleProp = 1 - (singlePointsNum * 1.0 / pointsNum * 1.0)

        # Get distance as proportional
        maxDist = self.puzzle.gridNumberX + self.puzzle.gridNumberY
        distProp = 1 - (self.distanceFromStart * 1.0 / maxDist * 1.0)

        self.puzzle.edgesHorizontal = originalEdgesHorizontal
        self.puzzle.edgesVertical = originalEdgesVertical

        global WEIGHT_COMPLETE
        global WEIGHT_DISTANCE
        global WEIGHT_SINGLE

        totalFitness = WEIGHT_COMPLETE * completeProp + WEIGHT_DISTANCE * distProp + WEIGHT_SINGLE * singleProp

        # Update weights if '-d' being used
        if USE_DYNAMIC_FITNESS and update:

            props = [completeProp, distProp, singleProp]
            minPropIndex = props.index(min(props))
            increment = FITNESS_INCREMENT
            halfIncrement = FITNESS_INCREMENT / 2.0

            if minPropIndex == 0:
                WEIGHT_COMPLETE = min(1.0, WEIGHT_COMPLETE + increment)
                WEIGHT_DISTANCE = max(0.0, WEIGHT_DISTANCE - halfIncrement)
                WEIGHT_SINGLE = max(0.0, WEIGHT_SINGLE - halfIncrement)

            elif minPropIndex == 1:
                WEIGHT_COMPLETE = max(0.0, WEIGHT_COMPLETE - halfIncrement)
                WEIGHT_DISTANCE = min(1.0, WEIGHT_DISTANCE + increment)
                WEIGHT_SINGLE = max(0.0, WEIGHT_SINGLE - halfIncrement)

            elif minPropIndex == 2:
                WEIGHT_COMPLETE = max(0.0, WEIGHT_COMPLETE - halfIncrement)
                WEIGHT_DISTANCE = max(0.0, WEIGHT_DISTANCE - halfIncrement)
                WEIGHT_SINGLE = min(1.0, WEIGHT_SINGLE + increment)

            totalWeights = WEIGHT_COMPLETE + WEIGHT_DISTANCE + WEIGHT_SINGLE
            WEIGHT_COMPLETE = WEIGHT_COMPLETE / totalWeights
            WEIGHT_DISTANCE = WEIGHT_DISTANCE / totalWeights
            WEIGHT_SINGLE = WEIGHT_SINGLE / totalWeights

        return totalFitness

    def getFitnessPoint(self, iCurrent, jCurrent):

        originalEdgesHorizontal = copy.deepcopy(self.puzzle.edgesHorizontal)
        originalEdgesVertical = copy.deepcopy(self.puzzle.edgesVertical)

        self.puzzle.edgesHorizontal = self.edgesHorizontal
        self.puzzle.edgesVertical = self.edgesVertical

        # Total number of boxes complete
        totalBoxesComplete = 0.0
        totalBoxesNumbers = 0.0
        for i in range(iCurrent - 1, iCurrent + 1):
            for j in range(jCurrent - 1, jCurrent + 1):

                if (0 <= i and i <= self.puzzle.gridNumberY - 1
                        and 0 <= j and j <= self.puzzle.gridNumberX - 1):
                    if self.puzzle.checkBoxComplete(i, j):
                        totalBoxesComplete += self.puzzle.blocks[i][j] + 1
                    if not self.puzzle.blocks[i][j] == None:
                        totalBoxesNumbers += 1

        completeProp = 0.5
        if totalBoxesNumbers != 0:
            completeProp = totalBoxesComplete * 1.0 / totalBoxesNumbers * 1.0

        # Total number of starting points hit
        self.puzzle.findSinglePoints()
        singlePointsNum = len(self.puzzle.singlePoints)
        pointsNum = self.puzzle.gridNumberX * self.puzzle.gridNumberY
        singleProp = 1 - (singlePointsNum * 1.0 / pointsNum * 1.0)

        # Get distance as proportional
        maxDist = self.puzzle.gridNumberX + self.puzzle.gridNumberY
        distProp = 1 - (self.distanceFromStart * 1.0 / maxDist * 1.0)

        self.puzzle.edgesHorizontal = originalEdgesHorizontal
        self.puzzle.edgesVertical = originalEdgesVertical

        return WEIGHT_COMPLETE * completeProp + WEIGHT_DISTANCE * distProp + WEIGHT_SINGLE * singleProp

    def isSolutionComplete(self):

        if not self.returnToStart:
            return False

        originalEdgesHorizontal = copy.deepcopy(self.puzzle.edgesHorizontal)
        originalEdgesVertical = copy.deepcopy(self.puzzle.edgesVertical)

        self.puzzle.edgesHorizontal = self.edgesHorizontal
        self.puzzle.edgesVertical = self.edgesVertical

        # Check one entire loop
        self.puzzle.findSinglePoints()
        if not len(self.puzzle.singlePoints) == 0:
            self.puzzle.edgesHorizontal = originalEdgesHorizontal
            self.puzzle.edgesVertical = originalEdgesVertical
            return False

        # Check no point has 3 edges
        for i in range(0, self.puzzle.gridNumberY + 1):
            for j in range(0, self.puzzle.gridNumberX + 1):
                if self.puzzle.checkPointsEdges(i, j) == 3:
                    self.puzzle.edgesHorizontal = originalEdgesHorizontal
                    self.puzzle.edgesVertical = originalEdgesVertical
                    return False

        # Total number of boxes with numbers vs complete
        totalNumbers = 0
        totalComplete = 0
        for i in range(0, self.puzzle.gridNumberY):
            for j in range(0, self.puzzle.gridNumberX):
                if not self.puzzle.blocks[i][j] == None:
                    totalNumbers += 1
                if self.puzzle.checkBoxComplete(i, j):
                    totalComplete += 1

        self.puzzle.edgesHorizontal = originalEdgesHorizontal
        self.puzzle.edgesVertical = originalEdgesVertical

        return totalNumbers == totalComplete


class Puzzle(object):

    def __init__(self, filename):
        file = open(filename, 'r')
        try:
            with open(filename, 'r') as f:
                firstLine = f.readline()
                dimensions = list(map(int, firstLine.strip().split(',')))
                self.gridNumberX = dimensions[1]
                self.gridNumberY = dimensions[0]
                self.blocks = [[None for i in range(self.gridNumberX)] for j in range(self.gridNumberY)]
                self.edgesHorizontal = [[None for i in range(dimensions[1])] for j in range(dimensions[0] + 1)]
                self.edgesVertical = [[None for i in range(dimensions[1] + 1)] for j in range(dimensions[0])]
                self.edgesHorizontalPheromones = [[1 for i in range(dimensions[1])] for j in range(dimensions[0] + 1)]
                self.edgesVerticalPheromones = [[1 for i in range(dimensions[1] + 1)] for j in range(dimensions[0])]
                self.startingPoints = []
                self.singlePoints = []

                i = -1
                j = 0
                for line in f:
                    for c in line:
                        i = i + 1
                        if c == '.':
                            continue
                        elif isInt(c):
                            self.blocks[j][i] = int(c)
                    i = -1
                    j = j + 1

        except Exception as e:
            print('Puzzle File Incorrectly Formatted')
            print('ERROR: ' + str(e))
            exit()

    def basicMoves(self):

        # Corner moves
        if self.blocks[0][0] == 2:
            self.edgesVertical[1][0] = True
            self.edgesHorizontal[0][1] = True
        elif self.blocks[0][0] == 3:
            self.edgesVertical[0][0] = True
            self.edgesHorizontal[0][0] = True

        if self.blocks[0][self.gridNumberX - 1] == 2:
            self.edgesVertical[1][self.gridNumberX] = True
            self.edgesHorizontal[0][self.gridNumberX - 2] = True
        elif self.blocks[0][self.gridNumberX - 1] == 3:
            self.edgesVertical[0][self.gridNumberX] = True
            self.edgesHorizontal[0][self.gridNumberX - 1] = True

        if self.blocks[self.gridNumberY - 1][0] == 2:
            self.edgesVertical[self.gridNumberY - 2][0] = True
            self.edgesHorizontal[self.gridNumberY][1] = True
        elif self.blocks[self.gridNumberY - 1][0] == 3:
            self.edgesVertical[self.gridNumberY - 1][0] = True
            self.edgesHorizontal[self.gridNumberY][0] = True

        if self.blocks[self.gridNumberY - 1][self.gridNumberX - 1] == 2:
            self.edgesVertical[self.gridNumberY - 2][self.gridNumberX] = True
            self.edgesHorizontal[self.gridNumberY][self.gridNumberX - 2] = True
        elif self.blocks[self.gridNumberY - 1][self.gridNumberX - 1] == 3:
            self.edgesVertical[self.gridNumberY - 1][self.gridNumberX] = True
            self.edgesHorizontal[self.gridNumberY][self.gridNumberX - 1] = True

        for i in range(0, self.gridNumberY):
            for j in range(0, self.gridNumberX):

                # Can add logic for 2s if need be later
                if self.blocks[i][j] == 3:

                    # Check for 0,3 in cardinal direction to 3
                    if i - 1 >= 0:
                        self.checkCardinal3(i, j, self.blocks[i - 1][j], horizontalEdges=True, checkForward=False)

                    if i + 1 < self.gridNumberY:
                        self.checkCardinal3(i, j, self.blocks[i + 1][j], horizontalEdges=True, checkForward=True)

                    if j - 1 >= 0:
                        self.checkCardinal3(i, j, self.blocks[i][j - 1], horizontalEdges=False, checkForward=False)

                    if j + 1 < self.gridNumberX:
                        self.checkCardinal3(i, j, self.blocks[i][j + 1], horizontalEdges=False, checkForward=True)

                    # Check for 0,3 diagonal to 3
                    if i - 1 >= 0 and j - 1 >= 0:
                        if self.blocks[i - 1][j - 1] == 0:
                            self.edgesHorizontal[i][j] = True
                            self.edgesVertical[i][j] = True
                        if self.blocks[i - 1][j - 1] == 3:
                            self.edgesHorizontal[i + 1][j] = True
                            self.edgesVertical[i][j + 1] = True

                    if i - 1 >= 0 and j + 1 < self.gridNumberX:
                        if self.blocks[i - 1][j + 1] == 0:
                            self.edgesHorizontal[i][j] = True
                            self.edgesVertical[i][j + 1] = True
                        if self.blocks[i - 1][j + 1] == 3:
                            self.edgesHorizontal[i + 1][j] = True
                            self.edgesVertical[i][j] = True

                    if i + 1 < self.gridNumberY and j - 1 >= 0:
                        if self.blocks[i + 1][j - 1] == 0:
                            self.edgesHorizontal[i + 1][j] = True
                            self.edgesVertical[i][j] = True
                        if self.blocks[i + 1][j - 1] == 3:
                            self.edgesHorizontal[i][j] = True
                            self.edgesVertical[i][j + 1] = True

                    if i + 1 < self.gridNumberY and j + 1 < self.gridNumberX:
                        if self.blocks[i + 1][j + 1] == 0:
                            self.edgesHorizontal[i + 1][j] = True
                            self.edgesVertical[i][j + 1] = True
                        if self.blocks[i + 1][j + 1] == 3:
                            self.edgesHorizontal[i][j] = True
                            self.edgesVertical[i][j] = True

        self.updateEdges()
        self.findStartingPoints()

    def findStartingPoints(self):

        for i in range(0, self.gridNumberY + 1):
            for j in range(0, self.gridNumberX + 1):
                if self.checkPointsEdges(i, j) == 1:
                    self.startingPoints.append([i, j])

    def findSinglePoints(self):
        self.singlePoints = []
        for i in range(0, self.gridNumberY + 1):
            for j in range(0, self.gridNumberX + 1):
                if self.checkPointsEdges(i, j) == 1:
                    self.singlePoints.append([i, j])

    def checkCardinal3(self, i, j, otherBox, horizontalEdges, checkForward=True):

        if otherBox == 0:

            if horizontalEdges:
                self.edgesVertical[i][j] = True
                if j + 1 < self.gridNumberX + 1:
                    self.edgesVertical[i][j + 1] = True

                if i + 1 < self.gridNumberY + 1:
                    i1 = i if checkForward else i + 1
                    i2 = i + 1 if checkForward else i

                    self.edgesHorizontal[i1][j] = True
                    if j - 1 >= 0:
                        self.edgesHorizontal[i2][j - 1] = True
                    if j + 1 < self.gridNumberX:
                        self.edgesHorizontal[i2][j + 1] = True

            else:

                self.edgesHorizontal[i][j] = True
                if i + 1 < self.gridNumberY + 1:
                    self.edgesHorizontal[i + 1][j] = True

                if j + 1 < self.gridNumberX + 1:
                    j1 = j if checkForward else j + 1
                    j2 = j + 1 if checkForward else j

                    self.edgesVertical[i][j1] = True
                    if i - 1 >= 0:
                        self.edgesVertical[i - 1][j2] = True
                    if i + 1 < self.gridNumberY:
                        self.edgesVertical[i + 1][j2] = True

        elif otherBox == 3:

            if horizontalEdges:
                self.edgesHorizontal[i][j] = True
                self.edgesHorizontal[i + 1][j] = True
            else:
                self.edgesVertical[i][j] = True
                self.edgesVertical[i][j + 1] = True

    def checkPointsEdges(self, i, j):
        drawnLines = [None] * 4

        if i - 1 >= 0:
            drawnLines[0] = self.edgesVertical[i - 1][j]
        if i + 1 <= self.gridNumberY:
            drawnLines[1] = self.edgesVertical[i][j]
        if j - 1 >= 0:
            drawnLines[2] = self.edgesHorizontal[i][j - 1]
        if j + 1 <= self.gridNumberX:
            drawnLines[3] = self.edgesHorizontal[i][j]

        return drawnLines.count(True)

    def checkBoxEdges(self, i, j):

        edgesDrawn = 0
        if self.edgesHorizontal[i][j]:
            edgesDrawn += 1
        if self.edgesHorizontal[i + 1][j]:
            edgesDrawn += 1
        if self.edgesVertical[i][j]:
            edgesDrawn += 1
        if self.edgesVertical[i][j + 1]:
            edgesDrawn += 1

        edgesBlocked = 0
        if self.edgesHorizontal[i][j] == False:
            edgesBlocked += 1
        if self.edgesHorizontal[i + 1][j] == False:
            edgesBlocked += 1
        if self.edgesVertical[i][j] == False:
            edgesBlocked += 1
        if self.edgesVertical[i][j + 1] == False:
            edgesBlocked += 1

        return [edgesDrawn, edgesBlocked]

    def checkBoxComplete(self, i, j):
        if self.blocks[i][j] == None:
            return False
        return self.blocks[i][j] == self.checkBoxEdges(i, j)[0]

    def updateEdges(self):

        # If -r is on don't update edges
        if USE_RANDOM:
            return

        updated = True
        while updated:
            updated = False

            for i in range(0, self.gridNumberY + 1):
                for j in range(0, self.gridNumberX + 1):
                    if self.checkPointsEdges(i, j) == 2:
                        self.completePointEdges(i, j)

            for i in range(0, self.gridNumberY):
                for j in range(0, self.gridNumberX):
                    if self.completeBox(i, j):
                        updated = True

            self.findSinglePoints()
            for point in self.singlePoints:
                validMoves = self.getValidMoves(point[0], point[1])
                if len(validMoves) == 1:
                    iCur = point[0]
                    jCur = point[1]
                    iNew = validMoves[0][0]
                    jNew = validMoves[0][1]

                    # Check if closing loop
                    match = False
                    for pointNew in self.singlePoints:
                        if pointNew[0] == iNew and pointNew[1] == jNew:
                            match = True
                            break
                    if match:
                        continue

                    # Moving horizontal
                    if iCur == iNew:
                        if jCur < jNew:
                            self.edgesHorizontal[iCur][jCur] = True
                        elif jCur > jNew:
                            self.edgesHorizontal[iNew][jNew] = True

                    # Moving vertical
                    elif jCur == jNew:
                        if iCur < iNew:
                            self.edgesVertical[iCur][jCur] = True
                        elif iCur > iNew:
                            self.edgesVertical[iNew][jNew] = True

                    # Update line
                    updated = True
                    self.findSinglePoints()

            self.findSinglePoints()

    def completePointEdges(self, i, j):

        if i - 1 >= 0 and not self.edgesVertical[i - 1][j]:
            self.edgesVertical[i - 1][j] = False
        if i + 1 <= self.gridNumberY and not self.edgesVertical[i][j]:
            self.edgesVertical[i][j] = False
        if j - 1 >= 0 and not self.edgesHorizontal[i][j - 1]:
            self.edgesHorizontal[i][j - 1] = False
        if j + 1 <= self.gridNumberX and not self.edgesHorizontal[i][j]:
            self.edgesHorizontal[i][j] = False

    def completeBox(self, i, j):
        updated = False
        if self.blocks[i][j] != None:
            if self.blocks[i][j] == 4 - self.checkBoxEdges(i, j)[1]:

                if (self.edgesHorizontal[i][j] == None
                        and (i - 1 < 0 or j + 1 > self.gridNumberX or not self.checkBoxComplete(i - 1, j))):
                    self.edgesHorizontal[i][j] = True
                    updated = True

                if (self.edgesHorizontal[i + 1][j] == None
                        and (i + 2 > self.gridNumberY or j + 1 > self.gridNumberX or not self.checkBoxComplete(i + 1,
                                                                                                               j))):
                    self.edgesHorizontal[i + 1][j] = True
                    updated = True

                if (self.edgesVertical[i][j] == None
                        and (i + 1 > self.gridNumberY or j - 1 < 0 or not self.checkBoxComplete(i, j - 1))):
                    self.edgesVertical[i][j] = True
                    updated = True

                if (self.edgesVertical[i][j + 1] == None
                        and (i + 1 > self.gridNumberY or j + 2 > self.gridNumberX or not self.checkBoxComplete(i,
                                                                                                               j + 1))):
                    self.edgesVertical[i][j + 1] = True
                    updated = True

        return updated

    def getValidMoves(self, i, j):

        validMoves = []

        # Check valid moves
        if (i - 1 >= 0
                and self.edgesVertical[i - 1][j] == None
                and self.checkPointsEdges(i - 1, j) < 2
                and (i - 1 < 0 or j - 1 < 0 or not self.checkBoxComplete(i - 1, j - 1))
                and (i - 1 < 0 or j + 1 > self.gridNumberX or not self.checkBoxComplete(i - 1, j))):
            validMoves.append([i - 1, j, self.edgesVerticalPheromones[i - 1][j]])

        if (i + 1 <= self.gridNumberY
                and self.edgesVertical[i][j] == None
                and self.checkPointsEdges(i + 1, j) < 2
                and (i + 1 > self.gridNumberY or j - 1 < 0 or not self.checkBoxComplete(i, j - 1))
                and (i + 1 > self.gridNumberY or j + 1 > self.gridNumberX or not self.checkBoxComplete(i, j))):
            validMoves.append([i + 1, j, self.edgesVerticalPheromones[i][j]])

        if (j - 1 >= 0
                and self.edgesHorizontal[i][j - 1] == None
                and self.checkPointsEdges(i, j - 1) < 2
                and (i - 1 < 0 or j - 1 < 0 or not self.checkBoxComplete(i - 1, j - 1))
                and (i + 1 > self.gridNumberY or j - 1 < 0 or not self.checkBoxComplete(i, j - 1))):
            validMoves.append([i, j - 1, self.edgesHorizontalPheromones[i][j - 1]])

        if (j + 1 <= self.gridNumberX
                and self.edgesHorizontal[i][j] == None
                and self.checkPointsEdges(i, j + 1) < 2
                and (i - 1 < 0 or j + 1 > self.gridNumberX or not self.checkBoxComplete(i - 1, j))
                and (i + 1 > self.gridNumberY or j + 1 > self.gridNumberX or not self.checkBoxComplete(i, j))):
            validMoves.append([i, j + 1, self.edgesHorizontalPheromones[i][j]])

        return validMoves

    def updatePheromones(self, solutions):

        for i in range(0, self.gridNumberY + 1):
            for j in range(0, self.gridNumberX):
                self.edgesHorizontalPheromones[i][j] *= EVAPORATION_RATE

        for i in range(0, self.gridNumberY):
            for j in range(0, self.gridNumberX + 1):
                self.edgesVerticalPheromones[i][j] *= EVAPORATION_RATE

        numberOfSolutions = len(solutions)
        for solution in solutions:

            fitness = 0

            # If -l is used we use local fitness around edge rather than fitness of entire solution
            if not USE_LOCAL_FITNESS:
                fitness = solution.getFitness(True)
            deltaPheromones = fitness * UPDATE_CONST

            for i in range(0, self.gridNumberY + 1):
                for j in range(0, self.gridNumberX):
                    if solution.edgesHorizontal[i][j]:

                        if USE_LOCAL_FITNESS:
                            fitness = solution.getFitnessPoint(i, j)
                            deltaPheromones = fitness * UPDATE_CONST
                        self.edgesHorizontalPheromones[i][j] += deltaPheromones * 1.0 / numberOfSolutions * 1.0

            for i in range(0, self.gridNumberY):
                for j in range(0, self.gridNumberX + 1):
                    if solution.edgesVertical[i][j]:

                        if USE_LOCAL_FITNESS:
                            fitness = solution.getFitnessPoint(i, j)
                            deltaPheromones = fitness * UPDATE_CONST
                        self.edgesVerticalPheromones[i][j] += deltaPheromones * 1.0 / numberOfSolutions * 1.0


class DrawPuzzle(object):

    def __init__(self, puzzle):
        self.puzzle = puzzle
        self.root = Tk()
        canvasSizeX = CANVAS_BOUNDARY_SIZE * 2 + CANVAS_BLOCK_SIZE * self.puzzle.gridNumberX
        canvasSizeY = CANVAS_BOUNDARY_SIZE * 2 + CANVAS_BLOCK_SIZE * self.puzzle.gridNumberY
        self.canvas = Canvas(self.root, width=canvasSizeX, height=canvasSizeY)
        self.canvas.pack()
        self.drawInitBoard()

    def drawInitBoard(self):

        for i in range(0, self.puzzle.gridNumberY + 1):
            for j in range(0, self.puzzle.gridNumberX + 1):
                xCoord = CANVAS_BOUNDARY_SIZE + j * CANVAS_BLOCK_SIZE
                yCoord = CANVAS_BOUNDARY_SIZE + i * CANVAS_BLOCK_SIZE
                self.canvas.create_oval(xCoord, yCoord, xCoord + CIRCLE_SIZE, yCoord + CIRCLE_SIZE, fill="black")

                # Draws numbers in (about) middle of block if number exists
                if j < self.puzzle.gridNumberX and i < self.puzzle.gridNumberY and self.puzzle.blocks[i][j] != None:
                    self.canvas.create_text(xCoord + CANVAS_BLOCK_SIZE / 1.75, yCoord + CANVAS_BLOCK_SIZE / 1.75,
                                            text=str(self.puzzle.blocks[i][j]))

        self.canvas.update()

    def drawBoard(self):

        for i in range(len(self.puzzle.edgesHorizontal)):
            for j in range(len(self.puzzle.edgesHorizontal[i])):
                if self.puzzle.edgesHorizontal[i][j]:
                    xCoord = CANVAS_BOUNDARY_SIZE + j * CANVAS_BLOCK_SIZE + CIRCLE_SIZE / 2 + LINE_SIZE / 2
                    yCoord = CANVAS_BOUNDARY_SIZE + i * CANVAS_BLOCK_SIZE + CIRCLE_SIZE / 2 + LINE_SIZE / 2
                    self.canvas.create_line(xCoord, yCoord, xCoord + CANVAS_BLOCK_SIZE, yCoord, width=LINE_SIZE)

        for i in range(len(self.puzzle.edgesVertical)):
            for j in range(len(self.puzzle.edgesVertical[i])):
                if self.puzzle.edgesVertical[i][j]:
                    xCoord = CANVAS_BOUNDARY_SIZE + j * CANVAS_BLOCK_SIZE + CIRCLE_SIZE / 2 + LINE_SIZE / 2
                    yCoord = CANVAS_BOUNDARY_SIZE + i * CANVAS_BLOCK_SIZE + CIRCLE_SIZE / 2 + LINE_SIZE / 2
                    self.canvas.create_line(xCoord, yCoord, xCoord, yCoord + CANVAS_BLOCK_SIZE, width=LINE_SIZE)

        for i in range(0, self.puzzle.gridNumberY + 1):
            for j in range(0, self.puzzle.gridNumberX + 1):

                if self.puzzle.checkPointsEdges(i, j) == 1:
                    xCoord = CANVAS_BOUNDARY_SIZE + j * CANVAS_BLOCK_SIZE - 1.5
                    yCoord = CANVAS_BOUNDARY_SIZE + i * CANVAS_BLOCK_SIZE - 1.5
                    self.canvas.create_oval(xCoord, yCoord, xCoord + CIRCLE_SIZE + 3, yCoord + CIRCLE_SIZE + 3,
                                            fill="black", outline="")

        self.canvas.update()

    def drawSolution(self, solution):

        for i in range(len(solution.edgesHorizontal)):
            for j in range(len(solution.edgesHorizontal[i])):
                xCoord = CANVAS_BOUNDARY_SIZE + j * CANVAS_BLOCK_SIZE + CIRCLE_SIZE / 2 + LINE_SIZE / 2
                yCoord = CANVAS_BOUNDARY_SIZE + i * CANVAS_BLOCK_SIZE + CIRCLE_SIZE / 2 + LINE_SIZE / 2
                if solution.edgesHorizontal[i][j]:
                    self.canvas.create_line(xCoord, yCoord, xCoord + CANVAS_BLOCK_SIZE, yCoord, width=LINE_SIZE,
                                            fill="black")
                else:
                    self.canvas.create_line(xCoord, yCoord, xCoord + CANVAS_BLOCK_SIZE, yCoord, width=LINE_SIZE,
                                            fill="white")

        for i in range(len(solution.edgesVertical)):
            for j in range(len(solution.edgesVertical[i])):

                xCoord = CANVAS_BOUNDARY_SIZE + j * CANVAS_BLOCK_SIZE + CIRCLE_SIZE / 2 + LINE_SIZE / 2
                yCoord = CANVAS_BOUNDARY_SIZE + i * CANVAS_BLOCK_SIZE + CIRCLE_SIZE / 2 + LINE_SIZE / 2
                if solution.edgesVertical[i][j]:
                    self.canvas.create_line(xCoord, yCoord, xCoord, yCoord + CANVAS_BLOCK_SIZE, width=LINE_SIZE,
                                            fill="black")
                else:
                    self.canvas.create_line(xCoord, yCoord, xCoord, yCoord + CANVAS_BLOCK_SIZE, width=LINE_SIZE,
                                            fill="white")

        self.drawInitBoard()
        self.drawBoard()
        self.canvas.update()

    def drawPheromones(self):

        # First finding max pheromone value
        maxPheromone = None
        for i in range(len(self.puzzle.edgesHorizontalPheromones)):
            for j in range(len(self.puzzle.edgesHorizontalPheromones[i])):
                if maxPheromone == None or self.puzzle.edgesHorizontalPheromones[i][j] > maxPheromone:
                    maxPheromone = self.puzzle.edgesHorizontalPheromones[i][j]
        for i in range(len(self.puzzle.edgesVerticalPheromones)):
            for j in range(len(self.puzzle.edgesVerticalPheromones[i])):
                if maxPheromone == None or self.puzzle.edgesVerticalPheromones[i][j] > maxPheromone:
                    maxPheromone = self.puzzle.edgesVerticalPheromones[i][j]
        if maxPheromone == None:
            maxPheromone = 1

        # Draw pheromones scaled black intensity with max value
        for i in range(len(self.puzzle.edgesHorizontalPheromones)):
            for j in range(len(self.puzzle.edgesHorizontalPheromones[i])):

                colour = "black"
                if not self.puzzle.edgesHorizontalPheromones[i][j] > 1:
                    colourProportional = int2Hex(
                        int(255 * (1 - (self.puzzle.edgesHorizontalPheromones[i][j] * 1.0 / maxPheromone * 1.0))))
                    colour = "#ff" + colourProportional + colourProportional

                xCoord = CANVAS_BOUNDARY_SIZE + j * CANVAS_BLOCK_SIZE + CIRCLE_SIZE / 2 + LINE_SIZE / 2
                yCoord = CANVAS_BOUNDARY_SIZE + i * CANVAS_BLOCK_SIZE + CIRCLE_SIZE / 2 + LINE_SIZE / 2
                self.canvas.create_line(xCoord, yCoord, xCoord + CANVAS_BLOCK_SIZE, yCoord, width=LINE_SIZE,
                                        fill=colour)

        for i in range(len(self.puzzle.edgesVerticalPheromones)):
            for j in range(len(self.puzzle.edgesVerticalPheromones[i])):

                colour = "black"
                if not self.puzzle.edgesVerticalPheromones[i][j] > 1:
                    colourProportional = int2Hex(
                        int(255 * (1 - (self.puzzle.edgesVerticalPheromones[i][j] * 1.0 / maxPheromone * 1.0))))
                    colour = "#ff" + colourProportional + colourProportional

                xCoord = CANVAS_BOUNDARY_SIZE + j * CANVAS_BLOCK_SIZE + CIRCLE_SIZE / 2 + LINE_SIZE / 2
                yCoord = CANVAS_BOUNDARY_SIZE + i * CANVAS_BLOCK_SIZE + CIRCLE_SIZE / 2 + LINE_SIZE / 2
                self.canvas.create_line(xCoord, yCoord, xCoord, yCoord + CANVAS_BLOCK_SIZE, width=LINE_SIZE,
                                        fill=colour)

        self.drawInitBoard()
        self.drawBoard()
        self.canvas.update()


class Ants(object):

    def __init__(self, puzzle, populationSize):
        self.puzzle = puzzle
        self.populationSize = populationSize

    def findBestAnt(self):

        # Get all best starting points, only if -s activated
        numberOfStartingPoints = 1
        if USE_STARTING_POINTS:
            numberOfStartingPoints = len(self.puzzle.startingPoints)

        bestFitness = [0] * numberOfStartingPoints
        bestSolutions = [None] * numberOfStartingPoints
        iterationStartTime = time.process_time()

        for startingPointIndex in range(numberOfStartingPoints):

            startingPoint = self.puzzle.startingPoints[startingPointIndex]

            # Randomise initial starting point, if -s not activated
            if not USE_STARTING_POINTS:
                randomNum = random.randint(0, len(self.puzzle.startingPoints) - 1)
                startingPoint = self.puzzle.startingPoints[randomNum]

            for _ in range(self.populationSize):

                self.puzzle = puzzle
                iStart = startingPoint[0]
                jStart = startingPoint[1]
                iCur = iStart
                jCur = jStart
                firstIteration = True

                edgesHorizontalCopy = copy.deepcopy(self.puzzle.edgesHorizontal)
                edgesVerticalCopy = copy.deepcopy(self.puzzle.edgesVertical)

                while True:

                    validMoves = self.puzzle.getValidMoves(iCur, jCur)

                    if (iCur == iStart and jCur == jStart and not firstIteration) or len(validMoves) == 0:
                        break

                    # Average out weightings
                    weights = []
                    totalWeight = 0
                    for move in validMoves:
                        weight = move[-1]
                        weights.append(weight)
                        totalWeight += weight
                    for index in range(len(weights)):
                        weights[index] = weights[index] * 1.0 / totalWeight * 1.0

                    # Select the random move from index
                    randomIndex = np.random.choice(range(len(weights)), p=weights)
                    randomValidMove = validMoves[randomIndex]
                    iNew = randomValidMove[0]
                    jNew = randomValidMove[1]

                    # Moving horizontal
                    if iCur == iNew:
                        if jCur < jNew:
                            self.puzzle.edgesHorizontal[iCur][jCur] = True
                        elif jCur > jNew:
                            self.puzzle.edgesHorizontal[iNew][jNew] = True

                    # Moving vertical
                    elif jCur == jNew:
                        if iCur < iNew:
                            self.puzzle.edgesVertical[iCur][jCur] = True
                        elif iCur > iNew:
                            self.puzzle.edgesVertical[iNew][jNew] = True

                    # itrSolution = Solution(self.puzzle, self.puzzle.edgesHorizontal, self.puzzle.edgesVertical, iStart, jStart, iCur, jCur)
                    # puzzleDisplay.drawSolution(itrSolution)
                    # time.sleep(0.5)
                    # Update any confirmed edges, effectively acting as heuristic
                    self.puzzle.updateEdges()

                    # If any single line is blocked end
                    # blockedPoint = False
                    # for point in self.puzzle.singlePoints:
                    #     pointValidMoves = self.puzzle.getValidMoves(point[0], point[1])
                    #     if len(pointValidMoves) == 0:
                    #         blockedPoint = True
                    #         break
                    # if blockedPoint:
                    #     break

                    # Move along already drawn lines
                    while (self.puzzle.checkPointsEdges(iNew, jNew) == 2
                           and not (iNew == iStart and jNew == jStart)):

                        # print(str(iCur)+","+str(jCur))

                        if (iNew - 1 >= 0
                                and iNew - 1 != iCur
                                and self.puzzle.edgesVertical[iNew - 1][jNew]):
                            iCur = iNew
                            jCur = jNew
                            iNew = iNew - 1
                            continue

                        if (iNew + 1 <= self.puzzle.gridNumberY
                                and iNew + 1 != iCur
                                and self.puzzle.edgesVertical[iNew][jNew]):
                            iCur = iNew
                            jCur = jNew
                            iNew = iNew + 1
                            continue

                        if (jNew - 1 >= 0
                                and jNew - 1 != jCur
                                and self.puzzle.edgesHorizontal[iNew][jNew - 1]):
                            iCur = iNew
                            jCur = jNew
                            jNew = jNew - 1
                            continue

                        if (jNew + 1 <= self.puzzle.gridNumberX
                                and jNew + 1 != jCur
                                and self.puzzle.edgesHorizontal[iNew][jNew]):
                            iCur = iNew
                            jCur = jNew
                            jNew = jNew + 1
                            continue

                    # itrSolution = Solution(self.puzzle, self.puzzle.edgesHorizontal, self.puzzle.edgesVertical, iStart, jStart, iCur, jCur)
                    # puzzleDisplay.drawSolution(itrSolution)
                    # time.sleep(0.5)

                    iCur = iNew
                    jCur = jNew
                    firstIteration = False

                    # Check if puzzle is already failed, only if -c activated
                    if USE_EARLY_CANCEL:
                        possibleMoves = True
                        self.puzzle.findSinglePoints()
                        for point in self.puzzle.singlePoints:
                            validMoves = self.puzzle.getValidMoves(point[0], point[1])
                            if len(validMoves) == 0:
                                possibleMoves = False
                                break
                        if not possibleMoves:
                            break

                # Compare with best ant in this iteration
                curSolution = Solution(self.puzzle, self.puzzle.edgesHorizontal, self.puzzle.edgesVertical, iStart,
                                       jStart, iCur, jCur)
                curFitness = curSolution.getFitness(False)
                if bestSolutions[startingPointIndex] == None or curFitness > bestFitness[startingPointIndex]:
                    bestFitness[startingPointIndex] = curFitness
                    bestSolutions[startingPointIndex] = curSolution

                self.puzzle.edgesHorizontal = edgesHorizontalCopy
                self.puzzle.edgesVertical = edgesVerticalCopy

        return bestSolutions


# Global Graphic Sizes
CANVAS_BLOCK_SIZE = 60
CIRCLE_SIZE = 5
LINE_SIZE = 2
CANVAS_BOUNDARY_SIZE = 5

# Global ACO Constants
POPULATION_SIZE = 20
EVAPORATION_RATE = 0.90
UPDATE_CONST = 1
MAX_ITERATIONS = 50

# Fitness weights
WEIGHT_COMPLETE = 0.33
WEIGHT_DISTANCE = 0.33
WEIGHT_SINGLE = 0.33

# Arguement Parser, requires a filename for puzzle
parser = argparse.ArgumentParser(description='Solve a Loops Puzzle')
parser.add_argument('filename', help='name of puzzle file requiblack to solve')
parser.add_argument('-p', '--pheromones', action='store_true',
                    help='display pheromones instead of best solution (-t flag must be off)')
parser.add_argument('-r', '--random', action='store_true', help='flag turns off the use of the heuristic with the ACO')
parser.add_argument('-s', '--startpoints', action='store_true',
                    help='flag turns on getting every starting points best solution per iteration')
parser.add_argument('-l', '--localized', action='store_true',
                    help='flag turns on using a localised fitness function for edge pheromones')
parser.add_argument('-c', '--cancel', action='store_true',
                    help='flag turns on the early cancel if ACO is known to be wrong')
parser.add_argument('-d', '--dynamic', type=float, nargs=1,
                    help='fitness weightings will adjust dynamically by increment of arg')
parser.add_argument('-w', '--weights', type=float, nargs='*',
                    help='3 floats representing fitness weighting for; completeness, distance, single points, respectively (must not be more than 1 combined)')
parser.add_argument('-t', '--testing', type=int, nargs=1,
                    help='single argument, number of times to test ACO with puzzle')
args = parser.parse_args()

USE_RANDOM = args.random
USE_EARLY_CANCEL = args.cancel
USE_STARTING_POINTS = args.startpoints
USE_LOCAL_FITNESS = args.localized

# Check '-d' used correctly
USE_DYNAMIC_FITNESS = args.dynamic != None
FITNESS_INCREMENT = 0
if USE_DYNAMIC_FITNESS:
    if args.dynamic[0] < 0 or 1 < args.dynamic[0]:
        print('ERROR: Dynamic increment must be between 0 and 1')
        exit()
    FITNESS_INCREMENT = args.dynamic[0]

# Check weights are correctly formatted
if args.weights == None:
    print('')
elif not len(args.weights) == 3:
    print('ERROR: Weights must be three values')
    exit()
else:
    weightSum = 0.0
    for index in range(0, 3):
        if len(args.weights) > index:
            if args.weights[index] < 0 or 1 < args.weights[index]:
                print('ERROR: Weights must be between 0 and 1')
                exit()
            weightSum += args.weights[index]

            if index == 0:
                WEIGHT_COMPLETE = args.weights[index]
            if index == 1:
                WEIGHT_DISTANCE = args.weights[index]
            if index == 2:
                WEIGHT_SINGLE = 1.0 - args.weights[0] - args.weights[1]

    if weightSum > 1.0:
        print('ERROR: Combined weights cannot exceed 1')
        exit()

# print("--------------------")
# print('Using weights:')
# print('  WEIGHT_COMPLETE:\t' + str(WEIGHT_COMPLETE))
# print('  WEIGHT_DISTANCE:\t' + str(WEIGHT_DISTANCE))
# print('  WEIGHT_SINGLE:\t'   + str(WEIGHT_SINGLE))
# print("--------------------")

# Check if file exists
filename = "puzzles/" + args.filename
if not path.exists(filename):
    print('ERROR: File not found')
    exit()

if args.testing != None:
    print("Testing heuristic search")
    TESTING_REPEATS = args.testing[0]
    startTime = time.process_time()
    completed = []
    completedTime = []

    for index in range(TESTING_REPEATS):

        # Intialise board
        puzzle = Puzzle(filename)
        puzzle.basicMoves()
        startTimeIteration = time.process_time()

        # Run ACO
        ants = Ants(puzzle, POPULATION_SIZE)
        solutionFound = False
        for iteration in range(MAX_ITERATIONS):
            bestSolutions = ants.findBestAnt()
            puzzle.updatePheromones(bestSolutions)

            for bestSolution in bestSolutions:
                if bestSolution.isSolutionComplete():
                    completed.append(iteration + 1)
                    completedTime.append(time.process_time() - startTimeIteration)
                    solutionFound = True
                    break

            if solutionFound:
                break

        print("ACO Complete " + str(index + 1) + "/" + str(TESTING_REPEATS) + " times")

    totalTime = time.process_time() - startTime
    numComplete = len(completed)
    avgTime = -1
    averageComplete = -1
    if not numComplete == 0:
        avgTime = sum(completedTime) * 1.0 / numComplete * 1.0
        averageComplete = sum(completed) / numComplete

    print("--------------------")
    print("Puzzle Solved")
    print("Total Time:\t\t" + str(totalTime) + "s")
    print("Puzzle Complete:\t" + str(numComplete) + "/" + str(TESTING_REPEATS) + " times")
    print("Average Complete Time:\t" + str(avgTime) + "s")
    print("Average Complete Itr:\t" + str(averageComplete) + "/" + str(MAX_ITERATIONS) + " itrs")
    print("--------------------\n")

else:
    print("Starting Path Search...")

    # Intialise board
    puzzle = Puzzle(filename)
    puzzleDisplay = DrawPuzzle(puzzle)
    puzzle.basicMoves()
    puzzleDisplay.drawBoard()
    startTime = time.process_time()

    # Run ACO
    ants = Ants(puzzle, POPULATION_SIZE)
    solutionFound = False
    for iteration in range(MAX_ITERATIONS):
        bestSolutions = ants.findBestAnt()
        puzzle.updatePheromones(bestSolutions)

        maxFitness = None
        maxSolution = None
        for bestSolution in bestSolutions:

            fitness = bestSolution.getFitness(False)
            if maxFitness == None or fitness > maxFitness:
                maxFitness = fitness
                maxSolution = bestSolution

            if bestSolution.isSolutionComplete():
                print("Solution Found on Iteration: " + str(iteration + 1))
                puzzleDisplay.drawSolution(bestSolution)
                solutionFound = True
                break

        if solutionFound:
            break

        # Type of display produced
        if args.pheromones:
            puzzleDisplay.drawPheromones()
        elif maxSolution != None:
            puzzleDisplay.drawSolution(maxSolution)

    print("Path Search Complete\nTotal Time: " + str(time.process_time() - startTime) + "s")

    puzzleDisplay.root.mainloop()



