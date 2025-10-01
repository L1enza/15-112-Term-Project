from cmu_graphics import *
from settings import *
from audioManager import AudioManager
import math
import random
from map import Map
from player import Player
from raycaster import Raycaster
from collectible import Collectible
from enemy import Enemy
from openal import oalOpen

def onAppStart(app):

    # Load menu and enemy images first
    app.menuImage = 'menu.jpg'
    app.kosbieImage = 'kosbie.png'
    app.austinImage = 'austin.jpg'
    
    # Initialize menu state
    app.inMenu = True
    app.inSettings = False
    app.inHowToPlay = False
    app.enemyType = 'kosbie'  # Default enemy is Kosbie

    app.audio = AudioManager()
    app.enemySound = oalOpen('menuTheme.wav')  # THIS ACTUALLY PLAYS THE MENU MUSIC, DO NOT BE CONFUSED!!!!!!!! 
    app.enemySound.set_looping(True)
    ambienceUrl = 'ambience.mp3'
    app.ambienceSound = Sound(ambienceUrl)
    chaseUrl = 'chaseMusic.wav'
    app.chaseSound = Sound(chaseUrl)
    heartbeatUrl = 'heartbeat.wav'
    app.heartbeat = Sound(heartbeatUrl)

    resetGame(app)
    app.setMaxShapeCount(5000)  # shape limit? cmu graphics yelled at me.
    app.stepsPerSecond = 60    #FPS

def resetGame(app):
    app.width = windowWidth
    app.height = windowHeight

    app.map = Map()
    app.player = Player()
    app.audio.stopAll()
    app.enemySound.play()
    app.soundPause = True
    app.checker = 0
    app.ambienceSound.play(restart = True)

    if app.inMenu or app.inSettings or app.inHowToPlay or app.gameOver:
        app.soundPause = True
    else:
        app.soundPause = False
    
    if app.soundPause:
        if app.checker > 0:
            if not app.doorCreated:
                app.ambienceSound.play(restart = True)
    else:
        app.checker += 1
        if not app.doorCreated:
            app.ambienceSound.play(restart = True)
        
    app.map = Map()          # Map must be created first
    app.player = Player()    # Player created after

    app.flashlightActive = False
    app.flashlightBattery = 100  # Battery percentage (0-100)
    app.flashlightDrainRate = 4.0  # How fast the battery drains per step
    app.flashlightRechargeRate = 0.25  # How fast the battery recharges when off
    app.stunEffect = 0
    
    # Find a valid spawn position for the player
    while True:
        gridX = random.randint(0, cols - 1)
        gridY = random.randint(0, rows - 1)

        if (0 <= gridY < len(app.map.grid)) and (0 <= gridX < len(app.map.grid[0])):
            if app.map.grid[gridY][gridX] == 0:
                break

    app.player.x = gridX * tileSize + tileSize / 2
    app.player.y = gridY * tileSize + tileSize / 2

    app.raycaster = Raycaster(app.player, app.map)
    app.keys = set()
    app.stepsPerSecond = 60
    app.show2d = False

    app.lastMouseX = None
    app.lastMouseY = None
    
    # Initialize collectibles
    app.collectibles = []
    app.keysCollected = 0
    app.totalKeys = 5
    
    # Spawn 5 exam keys
    for _ in range(app.totalKeys):
        app.collectibles.append(Collectible(app.map))
    
    # Create enemy after player and map are initialized
    app.enemy = Enemy(app.map, app.player)
    
   
    app.enemy.imageUrl = 'austin.jpg' if app.enemyType == 'austin' else 'kosbie.png'

    # caught state
    app.caught = False
    
    # Win condition animation
    app.winPulse = 0
    app.winPulseDirection = 1
    
    # Escape door (initially not active)
    app.escapeDoor = None
    app.doorCreated = False
    
    # Game state
    app.gameOver = False

def createEscapeDoor(app):
    # Choose a random position on the outer wall, but not a corner
    outerPositions = []
    
    # Top and bottom walls, excluding corners
    for x in range(1, cols-1):
        outerPositions.append((x, 0))  # Top wall
        outerPositions.append((x, rows-1))  # Bottom wall
    
    # Left and right walls, excluding corners
    for y in range(1, rows-1):
        outerPositions.append((0, y))  # Left wall
        outerPositions.append((cols-1, y))  # Right wall
    
    # Pick a random position
    doorPos = random.choice(outerPositions)
    
    # Create the door (replace wall with a "2" value in the grid)
    app.map.grid[doorPos[1]][doorPos[0]] = 2
    
    # Store door position for collision detection
    app.escapeDoor = {
        'x': doorPos[0] * tileSize + tileSize / 2,
        'y': doorPos[1] * tileSize + tileSize / 2
    }

def checkDoorCollision(app):
    if app.escapeDoor is None:
        return False
    
    # Check if player is close to the door
    doorX = app.escapeDoor['x']
    doorY = app.escapeDoor['y']
    
    distance = math.sqrt((app.player.x - doorX)**2 + (app.player.y - doorY)**2)
    if distance < tileSize:
        return True
    
    return False

def onStep(app):
    if app.inMenu or app.inSettings or app.inHowToPlay:
        return
    # Don't process steps if in menu or settings or how to play
    if app.gameOver or app.caught:
        return
    
    app.player.update(app)
    
    # Update stun effect counter if active
    if app.stunEffect > 0:
        app.stunEffect -= 1
    

    app.enemy.checkFlashlightStun(app)
    app.enemy.update(app)
    
    app.raycaster.castAllRays()
    
    # Check if player has been caught but only if enemy is not stunned
    if not app.enemy.stunned and app.enemy.checkCollision(app.player):
        app.caught = True
    
    
    # Update flashlight battery
    if app.flashlightActive and app.flashlightBattery > 0:
        app.flashlightBattery = max(0, app.flashlightBattery - app.flashlightDrainRate)
        if app.flashlightBattery == 0:
            app.flashlightActive = False
    elif not app.flashlightActive and app.flashlightBattery < 100:
        app.flashlightBattery = min(100, app.flashlightBattery + app.flashlightRechargeRate)
    
    # Check if player has collected any keys
    for collectible in app.collectibles:
        if collectible.checkCollection(app.player):
            app.keysCollected += 1
            app.audio.play('collectSound')
    
    # CITATION: AI USED TO CORRECT THE ANIMATION
    # PROMPT: MY WIN CONDITION ANIMATION WONT PULSE PROPERLY, CAN YOU IMPLEMENT A FIX FOR THIS
    
    # Animate the win message if all keys are collected
    if app.keysCollected >= app.totalKeys:
        app.ambienceSound.pause()
        app.enemy.speed = 5.5
        app.winPulse += 0.05 * app.winPulseDirection
        if app.winPulse >= 1:
            app.winPulse = 1
            app.winPulseDirection = -1
        elif app.winPulse <= 0.5:
            app.winPulse = 0.5
            app.winPulseDirection = 1
        
        # Create escape door if all keys collected and not created yet
        if not app.doorCreated:
            createEscapeDoor(app)
            app.doorCreated = True
            app.chaseSound.play(restart = True)
            app.heartbeat.play(restart = True)
            if app.gameOver or app.caught:
                app.chaseSound.pause()
                app.heartbeat.pause()
                

    
    # Check if player has reached the escape door
    if app.doorCreated and checkDoorCollision(app):
        app.gameOver = True
        app.chaseSound.pause()
        app.heartbeat.pause()
    if app.caught:
        app.audio.play('jumpscare')
        if app.doorCreated:
            app.chaseSound.pause()
            app.heartbeat.pause()

def drawMainMenu(app):
    # Draw menu background image
    drawImage(app.menuImage, 0, 0, width=app.width, height=app.height)
    
    # Draw Start button
    startButtonWidth = 300
    startButtonHeight = 80
    startButtonX = app.width / 2 - startButtonWidth / 2
    startButtonY = app.height / 2
    
    drawRect(startButtonX, startButtonY, startButtonWidth, startButtonHeight, 
             fill='khaki', opacity=50)
    drawLabel("START", app.width / 2, startButtonY + startButtonHeight / 2,
             size=36, bold=True, fill='black')
    
    # Draw Settings button
    settingsButtonWidth = 300
    settingsButtonHeight = 80
    settingsButtonX = app.width / 2 - settingsButtonWidth / 2
    settingsButtonY = app.height / 2 + 120
    
    drawRect(settingsButtonX, settingsButtonY, settingsButtonWidth, settingsButtonHeight, 
             fill='khaki', opacity=50)
    drawLabel("SETTINGS", app.width / 2, settingsButtonY + settingsButtonHeight / 2,
             size=36, bold=True, fill='black')
    
    # Draw How To Play button
    howToPlayButtonWidth = 300
    howToPlayButtonHeight = 80
    howToPlayButtonX = app.width / 2 - howToPlayButtonWidth / 2
    howToPlayButtonY = app.height / 2 + 240  
    
    drawRect(howToPlayButtonX, howToPlayButtonY, howToPlayButtonWidth, howToPlayButtonHeight, 
             fill='khaki', opacity=50)
    drawLabel("HOW TO PLAY", app.width / 2, howToPlayButtonY + howToPlayButtonHeight / 2,
             size=36, bold=True, fill='black')


def drawHowToPlayMenu(app):
    # Draw low opacity overlay
    drawImage(app.menuImage, 0, 0, width=app.width, height=app.height)
    drawRect(0, 0, app.width, app.height, fill='black', opacity=80)
    
    # Draw how to play button
    drawLabel("HOW TO PLAY", 
              app.width / 2, app.height / 6,
              size=60, bold=True,
              fill='white')
    
    descriptionText = """
Oh no! You're trapped inside the 112Rooms, a dark, mysterious, and haunting maze
that seems endless. The only way you can escape is to collect five exam keys
across the map, and find the exit. There's only one problem... something tells you
that you aren't alone in there. Avoid the enemy, and use your flashlight to stun him
if he's near. Be careful; your flashlight has very limited battery and it regenerates
quite slowly. Once you collect all the exam keys, check the map for a green door at an 
edge of the map. You must escape from there. Watch out; your enemy's speed will greatly
increase once all keys are collected. Good luck! 
    """
    
   
    textX = app.width / 2
    textY = app.height / 3
    lineHeight = 30
    
    # Draw each line
    lines = descriptionText.strip().split('\n')
    for i, line in enumerate(lines):
        drawLabel(line, textX, textY + i * lineHeight, 
                 size=20, bold=False, fill='white', align='center')
    
    # Draw controls header
    drawLabel("CONTROLS:", 
              app.width / 2, textY + len(lines) * lineHeight + 40,
              size=30, bold=True, fill='white')
    
    # Draw controls text
    controlsText = """
REMEMBER THESE. 
There is no pausing when you are in-game. 
You can't pause your life just because you're in trouble...
    
Movement - WASD or arrow keys
Flashlight - F (must be holding down key, looking directly at the enemy)
Map View - Tab
Reset to Main Menu - Esc
Look Left and Right - Mouse
    """
    
    # Draw the controls text
    controlsY = textY + len(lines) * lineHeight + 80
    controlLines = controlsText.strip().split('\n')
    for i, line in enumerate(controlLines):
        drawLabel(line, textX, controlsY + i * lineHeight, 
                 size=20, bold=False, fill='white', align='center')
    
    # Draw Back button
    backButtonWidth = 200
    backButtonHeight = 60
    backButtonX = app.width / 2 - backButtonWidth / 2
    backButtonY = app.height - 120
    
    drawRect(backButtonX, backButtonY, backButtonWidth, backButtonHeight, 
             fill='khaki', opacity=70)
    drawLabel("BACK", backButtonX + backButtonWidth / 2, backButtonY + backButtonHeight / 2,
             size=24, bold=True, fill='black')

def drawSettingsMenu(app):
    drawImage(app.menuImage, 0, 0, width=app.width, height=app.height)
    drawRect(0, 0, app.width, app.height, fill='black', opacity=80)
    drawLabel("SETTINGS", 
              app.width / 2, app.height / 4,
              size=60, bold=True,
              fill='white')
    
    # Draw enemy selection 
    drawLabel("Choose Enemy:", 
              app.width / 2, app.height / 2 - 100,
              size=30, bold=True,
              fill='white')
    
    # Draw Kosbie button
    kosbieButtonWidth = 200
    kosbieButtonHeight = 60
    kosbieButtonX = app.width / 2 - 220
    kosbieButtonY = app.height / 2
    
    # Highlight the selected option
    kosbieButtonColor = 'red' if app.enemyType == 'kosbie' else 'khaki'
    
    drawRect(kosbieButtonX, kosbieButtonY, kosbieButtonWidth, kosbieButtonHeight, 
             fill=kosbieButtonColor, opacity=70)
    drawLabel("KOSBIE", kosbieButtonX + kosbieButtonWidth / 2, kosbieButtonY + kosbieButtonHeight / 2,
             size=24, bold=True, fill='black')
    
    # Draw Austin button
    austinButtonWidth = 200
    austinButtonHeight = 60
    austinButtonX = app.width / 2 + 20
    austinButtonY = app.height / 2
    
    # Highlight the selected option
    austinButtonColor = 'red' if app.enemyType == 'austin' else 'khaki'
    
    drawRect(austinButtonX, austinButtonY, austinButtonWidth, austinButtonHeight, 
             fill=austinButtonColor, opacity=70)
    drawLabel("AUSTIN", austinButtonX + austinButtonWidth / 2, austinButtonY + austinButtonHeight / 2,
             size=24, bold=True, fill='black')
    
    # Draw Back button
    backButtonWidth = 200
    backButtonHeight = 60
    backButtonX = app.width / 2 - backButtonWidth / 2
    backButtonY = app.height / 2 + 120
    
    drawRect(backButtonX, backButtonY, backButtonWidth, backButtonHeight, 
             fill='khaki', opacity=70)
    drawLabel("BACK", backButtonX + backButtonWidth / 2, backButtonY + backButtonHeight / 2,
             size=24, bold=True, fill='black')

def redrawAll(app):
    if app.inMenu:
        drawMainMenu(app)
        return
        
    if app.inSettings:
        drawSettingsMenu(app)
        return
        
    if app.inHowToPlay: 
        drawHowToPlayMenu(app)
        return
    
    if app.caught:
        # Draw "caught" screen
        drawRect(0, 0, app.width, app.height, fill='black')
        
        drawLabel("YOU'VE BEEN CAUGHT!", 
                  app.width / 2, app.height / 2 - 100,
                  size=80, bold=True, italic=True,
                  fill='red', border='black')
        
        # Draw restart button
        buttonWidth = 300
        buttonHeight = 80
        buttonX = app.width / 2 - buttonWidth / 2
        buttonY = app.height / 2 + 80
        
        drawRect(buttonX, buttonY, buttonWidth, buttonHeight, 
                 fill='white', opacity=70)
        drawLabel("RESTART", app.width / 2, buttonY + buttonHeight / 2,
                 size=36, bold=True, fill='black')
       
        return

    if app.gameOver:
        # Draw game over screen
        drawRect(0, 0, app.width, app.height, fill='black')
        
        drawLabel("YOU ESCAPED THE 112ROOMS!", 
                  app.width / 2, app.height / 2 - 100,
                  size=80, bold=True, italic=True,
                  fill='red', border='black')
        
        # Draw restart button
        buttonWidth = 300
        buttonHeight = 80
        buttonX = app.width / 2 - buttonWidth / 2
        buttonY = app.height / 2 + 80
        
        drawRect(buttonX, buttonY, buttonWidth, buttonHeight, 
                 fill='white', opacity=70)
        drawLabel("RESTART", app.width / 2, buttonY + buttonHeight / 2,
                 size=36, bold=True, fill='black')
        
        return

    # Draw ceiling 
    ceilingColor1 = rgb(40, 35, 10)
    ceilingColor2 = rgb(60, 50, 15)  
    drawRect(0, 0, app.width, app.height/2, 
             fill=gradient(ceilingColor1, ceilingColor2, start='top'))
    
    # Draw floor
    floorColor1 = rgb(50, 40, 15)  
    floorColor2 = rgb(30, 25, 10)  
    drawRect(0, app.height/2, app.width, app.height/2, 
             fill=gradient(floorColor1, floorColor2, start='top'))
    
    # Draw the game in a 3D or 2D view
    if app.show2d:
        app.map.render(app)
        app.player.render(app)
        app.enemy.render(app)  # Render the enemy in 2D view
        
        # Render collectibles in 2D view
        for collectible in app.collectibles:
            collectible.render(app)
            
        for ray in app.raycaster.rays:
            ray.render(app)
    else:
        app.raycaster.render(app)
        app.raycaster.renderSprites(app)  # Render 3D collectibles and enemy
    
    if not app.show2d:
        # Draw Exam Keys counter
        drawRect(20, 20, 300, 50, fill='white', opacity=80)
        drawLabel(f"Exam Keys Collected: {app.keysCollected}/{app.totalKeys}", 
                170, 45, size=20, bold=True, fill='black')
        
        # Draw flashlight battery meter 
        drawRect(20, 80, 300, 50, fill='white', opacity=80)
        # Border for battery
        drawRect(25, 92, 290, 25, fill=None, border='black', borderWidth=2)
        
        # CITATION: AI ASSISTANCE IN BATTERY DRAIN 
        # PROMPT: HELP FIX THIS ISSUE. BATTERY DRAIN ISNT WORKING
        batteryWidth = (app.flashlightBattery / 100) * 286
        if batteryWidth > 0:
            drawRect(27, 94, batteryWidth, 21, fill='green' if not app.flashlightActive else 'yellow')
        
        drawLabel("Flashlight Battery", 170, 104, 
                size=18, bold=True, fill='black')
    
    # Show ESCAPE message when all keys are collected
    # CITATION: AI ASSISTANCE IN SIZE FACTOR AND OPACITY
    # PROMPT: THIS ISNT PROPERLY CHANGING THE SIZE BUT THE OPACITY WORKS. PLEASE FIX
    if app.keysCollected >= app.totalKeys:
        # Pulsing size and transparency for animation effect
        sizeFactor = 50 + 15 * app.winPulse 
        opacity = 100 * app.winPulse
        
        # Draw the escape message
        drawLabel("ESCAPE", 
                  app.width / 2, 120, 
                  size=sizeFactor,
                  bold=True,
                  italic=True,
                  fill='red', border='black',
                  opacity=opacity)

def onKeyPress(app, key):
    # Don't process key presses if in menu mode
    if app.inMenu or app.inSettings or app.inHowToPlay:
        return
        
    if app.gameOver or app.caught:
        return
        
    if key == 'tab':
        app.show2d = not app.show2d
    
    if key == 'w' or key == 'up':
        app.player.moveDirection = 1
    elif key == 's' or key == 'down':
        app.player.moveDirection = -1
    
    elif key == 'a' or key == 'left':
        app.player.strafeDirection = -1
    elif key == 'd' or key == 'right':
        app.player.strafeDirection = 1
    
    # Flashlight control
    elif key == 'f' and app.flashlightBattery > 0:
        app.flashlightActive = True
        app.audio.play('flashlight')
    
    if not app.inMenu or (not app.inSettings):
        if key == 'escape':
            app.ambienceSound.pause()
            app.inMenu = True
            resetGame(app)
    
    




def onKeyRelease(app, key):
    # Don't process key releases if in menu mode
    if app.inMenu or app.inSettings or app.inHowToPlay:
        return
        
    if app.gameOver or app.caught:
        return
        
    # Reset movement when specific keys are released
    if key in ['w', 'up', 's', 'down']:
        app.player.moveDirection = 0
    if key in ['a', 'left', 'd', 'right']:
        app.player.strafeDirection = 0
    
    # Turn off flashlight when F is released
    if key == 'f':
        app.flashlightActive = False
    
    # Remove the released key from tracked keys
    if key in app.keys:
        app.keys.remove(key)
    app.audio.stop('footsteps')
    
def onKeyHold(app, keys):
    if app.inMenu or app.inSettings or app.gameOver or app.caught or app.inHowToPlay:
        return
    
    # Check if any movement key is being held
    # CITATION: USED AI TO FIX ISSUE WITH FOOTSTEP SOUND
    # PROMPT: FOOTSTEP SOUND ISNT WORKING, SOUND IS NOT PLAYING EVEN WHEN MOVEMENT KEYS ARE HELD, FIX THIS
    
    movementKeys = ['w', 'up', 's', 'down', 'a', 'left', 'd', 'right']
    if any(key in keys for key in movementKeys):
        # Only play footsteps if not already looping
        if app.audio.looping != 'footsteps':
            app.audio.loop('footsteps')

    
    app.keys = keys



def onMouseMove(app, mouseX, mouseY):
    if app.inMenu or app.inSettings or app.inHowToPlay:
        return
        
    if app.gameOver or app.caught:
        return
        
    if app.lastMouseX is not None:
        dx = mouseX - app.lastMouseX
        sensitivity = 0.008

        app.player.rotationAngle += dx * sensitivity
        app.player.rotationAngle %= 2 * math.pi

    app.lastMouseX = mouseX
    app.lastMouseY = mouseY

def onMousePress(app, mouseX, mouseY):
    if app.inMenu or app.inSettings or app.inHowToPlay:  # Update condition
        app.audio.play('menuClick')

    if app.inMenu:
        # checking for button clicks
        startButtonWidth = 300
        startButtonHeight = 80
        startButtonX = app.width / 2 - startButtonWidth / 2
        startButtonY = app.height / 2

        settingsButtonWidth = 300
        settingsButtonHeight = 80
        settingsButtonX = app.width / 2 - settingsButtonWidth / 2
        settingsButtonY = app.height / 2 + 120
        
        howToPlayButtonWidth = 300
        howToPlayButtonHeight = 80
        howToPlayButtonX = app.width / 2 - howToPlayButtonWidth / 2
        howToPlayButtonY = app.height / 2 + 240

        if (startButtonX <= mouseX <= startButtonX + startButtonWidth and 
            startButtonY <= mouseY <= startButtonY + startButtonHeight):
            app.inMenu = False
            app.audio.stop('menuTheme')
            app.enemySound.stop()
            resetGame(app)
            return

        if (settingsButtonX <= mouseX <= settingsButtonX + settingsButtonWidth and 
            settingsButtonY <= mouseY <= settingsButtonY + settingsButtonHeight):
            app.inMenu = False
            app.inSettings = True
            return
            
        if (howToPlayButtonX <= mouseX <= howToPlayButtonX + howToPlayButtonWidth and 
            howToPlayButtonY <= mouseY <= howToPlayButtonY + howToPlayButtonHeight):
            app.inMenu = False
            app.inHowToPlay = True
            return

        return

    if app.inSettings:
        backButtonWidth = 200
        backButtonHeight = 60
        backButtonX = app.width / 2 - backButtonWidth / 2
        backButtonY = app.height / 2 + 120

        if (backButtonX <= mouseX <= backButtonX + backButtonWidth and 
            backButtonY <= mouseY <= backButtonY + backButtonHeight):
            app.inSettings = False
            app.inMenu = True
            app.audio.stopAll()
            app.audio.loop('menuTheme')
            return
        
    if app.inHowToPlay:
        backButtonWidth = 200
        backButtonHeight = 60
        backButtonX = app.width / 2 - backButtonWidth / 2
        backButtonY = app.height - 120
        
        if (backButtonX <= mouseX <= backButtonX + backButtonWidth and 
            backButtonY <= mouseY <= backButtonY + backButtonHeight):
            app.inHowToPlay = False
            app.inMenu = True
            return

    if app.gameOver or app.caught:
        buttonWidth = 300
        buttonHeight = 80
        buttonX = app.width / 2 - buttonWidth / 2
        buttonY = app.height / 2 + 80
        app.audio.stopAll()

        if (buttonX <= mouseX <= buttonX + buttonWidth and 
            buttonY <= mouseY <= buttonY + buttonHeight):
            resetGame(app)
    
    # settings menu button clicks
    if app.inSettings:
        # Kosbie button
        kosbieButtonWidth = 200
        kosbieButtonHeight = 60
        kosbieButtonX = app.width / 2 - 220
        kosbieButtonY = app.height / 2
        
        if (kosbieButtonX <= mouseX <= kosbieButtonX + kosbieButtonWidth and 
            kosbieButtonY <= mouseY <= kosbieButtonY + kosbieButtonHeight):
            app.enemyType = 'kosbie'
            return
            
        # Austin button
        austinButtonWidth = 200
        austinButtonHeight = 60
        austinButtonX = app.width / 2 + 20
        austinButtonY = app.height / 2
        
        if (austinButtonX <= mouseX <= austinButtonX + austinButtonWidth and 
            austinButtonY <= mouseY <= austinButtonY + austinButtonHeight):
            app.enemyType = 'austin'
            return
            
        # Back button
        backButtonWidth = 200
        backButtonHeight = 60
        backButtonX = app.width / 2 - backButtonWidth / 2
        backButtonY = app.height / 2 + 120
        
        if (backButtonX <= mouseX <= backButtonX + backButtonWidth and 
            backButtonY <= mouseY <= backButtonY + backButtonHeight):
            app.inSettings = False
            app.inMenu = True
            return
            
        return
    
    if app.gameOver or app.caught:
        # Check if restart button was clicked 
        buttonWidth = 300
        buttonHeight = 80
        buttonX = app.width / 2 - buttonWidth / 2
        buttonY = app.height / 2 + 80
        app.audio.stopAll()

        app.chaseSound.pause()
        app.heartbeat.pause()
        if (buttonX <= mouseX <= buttonX + buttonWidth and 
            buttonY <= mouseY <= buttonY + buttonHeight):
            resetGame(app)
        
#this is the final code
def main():
    runApp()

main()
