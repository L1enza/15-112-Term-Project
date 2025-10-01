from cmu_graphics import *
import math
import random
from settings import *

class Collectible:
    def __init__(self, map):
        self.map = map
        self.x = 0
        self.y = 0
        self.radius = 10
        self.collected = False
        self.label = "Exam Key"
        self.placeInValidPosition()
        self.examKeyImage = 'midterm.png'
        
    def placeInValidPosition(self):
        # Try to place the collectible in a valid position (not in a wall)
        maxAttempts = 100
        attempt = 0
        
        # Get player starting area coordinates for reference
        playerX, playerY = cols // 2 * tileSize, rows // 2 * tileSize
        
        # Create Flood Fill

        # CIATATION: AI Fixed
        # Prompt: I am trying to implement a simple flood fill here to ensure the player
        # can reach the key without being trapped. My algorithm is not working
        def isReachable(startX, startY, targetX, targetY):
            visited = set()
            queue = [(startX, startY)]
            
            while queue:
                x, y = queue.pop(0)
                if (x, y) in visited:
                    continue
                    
                visited.add((x, y))
                
                # Check if we've reached the target
                if abs(x - targetX) < tileSize and abs(y - targetY) < tileSize:
                    return True
                
                # Try all four directions
                directions = [(0, -tileSize), (tileSize, 0), 
                             (0, tileSize), (-tileSize, 0)]
                for dx, dy in directions:
                    newX, newY = x + dx, y + dy
                    if not self.map.hasWallAt(newX, newY):
                        queue.append((newX, newY))
            
            return False
        
        while attempt < maxAttempts:
            # Generate random position
            gridX = random.randint(1, cols - 2)
            gridY = random.randint(1, rows - 2)
            
            # Convert to world coordinates (center of tile)
            testX = gridX * tileSize + tileSize / 2
            testY = gridY * tileSize + tileSize / 2
            
            # Check if this position is valid (not in a wall)
            if self.map.hasWallAt(testX, testY) == 0:
                # Make sure it's not too close to player spawn
                distance = math.sqrt((testX - playerX)**2 + (testY - playerY)**2)
                
                if distance > 3 * tileSize:  # At least 3 tiles away from center
                    # Check if the position is reachable from player area
                    if isReachable(playerX, playerY, testX, testY):
                        self.x = testX
                        self.y = testY
                        return  # Valid position found
            
            attempt += 1
        
        # If we couldn't find a valid position, put it somewhere in the middle
        # This is a safety and should rarely happen
        self.x = (cols // 2 + 2) * tileSize
        self.y = (rows // 2 + 2) * tileSize
    
    def checkCollection(self, player):
        if self.collected:
            return False
            
        # Calculate distance between player and collectible
        distance = math.sqrt((player.x - self.x)**2 + (player.y - self.y)**2)
        
        # If player is close enough, mark as collected
        if distance < tileSize / 2:
            self.collected = True
            return True
        
        return False
    
    def render(self, app):
        if self.collected:
            return
            
        scaleX = app.width / (cols * tileSize)
        scaleY = app.height / (rows * tileSize)
        
        # Draw white paper with black text
        # Paper
        paperWidth = 16
        paperHeight = 20
        drawRect(
            (self.x - paperWidth/2) * scaleX, 
            (self.y - paperHeight/2) * scaleY,
            paperWidth * scaleX, 
            paperHeight * scaleY,
            fill='white'
        )
        
        # Text (scaled appropriately)
        drawLabel(
            "Exam Key", 
            self.x * scaleX, 
            self.y * scaleY,
            size=3 * min(scaleX, scaleY),
            fill='black'
        )
        
    def calculate3dProperties(self, player):
        dx = self.x - player.x
        dy = self.y - player.y
        
        # Distance between player and collectible
        distance = math.sqrt(dx**2 + dy**2)
        
        # CITATAION - Sprite angle taken from YouTube video in ciatations file
        spriteAngle = math.atan2(dy, dx)
        
        # Normalize the angle
        while spriteAngle - player.rotationAngle > math.pi:
            spriteAngle -= 2 * math.pi
        while spriteAngle - player.rotationAngle < -math.pi:
            spriteAngle += 2 * math.pi
            
        # Check if collectible is in front of player
        inFov = abs(spriteAngle - player.rotationAngle) < fov / 2
        
        return {
            'distance': distance,
            'angle': spriteAngle,
            'inFov': inFov
        }
