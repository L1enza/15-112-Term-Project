from cmu_graphics import *
import math
import random
import heapq 
from settings import *

class Enemy:
    def __init__(self, map, player):
        self.map = map
        self.player = player
        self.x = 0
        self.y = 0
        self.radius = 15
        self.speed = 4.5
        self.rotationAngle = 0
        
        # Pathfinding variables
        self.pathUpdateCounter = 0
        self.pathUpdateFrequency = 20 
        self.currentPath = []
        self.pathfindingGrid = None
        self.imageUrl = 'kosbie.png'
        
        # Stun variables
        self.stunned = False
        self.stunnedTimer = 0
        self.flashlightExposureTimer = 0
        self.flashlightExposureRequired = 15  # 1/4 second at 60 FPS
        
        # Place the enemy in a valid position
        self.placeInValidPosition()
    
    def placeInValidPosition(self):
        # CITATION: AI HELP
        # PROMPT: HOW CAN I USE RANDOM TO HELP IMPLEMENT THE RANDOM SPAWNING. I THINK I FIGURED OUT HOW TO NOT SPAWN IN BLOCKS BUT THIS CODE DOESNT WORK EVERY TIME
        maxAttempts = 100
        attempt = 0
        
        # Get player position for reference
        playerGridX = int(self.player.x // tileSize)
        playerGridY = int(self.player.y // tileSize)
        
        while attempt < maxAttempts:
            # Generate position on opposite side of map from player
            if playerGridX < cols / 2:
                gridX = random.randint(int(3*cols/4), cols - 2)  # Right side
            else:
                gridX = random.randint(1, int(cols/4))  # Left side
                
            if playerGridY < rows / 2:
                gridY = random.randint(int(3*rows/4), rows - 2)  # Bottom side
            else:
                gridY = random.randint(1, int(rows/4))  # Top side
            
            # Convert to the grid coordinates (center of a square)
            testX = gridX * tileSize + tileSize / 2
            testY = gridY * tileSize + tileSize / 2
            
            # Check if this position is not in a wall
            if self.map.hasWallAt(testX, testY) == 0:
                self.x = testX
                self.y = testY
                return  # Valid position found
            
            attempt += 1
        
        # If we couldn't find a valid position, put it near player as last resort
        # Find a close spot to player that's not a wall
        for distance in range(3, 10):
            for dx, dy in [(0, distance), (0, -distance), (distance, 0), (-distance, 0)]:
                newX = playerGridX + dx
                newY = playerGridY + dy
                
                if (0 <= newX < cols and 0 <= newY < rows and 
                    self.map.grid[newY][newX] == 0):
                    self.x = newX * tileSize + tileSize / 2
                    self.y = newY * tileSize + tileSize / 2
                    return
    
    def update(self, app):
        # stunned state
        if self.stunned:
            self.stunnedTimer -= 1
            if self.stunnedTimer <= 0:
                self.stunned = False
                self.flashlightExposureTimer = 0
            return  # Don't move while stunned
        
        # Reset exposure timer if not in flashlight beam
        if not self.isInFlashlightBeam(app):
            self.flashlightExposureTimer = 0
        
        # Update path periodically
        self.pathUpdateCounter += 1
        if self.pathUpdateCounter >= self.pathUpdateFrequency:
            self.findPathToPlayer()
            self.pathUpdateCounter = 0
        
        # Move enemy based on path or directly
        if self.currentPath and len(self.currentPath) > 0:
            self.followPath()
        else:
            self.moveDirectly()
    
    # CITATION: AI HELP
    # PROMPT: IM FAMILIAR WITH DJIKSTRA'S AND TRIED IMPLEMENTING SOMETHING SIMILAR, BUT ITS DEFINITELY NOT WORKING. CAN YOU HELP ME IMPLEMENT A SHORTEST PATH FOR THE ENEMY TO TAKE

    def heuristic(self, x1, y1, x2, y2): # Estimat3d distance between two points
        return abs(x1 - x2) + abs(y1 - y2)
    # CITATION: AI HELP
    # PROMPT: HE KEEPS GETTING STUCK ON CORNERS, HOW CAN IT FIGURE OUT HOW TO TURN TO THE SIDE AND AVOID THEM

    def findPathToPlayer(self): # A* pathfinding
        # Convert positions to grid coordinates
        startX, startY = int(self.x // tileSize), int(self.y // tileSize)
        targetX, targetY = int(self.player.x // tileSize), int(self.player.y // tileSize)
        # AI HELP CONTINUED just below
        # Initialize data structures
        openSet = [(0, (startX, startY))]  # Priority queue with (fScore, position)
        visited = set()
        cameFrom = {}
        gScore = {(startX, startY): 0}
        fScore = {(startX, startY): self.heuristic(startX, startY, targetX, targetY)}
        
        # Define directions
        cardinal_dirs = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # Down, Right, Up, Left
        diagonal_dirs = [(1, 1), (1, -1), (-1, 1), (-1, -1)]  # Down-Right, Up-Right, Down-Left, Up-Left
        
        # MORE AI HELP, ONLY ON HEAPQ USAGE on 177 AND 132, REST LOOSELY GUIDED FROM EXPLANATION
        while openSet:
            # Get the position with lowest fScore
            _, current = heapq.heappop(openSet)
            
            # If we've reached the target
            if current == (targetX, targetY):
                # Reconstruct path
                path = []
                while current in cameFrom:
                    x, y = current
                    path.append((x * tileSize + tileSize/2, y * tileSize + tileSize/2))
                    current = cameFrom[current]
                
                path.reverse()
                self.currentPath = path
                return
            
            if current in visited:
                continue
            
            visited.add(current)
            
            # First check directions
            for dx, dy in cardinal_dirs:
                nextX, nextY = current[0] + dx, current[1] + dy
                next_pos = (nextX, nextY)
                
                # Skip invalid positions
                if not (0 <= nextX < cols and 0 <= nextY < rows):
                    continue
                
                # Check if there's a wall
                cellX = nextX * tileSize + tileSize/2
                cellY = nextY * tileSize + tileSize/2
                if self.map.hasWallAt(cellX, cellY):
                    continue
                
                # Calculate scores (cost is 1.0 for cardinal directions)
                tentative_gScore = gScore[current] + 1.0
                
                if next_pos not in gScore or tentative_gScore < gScore[next_pos]:
                    # This path is better than any previous one
                    cameFrom[next_pos] = current
                    gScore[next_pos] = tentative_gScore
                    fScore[next_pos] = tentative_gScore + self.heuristic(nextX, nextY, targetX, targetY)
                    
                    if next_pos not in visited:
                        heapq.heappush(openSet, (fScore[next_pos], next_pos))
            
            # Then check diagonal directions
            for dx, dy in diagonal_dirs:
                nextX, nextY = current[0] + dx, current[1] + dy
                next_pos = (nextX, nextY)
                
                # Skip invalid positions
                if not (0 <= nextX < cols and 0 <= nextY < rows):
                    continue
                
                # Check if there's a wall
                cellX = nextX * tileSize + tileSize/2
                cellY = nextY * tileSize + tileSize/2
                if self.map.hasWallAt(cellX, cellY):
                    continue
                
                # AI HELP
                # #PROMPT: FIX diagonal movement, it thinks it can move between cracks that are flush
                adjacentX = self.map.hasWallAt((current[0] + dx) * tileSize + tileSize/2, current[1] * tileSize + tileSize/2)
                adjacentY = self.map.hasWallAt(current[0] * tileSize + tileSize/2, (current[1] + dy) * tileSize + tileSize/2)
                
                # If either adjacent cell has a wall, can't move diagonally
                if adjacentX or adjacentY:
                    continue  # Skip this, would cut through a corner
                # AI HELP ON WHAT THE SCORE SHOULD BE
                # Calculate scores (cost is sqrt(2) ≈ 1.414 for diagonal directions)
                tentative_gScore = gScore[current] + 1.414
                
                if next_pos not in gScore or tentative_gScore < gScore[next_pos]:
                    # This path is better than any previous one
                    cameFrom[next_pos] = current
                    gScore[next_pos] = tentative_gScore
                    fScore[next_pos] = tentative_gScore + self.heuristic(nextX, nextY, targetX, targetY)
                    
                    if next_pos not in visited:
                        heapq.heappush(openSet, (fScore[next_pos], next_pos))
        
        # If no path is found, clear the current path
        self.currentPath = []


    def followPath(self):
        if not self.currentPath:
            return
        
        # Get the next dot
        targetX, targetY = self.currentPath[0]
        
        # Calculate distance to dot
        dx = targetX - self.x
        dy = targetY - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # If we've reached the dot, remove it
        if distance < tileSize / 3:
            self.currentPath.pop(0)
            return
        
        # Move toward the dot
        if distance > 0:
            # Normalize direction vector
            dx /= distance
            dy /= distance
            
            # Calculate new position
            moveDistance = min(distance, self.speed)
            newX = self.x + dx * moveDistance
            newY = self.y + dy * moveDistance
            
            # try direct movement
            if not self.map.hasWallAt(newX, newY):
                # Direct path is clear
                self.x = newX
                self.y = newY
                self.rotationAngle = math.atan2(dy, dx)
            else:
                # Direct path is blocked so try moving along X and Y separately
                canMoveX = not self.map.hasWallAt(newX, self.y)
                canMoveY = not self.map.hasWallAt(self.x, newY)
                
                if canMoveX:
                    self.x = newX
                
                if canMoveY:
                    self.y = newY
                
                # If we couldn't move along either axis, force path recalculation
                if not canMoveX and not canMoveY:
                    self.pathUpdateCounter = self.pathUpdateFrequency
                
                # Only update rotation if we actually moved
                if canMoveX or canMoveY:
                    newDx = 0
                    newDy = 0
                    
                    if canMoveX:
                        newDx = dx
                    if canMoveY:
                        newDy = dy
                    
                    if newDx != 0 or newDy != 0:
                        # Only update rotation if we have a direction
                        magnitude = math.sqrt(newDx*newDx + newDy*newDy)
                        if magnitude > 0:
                            self.rotationAngle = math.atan2(newDy/magnitude, newDx/magnitude)
    
    def moveDirectly(self):
        dx = self.player.x - self.x
        dy = self.player.y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > 0:
            # Normalize direction
            dx /= distance
            dy /= distance
            
            # Calculate new position
            newX = self.x + dx * self.speed
            newY = self.y + dy * self.speed
            
            # Check for wall collisions separately in X and Y
            if not self.map.hasWallAt(newX, self.y):
                self.x = newX
            if not self.map.hasWallAt(self.x, newY):
                self.y = newY
            
            # Update rotation angle if we moved
            if newX != self.x or newY != self.y:
                self.rotationAngle = math.atan2(dy, dx)
    
    def isInFlashlightBeam(self, app):
        # Only check if flashlight is active and has battery
        if not app.flashlightActive or app.flashlightBattery <= 0:
            return False
        
        # Check if enemy is in front of player
        dx = self.x - app.player.x
        dy = self.y - app.player.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # If too far away, flashlight won't reach
        if distance > 500:  # Flashlight range
            return False
        # CITATION: # https://www.youtube.com/watch?v=ECqUrT7IdqQ, also cited in ray.py. Helped with angle correction
        # Calculate angle between player direction and enemy
        angleToEnemy = math.atan2(dy, dx)
        
        # Normalize angle difference
        angleDiff = abs(angleToEnemy - app.player.rotationAngle)
        while angleDiff > math.pi:
            angleDiff -= 2 * math.pi
        angleDiff = abs(angleDiff)
        
        # Check if enemy is within the flashlight beam angle
        beamAngle = 45 * (math.pi / 180)  # 45 degrees in radians
        return angleDiff < beamAngle / 2
    
    
    
    
    def checkFlashlightStun(self, app):
        # Only process if not already stunned
        if not self.stunned and app.flashlightActive and app.flashlightBattery > 0:
            # Check if enemy is in flashlight beam
            if self.isInFlashlightBeam(app):
                self.flashlightExposureTimer += 1
                
                # If exposed to flashlight for required time, stun enemy
                if self.flashlightExposureTimer >= self.flashlightExposureRequired:
                    self.stunned = True
                    app.audio.play('stun') # play stun sound
                    self.stunnedTimer = 100  # 5 seconds at 20 FPS
                    # Add visual effect for stunning
                    app.stunEffect = 20  # Frames to show stun effect
                    return True
            else:
                # Reset timer if not in beam
                self.flashlightExposureTimer = 0
        
        return False
    
    def checkCollision(self, player):
        # Calculate distance between player and enemy
        distance = math.sqrt((player.x - self.x)**2 + (player.y - self.y)**2)
        
        # If player is close enough, they're caught
        if distance < (self.radius + tileSize/4):
            return True
        
        return False
    
    def render(self, app):
        scaleX = app.width / (cols * tileSize)
        scaleY = app.height / (rows * tileSize)
        
        # Calculate size for 2D view
        size = self.radius * 2 * scaleX
        
        # Draw enemy as an image in 2D view with different opacity if stunned
        opacity = 50 if self.stunned else 100
        
        drawImage(
            self.imageUrl,
            (self.x - self.radius) * scaleX, 
            (self.y - self.radius) * scaleY,
            width=size,
            height=size,
            opacity=opacity
        )
        
        # Draw direction indicator
        dirX = self.x + math.cos(self.rotationAngle) * self.radius
        dirY = self.y + math.sin(self.rotationAngle) * self.radius
        
        # Draw stun indicator even if stunned
        # Draw circle to indicate stun
        if self.stunned:
            drawCircle(
                self.x * scaleX, 
                self.y * scaleY,
                size/1.5,
                fill=None,
                border='yellow',
                borderWidth=2
            )
        else:
            drawLine(
                self.x * scaleX, self.y * scaleY,
                dirX * scaleX, dirY * scaleY,
                fill='red', 
                lineWidth=2
            )
        
        # Draw path in 2D view
        if app.show2d and self.currentPath:
            for i, point in enumerate(self.currentPath):
                color = 'green' if i == 0 else 'blue'
                drawCircle(
                    point[0] * scaleX,
                    point[1] * scaleY,
                    3,
                    fill=color
                )
    
    def calculate3dProperties(self, player):
        dx = self.x - player.x
        dy = self.y - player.y
        
        # Distance between player and enemy
        distance = math.sqrt(dx**2 + dy**2)
        
        # Angle between player's direction and enemy position
        spriteAngle = math.atan2(dy, dx)
        
        # Normalize the angle
        while spriteAngle - player.rotationAngle > math.pi:
            spriteAngle -= 2 * math.pi
        while spriteAngle - player.rotationAngle < -math.pi:
            spriteAngle += 2 * math.pi
            
        # Is the enemy in front of the player?! find out... below! hehe
        inFov = abs(spriteAngle - player.rotationAngle) < fov / 2
        
        return {
            'distance': distance,
            'angle': spriteAngle,
            'inFov': inFov
        }