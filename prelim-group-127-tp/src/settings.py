import math

tileSize = 32
rows = 30
cols = 45

windowWidth = 1920
windowHeight = 1080

fov = 60 * (math.pi / 180)


res = 8  
numRays = windowWidth // res

# How tall or short the walls and sprites appear based on distance from player
projectionDistance = 800

