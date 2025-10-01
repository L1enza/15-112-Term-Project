from cmu_graphics import *
import math
from settings import *

class Player:
    def __init__(self):
        self.x = windowWidth / 2
        self.y = windowHeight / 2
        self.radius = 3
        self.moveDirection = 0
        self.strafeDirection = 0
        self.rotationAngle = 0
        self.moveSpeed = 4  
        self.rotationSpeed = 3 * (math.pi / 180)  

    def update(self, app):
        moveStep = self.moveDirection * self.moveSpeed
        strafeStep = self.strafeDirection * self.moveSpeed

        # Uses trig to convert angle and speed into x and y movement
        forwardX = math.cos(self.rotationAngle) * moveStep
        forwardY = math.sin(self.rotationAngle) * moveStep
        # Adds sideways moevement perpendicular to the view direction (Adds 90 degrees to the angle)
        strafeX = math.cos(self.rotationAngle + math.pi/2) * strafeStep
        strafeY = math.sin(self.rotationAngle + math.pi/2) * strafeStep

        newX = self.x + forwardX + strafeX
        newY = self.y + forwardY + strafeY
        # Checks for walls before movement
        if not app.map.hasWallAt(newX, self.y):
            self.x = newX
        if not app.map.hasWallAt(self.x, newY):
            self.y = newY

        self.rotationAngle %= 2 * math.pi

    def render(self, app):
        scaleX = app.width / (cols * tileSize)
        scaleY = app.height / (rows * tileSize)

        drawCircle(self.x * scaleX, self.y * scaleY, 7, fill='blue')

        drawLine(
            self.x * scaleX, self.y * scaleY,
            (self.x + math.cos(self.rotationAngle) * 70) * scaleX,
            (self.y + math.sin(self.rotationAngle) * 70) * scaleY,
            fill='blue'
        )
