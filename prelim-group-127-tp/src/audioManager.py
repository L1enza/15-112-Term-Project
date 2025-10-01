from openal import oalOpen, oalQuit

# CITATION: READ WEBSITE/DOCUMENTATION
# URL: https://pypi.org/project/PyOpenAL/

class AudioManager:
    def __init__(self):
        self.sounds = {
            'menuClick': oalOpen('menuClick.wav'),
            'flashlight': oalOpen('flashlight.wav'),
            'jumpscare': oalOpen('newJumpscare.wav'),
            'menuTheme': oalOpen('menuTheme.wav'),
            'footsteps': oalOpen('footsteps.wav'),
            'collectSound': oalOpen('collectSound.wav'),
            'heartbeat': oalOpen('heartbeat.wav'),
            'chaseMusic': oalOpen('chaseMusic.wav'),
            'stun': oalOpen('stunSound.wav')
        }
        self.looping = None
    def play(self, name):
        if name in self.sounds:
            self.sounds[name].play()

    def loop(self, name):
        if self.looping and self.looping != name:
            self.stop(self.looping)
        if name in self.sounds:
            self.sounds[name].set_looping(True)
            self.sounds[name].play()
            self.looping = name

    def stop(self, name):
        if name in self.sounds:
            self.sounds[name].stop()
        if self.looping == name:
            self.looping = None

    def stopAll(self):
        for sound in self.sounds.values():
            sound.stop()
        self.looping = None


    def cleanup(self):
        oalQuit()
