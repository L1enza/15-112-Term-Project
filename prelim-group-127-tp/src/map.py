from cmu_graphics import *
from settings import *
import random

class Map:
    def __init__(self):
        # Generate a random map
        self.grid = self.generateRandomMap()

    def generateRandomMap(self):
        # Initialize an empty grid with all 0s (empty spaces)
        grid = [[0 for _ in range(cols)] for _ in range(rows)]
        
        # Set the border to all 1s (walls)
        for i in range(rows):
            for j in range(cols):
                # Border cells
                if i == 0 or i == rows - 1 or j == 0 or j == cols - 1:
                    grid[i][j] = 1
        
        # Add random rooms and corridors for a more interesting map
        self.generateRooms(grid)
        self.generateObstacles(grid)
        
        # Ensure player spawn area is clear
        self.clearSpawnArea(grid)
        
        return grid
    
    def generateRooms(self, grid):
        # Create several random rooms
        numRooms = random.randint(3, 6)
        
        for _ in range(numRooms):
            # Random room dimensions and position
            roomWidth = random.randint(4, 8)
            roomHeight = random.randint(4, 8)
            roomX = random.randint(2, cols - roomWidth - 2)
            roomY = random.randint(2, rows - roomHeight - 2)
            
            # Decide if this is a solid room (walls only) or obstacle (solid block)
            isSolid = random.random() < 0.3
            
            # Create the room
            for y in range(roomY, roomY + roomHeight):
                for x in range(roomX, roomX + roomWidth):
                    if isSolid:
                        # For solid rooms, only set the borders as walls
                        if (y == roomY or y == roomY + roomHeight - 1 or
                            x == roomX or x == roomX + roomWidth - 1):
                            grid[y][x] = 1
                    else:
                        # Random pillars or obstacles inside the room
                        if random.random() < 0.15:
                            grid[y][x] = 1
            
            # Sometimes add a doorway
            if isSolid and random.random() < 0.75:
                # Pick a random wall
                wall = random.choice(['north', 'south', 'east', 'west'])
                if wall == 'north':
                    doorX = random.randint(roomX + 1, roomX + roomWidth - 2)
                    grid[roomY][doorX] = 0
                elif wall == 'south':
                    doorX = random.randint(roomX + 1, roomX + roomWidth - 2)
                    grid[roomY + roomHeight - 1][doorX] = 0
                elif wall == 'east':
                    doorY = random.randint(roomY + 1, roomY + roomHeight - 2)
                    grid[doorY][roomX + roomWidth - 1] = 0
                elif wall == 'west':
                    doorY = random.randint(roomY + 1, roomY + roomHeight - 2)
                    grid[doorY][roomX] = 0
    
    def generateObstacles(self, grid):
        # Add random corridors and walls
        numCorridors = random.randint(8, 15)
        
        for _ in range(numCorridors):
            # Pick a random starting point
            startX = random.randint(2, cols - 3)
            startY = random.randint(2, rows - 3)
            
            # Random corridor length
            length = random.randint(4, 10)
            
            # Random direction (horizontal or vertical)
            isHorizontal = random.choice([True, False])
            
            if isHorizontal:
                for x in range(startX, min(cols - 2, startX + length)):
                    grid[startY][x] = 1
            else:
                for y in range(startY, min(rows - 2, startY + length)):
                    grid[y][startX] = 1
        
        # Add some random single blocks
        numBlocks = int((rows * cols) * 0.05)  # 5% of the map
        for _ in range(numBlocks):
            x = random.randint(2, cols - 3)
            y = random.randint(2, rows - 3)
            grid[y][x] = 1
    
    def clearSpawnArea(self, grid):
        # Ensure there's an open area for the player to spawn
        centerY, centerX = rows // 2, cols // 2
        radius = 3
        
        for y in range(centerY - radius, centerY + radius + 1):
            for x in range(centerX - radius, centerX + radius + 1):
                if 0 <= y < rows and 0 <= x < cols:
                    # Clear a circle-like area
                    if ((y - centerY) ** 2 + (x - centerX) ** 2) <= radius ** 2:
                        grid[y][x] = 0

    def hasWallAt(self, x, y):
        gridX = int(x // tileSize)
        gridY = int(y // tileSize)

        if gridX < 0 or gridX >= len(self.grid[0]) or gridY < 0 or gridY >= len(self.grid):
            return 1  # Treat out of bounds as wall

        # Both 1 (wall) and 2 (door) count as walls for collision
        return self.grid[gridY][gridX] > 0  

    def render(self, app):
        # Ensure the scaling uses the actual app width/height, not the settings values
        newTileSizeX = app.width / cols
        newTileSizeY = app.height / rows

        for i in range(rows):
            for j in range(cols):
                tileX = j * newTileSizeX
                tileY = i * newTileSizeY

                if self.grid[i][j] == 0:
                    # Empty space
                    drawRect(tileX, tileY, newTileSizeX-1, newTileSizeY-1, fill='khaki')
                elif self.grid[i][j] == 1:
                    # Normal wall
                    drawRect(tileX, tileY, newTileSizeX-1, newTileSizeY-1, 
                            fill='darkKhaki')
                elif self.grid[i][j] == 2:
                    # Escape door
                    drawRect(tileX, tileY, newTileSizeX-1, newTileSizeY-1, 
                            fill='black')
