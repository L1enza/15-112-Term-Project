from cmu_graphics import *
import math
from settings import *

def normalizeAngle(angle):
    # Ensures the angle is always between 0 and 2pi
    angle = angle % (2 * math.pi)
    if angle <= 0:
        angle = (2 * math.pi) + angle
    return angle

def distanceBetween(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

class Ray:
    def __init__(self, rayAngle, player, map):
        self.rayAngle = normalizeAngle(rayAngle)
        self.player = player
        self.map = map
        self.wallHitX = 0
        self.wallHitY = 0
        self.distance = 0
        self.color = 255
        self.collected = True

    def cast(self):
        # This raycasting algorithm is based on the tutorial by
        # "ChiliTomatoNoodle" on YouTube: "Raycasting Tutorial (in Python)"
        # https://www.youtube.com/watch?v=ECqUrT7IdqQ

        # This is a DDA (Digital Differential Analysis) algorithim
        # It finds the closest horizontal grid line intersection
        # Then the closest vertical line intersection
        # Then compares these distances and uses the closest hit for the wall drawn
        self.wallHitX = self.player.x
        self.wallHitY = self.player.y

        # HORIZONTAL CHECK!
        foundHorizontalWall = False
        horizontalHitX, horizontalHitY = 0, 0

        if self.rayAngle == 0 or self.rayAngle == math.pi:
            foundHorizontalWall = False
        else:
            if self.rayAngle > math.pi:
                stepY = -tileSize
                interceptY = (self.player.y // tileSize) * tileSize - 0.01
            else:
                stepY = tileSize
                interceptY = (self.player.y // tileSize) * tileSize + tileSize

            interceptX = self.player.x + (interceptY - self.player.y) / math.tan(
                self.rayAngle)

            nextX = interceptX
            nextY = interceptY

            stepX = stepY / math.tan(self.rayAngle)

            while 0 <= nextX < windowWidth and 0 <= nextY < windowHeight:
                if self.map.hasWallAt(nextX, nextY):
                    foundHorizontalWall = True
                    horizontalHitX, horizontalHitY = nextX, nextY
                    break
                nextX += stepX
                nextY += stepY

        # VERTICAL CHECK!
        foundVerticalWall = False
        verticalHitX, verticalHitY = 0, 0

        if self.rayAngle == math.pi/2 or self.rayAngle == 3*math.pi/2:
            foundVerticalWall = False
        else:
            if (self.rayAngle < math.pi/2) or (self.rayAngle > 3*math.pi/2):
                stepX = tileSize
                interceptX = (self.player.x // tileSize) * tileSize + tileSize
            else:
                stepX = -tileSize
                interceptX = (self.player.x // tileSize) * tileSize - 0.01

            interceptY = self.player.y + (interceptX - self.player.x) * math.tan(
                self.rayAngle)

            nextX = interceptX
            nextY = interceptY

            stepY = stepX * math.tan(self.rayAngle)

            while 0 <= nextX < windowWidth and 0 <= nextY < windowHeight:
                if self.map.hasWallAt(nextX, nextY):
                    foundVerticalWall = True
                    verticalHitX, verticalHitY = nextX, nextY
                    break
                nextX += stepX
                nextY += stepY

        # Compare distances
        horizontalDistance = distanceBetween(
            self.player.x, self.player.y, horizontalHitX, horizontalHitY
        ) if foundHorizontalWall else float('inf')
        
        verticalDistance = distanceBetween(
            self.player.x, self.player.y, verticalHitX, verticalHitY
        ) if foundVerticalWall else float('inf')

        if horizontalDistance < verticalDistance:
            self.wallHitX, self.wallHitY = horizontalHitX, horizontalHitY
            self.distance = horizontalDistance
        else:
            self.wallHitX, self.wallHitY = verticalHitX, verticalHitY
            self.distance = verticalDistance
        # This corrects a fisheye effect
        # It adjusts the perceived distance based on the angle between the ray ...
        # ... and the players view direction
        self.distance *= math.cos(self.player.rotationAngle - self.rayAngle)

    def render(self, app):
        if self.collected:
            return
            
        scaleX = app.width / (cols * tileSize)
        scaleY = app.height / (rows * tileSize)
        
        
        imageWidth = 16
        imageHeight = 20
        drawImage(
            'midterm.png',  
            (self.x - imageWidth/2) * scaleX, 
            (self.y - imageHeight/2) * scaleY,
            width=imageWidth * scaleX, 
            height=imageHeight * scaleY
        )
