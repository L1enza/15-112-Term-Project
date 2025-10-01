from cmu_graphics import *
from settings import *
from ray import Ray
import random
import math

class Raycaster:
    def __init__(self, player, map):
        self.rays = []
        self.player = player
        self.map = map
        self.zBuffer = []  # Store wall distances for depth sorting

    def castAllRays(self):
        if len(self.rays) != numRays:
            self.rays = [None] * numRays
            self.zBuffer = [0] * numRays
        
        # Cast rays only in the field of view
        # Calculate angular step once
        rayAngle = self.player.rotationAngle - fov/2
        angleStep = fov / numRays
        
        # Cast rays efficiently
        for i in range(numRays):
            # Normalize the ray angle
            normalizedAngle = rayAngle % (2 * math.pi)
            if normalizedAngle < 0:
                normalizedAngle += 2 * math.pi
                
            # Initialize or update ray
            if self.rays[i] is None:
                self.rays[i] = Ray(normalizedAngle, self.player, self.map)
            else:
                self.rays[i].rayAngle = normalizedAngle
                self.rays[i].player = self.player
            
            # CITATION: AI HELP
            # PROMPT: ZBUFFER NOT WORKING PROPERLY, ITS STILL SHOWING SPRITES THROUGH WALLS, HELP
            # Cast the ray
            self.rays[i].cast()
            self.zBuffer[i] = self.rays[i].distance
            rayAngle += angleStep

    def render(self, app):
        # Set a max render distance for performance
        maxRenderDistance = 1500
        
        # Pre-calculate some values to avoid lots of calculations
        halfHeight = windowHeight / 2
        
        # First render the walls
        i = 0
        for ray in self.rays:
            if ray.distance == 0 or ray.distance > maxRenderDistance:
                # Skip the rays that hit nothing or are too far away
                i += 1
                continue

            # Avoid division inside loop
            distanceFactor = 32 / ray.distance
            
            # Adjust the projection constant for the larger window
            projectionFactor = 800
            # The wall height is inversely proportional to the distance
            lineHeight = distanceFactor * projectionFactor
            lineHeight = max(lineHeight, 1)
            drawBegin = halfHeight - (lineHeight / 2)

            # Use fewer multiplications for flashlight calculation
            if app.flashlightActive and app.flashlightBattery > 0:
                torchFactor = 1.0
            else:
                torchFactor = 0.5
                
            # map coordinates of the hit
            mapX = int(ray.wallHitX // tileSize)
            mapY = int(ray.wallHitY // tileSize)
            
            # Determine if hit a door
            isDoor = (0 <= mapY < len(self.map.grid) and 
                    0 <= mapX < len(self.map.grid[0]) and
                    self.map.grid[mapY][mapX] == 2)
            
            if isDoor:
                wallColor = rgb(0, 60, 0)
            # CITATION: AI USED FOR SHADOW EFFECT HELP
            # PROMPT: IM LOOPING THROUGH THE GRID TRYING TO APPLY DARKER WALLS TO IMITATE SHADOWS. HELP ME IMPLEMENT A FIX FOR THIS USING AN ALGORITHM
            else:
                # Check exactly which wall side was hit by examining the hit point
                # Convert the fractional part of X and Y to a percentage of tile
                fractX = ray.wallHitX % tileSize / tileSize
                
                # If we're at an integer X coordinate (very small or very large fractional X)
                # then we've hit a vertical wall (east or west facing)
                if fractX < 0.02 or fractX > 0.98:
                    # Vertical wall (east or west facing) - darker
                    wallColor = rgb(65, 55, 0)  # Much darker
                else:
                    # Horizontal wall (north or south facing) - slightly less dark
                    wallColor = rgb(85, 75, 0) 
            
            # Apply distance darkening with stronger fog effect for scarier atmosphere
            distanceFactor = max(0.1, min(1.0, 1.5 / (ray.distance / 200)))
            totalFactor = distanceFactor * torchFactor
            
            r = int(wallColor.red * totalFactor)
            g = int(wallColor.green * totalFactor)
            b = int(wallColor.blue * totalFactor)
            
            shadedColor = rgb(r, g, b)
            
            # Draw the wall strip with no border
            drawRect(i * res, drawBegin, res, lineHeight, fill=shadedColor, border=None)

            i += 1

    def renderSprites(self, app):
        spriteRenderDistance = 800
        
        # Prepare sprite data for sorting
        spritesToRender = []
        # CITATION: AI HELP WITH SPRITE
        # PROMPT: IVE BEGUN TO IMPLEMENT THE SAME RAYCASTING FEATURES AS THE WALLS BUT FOR THE SPRITES. CAN YOU FIX THE CODE I HAVE TO PROPERLY RENDER THEM
        # Add enemy to the sprites to render if in FOV
        if hasattr(app, 'enemy') and not app.enemy.stunned:  # Only process if not stunned
            enemyProps = app.enemy.calculate3dProperties(self.player)
            if enemyProps['inFov'] and enemyProps['distance'] < spriteRenderDistance:
                spritesToRender.append({
                    'type': 'enemy',
                    'distance': enemyProps['distance'],
                    'angle': enemyProps['angle']
                })
        
        # CONTINUED CITATION FROM ABOVE
        if hasattr(app, 'collectibles'):
            for collectible in app.collectibles:
                if collectible.collected:
                    continue
                        
                # Skip calculation if already known to be far away
                approxDist = ((collectible.x - self.player.x)**2 + 
                            (collectible.y - self.player.y)**2)**0.5
                            
                if approxDist > spriteRenderDistance * 1.2:  # Add margin
                    continue
                    
                # Get 3D properties of the collectible
                props = collectible.calculate3dProperties(self.player)
                
                # Only render sprites that are in FOV and within render distance
                if props['inFov'] and props['distance'] < spriteRenderDistance:
                    spritesToRender.append({
                        'type': 'collectible',
                        'collectible': collectible,
                        'distance': props['distance'],
                        'angle': props['angle']
                    })
        
        # Skip if nothing to render
        if not spritesToRender:
            return
        # CITATION: AI ASSISTANCE
        # PROMPT: IM TRYING TO USE THE LAMBDA FUNCTION HERE BUT IM DOING IT WRONG CAN YOU HELP    
        # Sort sprites by distance (furthest first for proper rendering)
        spritesToRender.sort(key=lambda x: x['distance'], reverse=True)
            
        # Render the sorted sprites
        for sprite in spritesToRender:
            distance = sprite['distance']
            angle = sprite['angle']
            
            # Calculate sprite position in screen space
            angleDiff = angle - self.player.rotationAngle
            
            # Calculate the screen x position
            spriteScreenX = int((windowWidth / 2) + 
                            math.tan(angleDiff) * 
                            (windowWidth / 2 / math.tan(fov / 2)))
            
            if sprite['type'] == 'enemy':
                # Calculate enemy sprite height based on distance
                spriteHeight = int((tileSize * 1.5 / distance) * projectionDistance)
                spriteWidth = spriteHeight  # Square aspect ratio for enemy
                
                # Calculate y position - place it on the floor
                spriteScreenY = windowHeight / 2 + spriteHeight / 4
                
                # Check if this sprite is occluded by walls!!
                # Calculate the column range this sprite is in
                leftColumn = max(0, int((spriteScreenX - spriteWidth/2) / res))
                rightColumn = min(numRays-1, 
                                int((spriteScreenX + spriteWidth/2) / res))
                
                # Don't render if fully occluded
                fullyOccluded = True
                
                for screenColumn in range(leftColumn, rightColumn + 1):
                    # Check if this column of the sprite is behind a wall
                    if screenColumn >= 0 and screenColumn < len(self.zBuffer):
                        if distance < self.zBuffer[screenColumn]:
                            fullyOccluded = False
                            break
                
                if fullyOccluded:
                    continue  # Skip rendering this sprite
                # CITATION: AI HELP
                # PROMPT: HELP ME IMPLEMENT A FOG EFFECT TO THE PLAYERS VIEW
                # Apply distance-based fog effect
                distanceFactor = max(0.5, min(1.0, 1.5 / (distance / 300)))
                
                # Check if enemy is in flashlight beam :)
                centeredness = 1.0 - (abs(angleDiff) / (fov/2))
                brightnessFactor = 1.0
                
                if app.flashlightActive and app.flashlightBattery > 0 and centeredness > 0.7:
                    brightnessFactor = 1.5
                
                # Calculate opacity (make sure it stays within 0-100 range)
                opacity = min(95 * distanceFactor * brightnessFactor, 100)
                
                # Draw enemy as an image
                drawImage(
                    app.enemy.imageUrl,
                    spriteScreenX - spriteWidth/2,
                    spriteScreenY - spriteHeight/2,
                    width=spriteWidth,
                    height=spriteHeight,
                    opacity=opacity
                )
            # CITATION: AI USED, BUT MAINLY ME. MORE OF A PUSH IN THE RIGHT DIRECTION!
            # PROMPT: IM HAVING TROUBLE WITH THE DISTANCE CALCULATIONS WITH THE ZBUFFER. WITHOUT SHOWING ME HOW, HOW CAN I BEGIN TO SOLVE THE ISSUE WITH OCCLUSION    
            elif sprite['type'] == 'collectible':
                collectible = sprite['collectible']
                # Calculate sprite height based on distance
                spriteHeight = int((tileSize / distance) * projectionDistance)
                spriteWidth = spriteHeight * 0.7  # Paper is slightly narrower
                
                # Calculate y position and place it on the floor
                spriteScreenY = windowHeight / 2 + spriteHeight / 4
                
                # Check if this sprite is occluded by walls
                # Calculate the column range this sprite has
                leftColumn = max(0, int((spriteScreenX - spriteWidth/2) / res))
                rightColumn = min(numRays-1, 
                                int((spriteScreenX + spriteWidth/2) / res))
                
                # Don't render if fully occluded!
                fullyOccluded = True
                
                for screenColumn in range(leftColumn, rightColumn + 1):
                    # Check if this column of the sprite is behind a wall
                    if screenColumn >= 0 and screenColumn < len(self.zBuffer):
                        if distance < self.zBuffer[screenColumn]:
                            fullyOccluded = False
                            break
                
                if fullyOccluded:
                    continue  # Skip rendering this sprite
                
                # Apply fog effect to collectibles
                distanceFactor = max(0.5, min(1.0, 1.5 / (distance / 300)))
                
                # Make sure opacity stays within 0-100
                opacity = min(95 * distanceFactor, 100)
                
                drawImage(
                    'midterm.png',  
                    spriteScreenX - spriteWidth/2,
                    spriteScreenY - spriteHeight/2,
                    width=spriteWidth,
                    height=spriteHeight,
                    opacity=opacity
                )
            
