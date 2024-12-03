import json
import os
import re
import vlc
import urllib.parse
import urllib.request
import yt_dlp
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.uix.checkbox import CheckBox
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.textinput import TextInput
from kivy.uix.image import AsyncImage
from kivy.uix.slider import Slider
import random as rd
import time
from kivy.core.window import Window
Window.size = (300, 600)

class Video:
    def __init__(self, info: dict):
        for key,val in info.items():
            setattr(self, key, val)

class CustomTextInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, None)
        self.height = 35
        self.readonly = True
        self.background_color = (0,0,0,1)
        self.foreground_color = (1,1,1,1)
        self.multiline = False

class MusicPlayer(App):
    def build(self):
        self.curPlayList = None
        self.updatingTime = True
        self.man = ScreenManager()
        self.med = vlc.MediaPlayer()
        self.curson = None
        self.paused = False
        self.speed = 1
        self.currentLabel = None
        self.loop = False
        self.queue = []
        self.url = ""
        self.doingSomething = False
        self.playingPlaylist = False
        self.playlistButtonDict = {}
        self.buttons = {}
        os.chdir("\\".join(os.path.abspath(__file__).split("\\")[:-1]))
        if "settings.json" in os.listdir():
            with open("settings.json", "r") as f:
                self.playlists = json.load(f)["Playlists"]
        else:
            with open("settings.json", "x") as f:
                json.dump({}, f)
                self.playlists = {}


        for name in ["main", "play", "playlists", "playlist", "queue"]:
            self.man.add_widget(Screen(name = name))
        layout = BoxLayout(orientation = "vertical")
        first = BoxLayout(orientation='vertical', spacing=1)
        inner = BoxLayout(orientation="horizontal")
        d = {"Rewind": lambda x: self.rewind(), "Pause": self.pause,
             "Play Song": self.playSong, "Skip": lambda x: self.med.stop()}
        for key, val in d.items():
            a = AnchorLayout(anchor_x='center', anchor_y='top')
            b = Button(text=key, size_hint=(1, 1))
            b.bind(on_release=val)
            a.add_widget(b)
            inner.add_widget(a)
            self.buttons[key] = b
        first.add_widget(inner)

        inner = BoxLayout(orientation="horizontal")
        d = {"Add to Queue": lambda x: self.playSong(
            x, "Q"), "Playlists": lambda x: self.playlistsGUI(), "loop (off)": self.toggleLoop}
        for key, val in d.items():
            a = AnchorLayout(anchor_x='left', anchor_y='top')
            b = Button(text=key, size_hint=(1, 1))
            b.bind(on_release=val)
            a.add_widget(b)
            inner.add_widget(a)
            self.buttons[key] = b
        first.add_widget(inner)
        layout.add_widget(first)

        self.imgLayout = AnchorLayout(anchor_x = 'left', anchor_y = 'center')
        layout.add_widget(self.imgLayout)
        self.currentLabel = Label()
        a = AnchorLayout(anchor_y='top')
        self.authorLabel = Label(text="", font_size="11sp")
        layout.add_widget(self.currentLabel)
        a.add_widget(self.authorLabel)
        layout.add_widget(a)
        self.man.current_screen.add_widget(layout)

        self.timeLabel = Label(text = "00:00:00 / 00:00:00")
        self.timeSlider = Slider(min=0, max=0, step=1, orientation='horizontal', value=0)
        self.timeSlider.bind(on_touch_move=self.timeStop)

        layout.add_widget(self.timeLabel)
        layout.add_widget(self.timeSlider)

        lastLayout = BoxLayout(orientation="horizontal")

        layoutLeft = BoxLayout(orientation='vertical')
        speedSlider = Slider(min=0.5, max=2, step=0.05, orientation='horizontal', value=1)
        speedSlider.bind(value=self.updateSpeed)
        self.speedLabel = Label(text="Speed: 1.00x")
        layoutLeft.add_widget(self.speedLabel)
        layoutLeft.add_widget(speedSlider)
        lastLayout.add_widget(layoutLeft)


        layoutRight = BoxLayout(orientation='vertical')
        volSlider = Slider(min=0, max=100, step=1, orientation='horizontal', value=100)
        volSlider.bind(value=self.updateVol)
        self.volLabel = Label(text="Volume: 100%")
        layoutRight.add_widget(self.volLabel)
        layoutRight.add_widget(volSlider)
        lastLayout.add_widget(layoutRight)


        layout.add_widget(lastLayout)
        Clock.schedule_once(lambda x: self.checking(), 1)
        return self.man
    
    def rewind(self):
        if self.queue:
            self.med.stop()
            try:
                self.queue = self.queue[-2:] + self.queue[:-2]
            except Exception as e:
                print(e)
                self.queue.insert(0, self.queue.pop(-1))
        else:
            self.med.set_time(0)
    
    def timeContinue(self, slider, mouse):
        self.timeSlider.unbind(on_touch_up=self.timeContinue)
        sec=slider.value
        self.med.set_time(int(1000*sec))
        sec = int(sec)
        mins=sec//60;sec%=60
        hr=mins//60;mins%=60
        osec=int(self.med.get_length()/1000)
        omin=osec//60;osec%=60
        ohr=omin//60;omin%=60        
        self.timeLabel.text = "{0}:{1}:{2} / {3}:{4}:{5}".format(str(hr).zfill(2), str(mins).zfill(2), str(
            sec).zfill(2), str(ohr).zfill(2), str(omin).zfill(2), str(osec).zfill(2)).replace(".", "")
        Clock.schedule_once(lambda x: self.timeReset(), 1)
        self.timeSlider.bind(on_touch_move=self.timeStop)

    def timeReset(self):
        self.updatingTime = True        

    def timeStop(self, thing, inst):
        if self.updatingTime and inst.pos[1]<155 and inst.pos[1]>115:
            self.timeSlider.unbind(value=self.timeStop)
            self.updatingTime = False
            self.timeSlider.bind(on_touch_up=self.timeContinue)
    
    def updateTime(self):
        sec = int(self.med.get_time()/1000)
        if self.updatingTime:
            self.timeSlider.value = sec
        mins = sec//60
        sec %= 60
        hr = mins//60
        mins %= 60
        osec = int(self.med.get_length()/1000)
        omin = osec//60
        osec %= 60
        ohr = omin//60
        omin %= 60
        self.timeLabel.text = "{0}:{1}:{2} / {3}:{4}:{5}".format(str(hr).zfill(2), str(mins).zfill(2), str(
            sec).zfill(2), str(ohr).zfill(2), str(omin).zfill(2), str(osec).zfill(2)).replace(".", "")
  
    def updateVol(self, instance, volume):
        self.volLabel.text = "Volume: {:.0f}%".format(volume)
        self.med.audio_set_volume(int(volume))
    
    def updateSpeed(self, instance, speed):
        self.speedLabel.text = "Speed: {:.2f}x".format(speed)
        self.med.set_rate(speed)
    
    def toggleLoop(self, event = None):
        self.loop = not self.loop
        event.text = "loop " + ("(on)" if self.loop else "(off)")
    
    def playSong(self, event = None, _type = "Play"):
        self.man.current = "play"
        self.man.current_screen.clear_widgets()
        self.playGUI(_type)

    def playGUI(self, _type):
        layout = BoxLayout(orientation = 'vertical')
        a = AnchorLayout(anchor_x = 'center', anchor_y = 'top', height = 5)
        
        back = Button(text="Back", size_hint_x=None,
                     size_hint_y=None, width=40, height=15, size=(40, 15))
        back.bind(on_release=lambda x: self.backToMain(None, ""))
       
        t = TextInput(size_hint_y = None, height = 30, multiline=False)
        t.bind(on_text_validate = lambda txt: self.showResults(txt, _type))
        a.add_widget(t)
        layout.add_widget(back)
        layout.add_widget(a)
        anc = AnchorLayout(anchor_x = 'center', anchor_y = 'top')
        self.playSongLayout = BoxLayout(orientation = 'vertical')
        anc.add_widget(self.playSongLayout)
        layout.add_widget(anc)
        self.man.current_screen.add_widget(layout)

    def showResults(self, text, _type):
        self.ADDFUNCTIONS = []
        self.playDict = {}
        self.playSongLayout.clear_widgets()
        res = [*set(self.find(text.text)[:5])]
        for result in res:
            tot = AnchorLayout(anchor_x = 'center', anchor_y = 'top')
            subLayout = BoxLayout(orientation='horizontal')
            with yt_dlp.YoutubeDL({'extract_audio': True, 'format': 'bestaudio', 'outtmpl': '%(title)s.mp3'}) as video:
                while True:
                    try:
                        info = video.extract_info(f"https://www.youtube.com/watch?v={result}", download=False)
                        break
                    except AttributeError as e:
                        print(e)
            a = AnchorLayout(anchor_x = 'left', anchor_y = 'center')
            img = AsyncImage(source=info['thumbnail'])
            a.add_widget(img)
            subLayout.add_widget(a)
            innerLayout = BoxLayout(orientation = 'vertical')
            innerLayout.add_widget(Label(text=info['title'], font_size = "12sp"))
            a = AnchorLayout(anchor_x = 'center', anchor_y='top')
            a.add_widget(Label(text=info['uploader'], font_size = "10sp"))
            innerLayout.add_widget(a)
            subLayout.add_widget(innerLayout)
            a = AnchorLayout(anchor_y = 'center')
            self.ADDFUNCTIONS.append(lambda x: self.backToMain(x, _type))
            b = Button(text="Play" if _type=="Play" else "Add", size_hint_x = None, size_hint_y=None, width=40, height=10, size = (40,10))
            b.bind(on_release=self.ADDFUNCTIONS[-1])
            self.playDict[b] = [f"https://www.youtube.com/watch?v={result}", info['title'], info['uploader'], info['thumbnail']]
            a.add_widget(b)
            subLayout.add_widget(a)
            tot.add_widget(subLayout)
            self.playSongLayout.add_widget(tot)
    
    def playlistsGUI(self):
        self.man.current = "playlists"
        self.playlistButtonDict = {}
        self.man.current_screen.clear_widgets()
        layout = BoxLayout(orientation="vertical")
        horz = BoxLayout(orientation = "horizontal")
        but = Button(text="Back", size_hint_x = None, size_hint_y=None, width=40, height=10, size = (40,10))
        but.bind(on_release=lambda x: self.backToMain(None,""))
        horz.add_widget(but)
        add = Button(text="Add", size_hint_x = None, size_hint_y=None, width=40, height=10, size = (40,10))
        add.bind(on_release=lambda x: self.addPlaylist(layout))
        horz.add_widget(add)
        layout.add_widget(horz)
        for name,songs in self.playlists.items():
            a = AnchorLayout(anchor_y='top')
            inner = BoxLayout(orientation="horizontal")
            if songs:
                inner.add_widget(AsyncImage(source=songs[0][-1]))
            store = (name,)
            inner.add_widget(Label(text=name, font_size="15sp"))
            b = Button(text="View", size_hint_x = None, size_hint_y = None, width = 40, height = 15, size = (40,15))
            b.bind(on_release=self.playlistSingularGUI)
            self.playlistButtonDict[str(b)] = store
            inner.add_widget(b)
            b = Button(text="Play", size_hint_x = None, size_hint_y = None, width = 40, height = 15, size = (40,15))
            b.bind(on_release=self.playlistPlay)
            self.playlistButtonDict[str(b)] = store
            inner.add_widget(b)
            ba = Button(text="Shuffle", size_hint_x = None, size_hint_y = None, width = 60, height = 15, size = (60,15))
            ba.bind(on_release=self.playlistPlay)
            self.playlistButtonDict[str(ba)] = store
            inner.add_widget(ba)
            b = Button(text="Remove", size_hint_x=None, size_hint_y=None, width=60, height=15, size=(60, 15))
            b.bind(on_release=self.delPlaylist)
            self.playlistButtonDict[str(b)] = store
            inner.add_widget(b)

            a.add_widget(inner)
            layout.add_widget(a)
        self.man.current_screen.add_widget(layout)

    def addPlaylist(self, layout):
        t = TextInput(size_hint_y = None, height = 30, multiline=False)
        t.bind(on_text_validate = lambda txt: self.addNewPlaylist(txt.text))
        layout.add_widget(t)
    
    def addNewPlaylist(self, txt):
        if txt not in list(self.playlists.keys()):
            self.playlists[txt] = []
        Clock.schedule_once(lambda x: self.playlistsGUI(), 0.2)
    
    def playlistPlay(self, button, shuffle = False):
        self.doingSomething = True
        self.med.stop()
        randomize = button.text == "Shuffle" or shuffle
        self.queue.clear()
        self.backToMain(None, "")
        if randomize:
            q = self.playlists[self.playlistButtonDict[str(button)][0]].copy()
            rd.shuffle(q)
            self.queue = q
        else:
            self.queue = self.playlists[self.playlistButtonDict[str(button)][0]].copy()
        self.curPlayList = self.playlistButtonDict[str(button)][0]
        self.playingPlaylist = True
        self.resetLoopAndPause()
        Clock.schedule_once(self.reset, 0.8)
    
    def playlistSingularGUI(self, button):
        self.man.current = 'playlist'
        self.man.current_screen.clear_widgets()
        layout = BoxLayout(orientation = 'vertical')
        inner = BoxLayout(orientation = 'horizontal')
        inner.add_widget(Label(text = self.playlistButtonDict[str(button)][0], font_size = "15sp"))
        layout.add_widget(inner)
        images = len(self.playlists[self.playlistButtonDict[str(button)][0]]) <= 8
        for song in self.playlists[self.playlistButtonDict[str(button)][0]]:
            tot = AnchorLayout(anchor_x='center', anchor_y='top')
            subLayout = BoxLayout(orientation='horizontal')
            info = song[1:]
            song = song[0]
            if images:
                a = AnchorLayout(anchor_x='left', anchor_y='center')
                img = AsyncImage(source=info[2])
                a.add_widget(img)
                subLayout.add_widget(a)
            innerLayout = BoxLayout(orientation='vertical')
            innerLayout.add_widget(Label(text=info[0], font_size="12sp"))
            a = AnchorLayout(anchor_x='center', anchor_y='top')
            a.add_widget(Label(text=info[1], font_size="10sp"))
            innerLayout.add_widget(a)
            remove = Button(text="Remove", size_hint_y=None, height=20)
            remove.bind(on_release=self.removeFromPlaylist)
            subLayout.add_widget(innerLayout)
            subLayout.add_widget(remove)
            self.playlistButtonDict[str(remove)] = [self.playlistButtonDict[str(button)][0], str(song)]
            tot.add_widget(subLayout)
            layout.add_widget(tot)
        inner = BoxLayout(orientation='horizontal')
        b = Button(text="Back", size_hint_x=None, size_hint_y=None, width=50, height=20, size=(50, 20))
        b.bind(on_release=lambda x:self.playlistsGUI())
        inner.add_widget(b)
        b = Button(text="Play", size_hint_x=None, size_hint_y=None, width=50, height=20, size=(50, 20))
        b.bind(on_release=lambda x:self.playlistPlay(button))
        inner.add_widget(b)
        b = Button(text="Shuffle", size_hint_x=None, size_hint_y=None, width=80, height=20, size=(80, 20))
        b.bind(on_release=lambda x:self.playlistPlay(button, shuffle=True))
        inner.add_widget(b)
        b = Button(text="Add", size_hint_x=None, size_hint_y=None, width=40, height=20, size=(40, 20))
        b.bind(on_release=lambda x:self.addToPlaylist(self.playlistButtonDict[str(button)][0]))
        inner.add_widget(b)
        b = Button(text="Delete", size_hint_x=None, size_hint_y=None,
                   width=80, height=20, size=(80, 20))
        b.bind(on_release=lambda x: self.delPlaylist(
            self.playlistButtonDict[button][0]))
        inner.add_widget(b)
        layout.add_widget(inner)
        self.man.current_screen.add_widget(layout)
    
    def removeFromPlaylist(self, button):
        for song in self.playlists[self.playlistButtonDict[str(button)][0]]:
            if song[0] == self.playlistButtonDict[str(button)][1]:
                break
        self.playlists[self.playlistButtonDict[str(button)][0]].remove(song)
        if self.playingPlaylist and self.curPlayList == self.playlistButtonDict[str(button)][0]:
            self.queue.remove(song[0])
        self.updatePlaylist()
        self.playlistsGUI()
    
    def delPlaylist(self, name):
        if isinstance(name, Button):
            name = self.playlistButtonDict[str(name)][0]
        self.playlists.pop(name)
        self.updatePlaylist()
        self.playlistsGUI()
    
    def addToPlaylist(self, name):
        self.playSong(_type="PL"+name)
    
    def updateLabel(self):
        try:
            self.currentLabel.text = self.info.title if len(self.info.title) < 40 else self.info.title[:36] + "..."
            self.authorLabel.text = self.info.uploader
            self.imgLayout.clear_widgets()
            self.imgLayout.add_widget(AsyncImage(source=self.info.thumbnail))
        except Exception as e:
            print(e)
    
    def checking(self):
        if not self.med.is_playing():
            if self.paused or self.doingSomething:
                pass
            elif self.loop and self.info.url:
                self.repeat()
            elif self.playingPlaylist:
                self.doingSomething = True
                self.play(self.queue[0])
                self.queue.append(self.queue.pop(0))
            elif self.queue:
                self.play(self.queue.pop(0))
            Clock.schedule_once(lambda x: self.checking(), 3)
        else:
            self.updateTime()
            Clock.schedule_once(lambda x: self.checking(), 0.1)

    def backToMain(self, button, _type):
        if _type == "Play":
            self.queue.clear()
            self.playingPlaylist = False
            self.man.current = 'main'
            Clock.schedule_once(lambda x: self.resetLoopAndPause() or self.play(self.playDict[button]), 1)
        elif _type == "Q":
            self.playingPlaylist = False
            self.man.current = 'main'
            self.queue.pop(-1)
            self.queue.append(self.playDict[button][0])
        elif _type.startswith("PL"):
            button.text = "Added"
            button.unbind()
            for function in self.ADDFUNCTIONS:
                button.unbind(on_release=function)
            self.playlists[_type[2:]].append(self.playDict[button])
            if self.playingPlaylist and self.curPlayList == _type[2:]:
                self.queue.append(self.playDict[button])
            self.updatePlaylist()
        else:
            self.man.current = 'main'
            self.updateLabel()
    
    def resetLoopAndPause(self):
        if self.loop:
            self.toggleLoop(self.buttons["loop (off)"])
        if self.paused:
            self.pause(self.buttons["Pause"], reset=True)
    
    def updatePlaylist(self):
        with open("settings.json", "w") as f:
            json.dump({"Playlists": self.playlists}, f)

    def pause(self, event = None, reset=False):
        if self.paused and not reset:
            self.med.play()
        else:
            self.med.pause()
        self.paused = not self.paused
        event.text = "Unpause" if self.paused else "Pause"

    def find(self, name):
        qs = urllib.parse.urlencode({"search_query": name})
        fURL = urllib.request.urlopen("https://www.youtube.com/results?"+qs)
        return re.findall(r"watch\?v=(\S{11})", fURL.read().decode())

    def play(self, url, a=True):
        if isinstance(url, list):
            url = url[0]
        self.doingSomething = True
        for _ in range(4):
            try:
                with yt_dlp.YoutubeDL({'extract_audio': True, 'format': 'bestaudio', 'outtmpl': '%(title)s.mp3'}) as video:
                    self.info = Video(info = video.extract_info(url, download=False))
                break
            except:
                time.sleep(3)
        self.med.stop()
        self.med.set_media(vlc.Media(self.info.url))
        self.med.play()
        self.p = True
        self.updatingTime = True
        self.updateLabel()
        self.updateTime()
        time.sleep(1)
        self.timeSlider.max=int(self.med.get_length()/1000)
        Clock.schedule_once(self.reset, 2)
    
    def repeat(self):
        self.doingSomething = True
        self.med.stop()
        self.med.set_media(vlc.Media(self.info.url))
        self.med.play()
        self.p = True
        Clock.schedule_once(self.reset, 2)
    
    def reset(self, x):
        self.doingSomething = False

if __name__ == "__main__":
    MusicPlayer().run()