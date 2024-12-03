import random
import re
import pafy
import vlc
import urllib.parse, urllib.request
import tkinter as tk
import json
import os
import keyboard
import pytube

class MP:
    def __init__(self, setup=True):
        #self.med.get_length()
        #get_position() [percentage from 0 to 1]
        #get_time() cur time
        #
        self.med = None  # media player
        if setup:
            self.root=tk.Tk()
            self.root.title("Player")
            #self.root.geometry("1280x720")
            self.canvas=tk.Canvas(self.root, width=1280, height=720)
            self.canvas.pack()
            self.ls = []
            self.p = False #playing or not, true = playing
            self.n=0 #index for playlist
            self.loopBool=False #loop or not
            self.root2=None #second window
            self.root3=None #Third
            self.outofpl=False #When to leave playlist mode
            self.l = None #label
            b=tk.Button(master=self.canvas, command=self.pause, text="Pause/Unpause", width=20, height=10, bg="yellow")
            b.place(relx=0.1, rely=0.18, anchor='center')
            self.loopButton=tk.Button(master=self.canvas, command=self.loop, text="loop (off)", width=20, height=10, bg="green")
            self.loopButton.place(relx=0.9, rely=0.18, anchor='center')
            b = tk.Button(master=self.canvas, command=self.inp, text="Play Song", width=20, height=10, bg="#15ff00")
            b.place(relx=0.5, rely=0.18, anchor='center')
            tk.Button(master=self.canvas, command=self.playlistFUNC, text="Playlists", width=8, height=1).place(x=0, y=698)
            tk.Button(master=self.canvas, command=lambda a=19028: self.ls.clear(), text="Clear Queue", width=9, height=1).place(relx=1, rely=1, anchor="se")#x=1215, y=698)
            tk.Button(master=self.canvas, command=self.restart, text="Restart", width=8, height=1).place(relx=0.5, rely=709/720, anchor='center')
            tk.Button(master=self.canvas, command=lambda: self.med.stop() if self.med else False, text="Skip", width=20, height=10, bg='red').place(relx=0.5, rely=0.82, anchor='center')
            tk.Button(master=self.canvas, text="Add to Queue", command=self.addtoq, width=20, height=10, bg='purple').place(relx=0.9, rely=0.82, anchor='center')
            tk.Button(master=self.canvas, text="Rewind", command=lambda: (self.__setattr__("n", self.n-2) or self.med.pause()) if self.n>0 else False, width=20, height=10, bg='brown').place(relx=0.1, rely=0.82, anchor='center')
            try:
                self.root.protocol("WM_DELETE_WINDOW", exit)
            except:
                pass
            self.plRoot=None
            #self.root.bind("<space>", lambda arg1=None: print(self.med.is_playing()))
            self.root.resizable(False, False)
            self.updating=False
            
            self.w = tk.Scale(self.canvas, from_=0, to=10, orient=tk.HORIZONTAL, showvalue=0)
            self.w.bind("<ButtonRelease-1>", self.stopUpdatingSlider)
            self.w.bind("<Button-1>", self.set_slider)
            self.w.place(relx=0.5, rely=0.6, anchor='center')

            self.speed = 1
            self.speeder = tk.Scale(self.canvas, from_=0.5, to=2, digits = 2, resolution=0.1, orient=tk.HORIZONTAL, showvalue=1.0, width=10, label="        Speed")
            self.speeder.bind("<ButtonRelease-1>", self.OnSpeed)
            self.speeder.bind("<Button-1>", self.OnSpeed)
            self.speeder.place(relx=0.8, rely=0.55, anchor='center')
            self.speeder.set(1)
            
            self.timelbl=tk.Label(self.canvas)
            self.timelbl.place(relx=0.5, rely=0.65, anchor='center')
            self.root.bind("<space>", self.pause)
            self.root.bind("e", self.test)
            self.root.bind("<Left>", lambda arg1: self.med.set_time(0 if self.med.get_time()-5000 < 0 else self.med.get_time()-5000) if self.med else False)
            self.root.bind("<Right>", lambda arg1: self.med.set_time(self.med.get_time()+5000) if self.med else False)
            self.root.bind("l", lambda arg1=None: self.med.stop() if self.med else False)
            self.root.bind("j", lambda arg1=None: (self.__setattr__("n", self.n-2) or self.med.pause()) if self.n>0 else False)
            self.root.after(1, self.specset)
            self.root.after(10, self.func)
            keyboard.on_press(lambda key: self.med.stop() if key.name == "play/pause media" and self.med else False)
            self.root.mainloop()

    def OnSpeed(self, e=None):
        if self.med:
            self.med.set_rate(self.speeder.get())
        self.speed = self.speeder.get()
    
    def addtoq(self, e=None):
        if self.root3:
            return
        self.root3 = tk.Tk()

        def deled():
            self.root3.destroy()
            self.root3 = None
        self.root3.protocol("WM_DELETE_WINDOW", deled)
        t = tk.Entry(master=self.root3)

        def b(e=None):
            i = t.get()
            self.root3.destroy()
            self.root3 = None
            if self.ls:
                self.ls.append(i)
            else:
                self.ls.extend([self.curson, i])
                print(f"'{i}' added to queue!")
                self.n+=1
        t.pack()
        t.bind("<Return>", b)
        self.root3.mainloop()
        
    def test(self, arg=None):
        eval(input())
        print('')
    
    def func(self):
        if self.med:
            self.w.config(to=self.med.get_length()/1000)
            if self.p and not self.med.is_playing():
                if self.loopBool:
                    self.play(self.curson)
                    self.canvas.after(5000, self.func)
                    return None
                elif self.ls:
                    self.timelbl.config(text="00:00:00")
                    self.w.set(0)
                    self.n += 1
                    self.play(self.ls[self.n%len(self.ls)])
                    self.canvas.after(5000, self.func)
                    return None
            elif self.med.is_playing():
                if not self.updating:
                    self.w.set(int(self.med.get_time()/1000))
                sec=self.w.get()
                mins=sec//60;sec%=60
                hr=mins//60;mins%=60
                osec=int(self.med.get_length()/1000)
                omin=osec//60;osec%=60
                ohr=omin//60;omin%=60
                self.timelbl.config(text="{0}:{1}:{2} / {3}:{4}:{5}".format(str(hr).zfill(2), str(mins).zfill(2), str(sec).zfill(2), str(ohr).zfill(2), str(omin).zfill(2), str(osec).zfill(2)).replace(".",""))
        self.canvas.after(10, self.func)
    
    def set_slider(self, e=None):
        if self.med:
            self.updating = True
            #self.w.config(showvalue=1)
            self.med.set_time(self.w.get()*1000)

    def stopUpdatingSlider(self, e=None):
        self.med.set_time(self.w.get()*1000)
        #self.w.config(showvalue=0)
        self.updating = False

    def specset(self):
        os.chdir("\\".join(os.path.abspath(__file__).split("\\")[:-1]))
        with open("settings.json", "r" if 'settings.json' in os.listdir() else "x") as f:
            try:
                self.rules = json.load(f)
                if not self.rules:
                    self.rules = {"Playlists":{}}
            except:
                self.rules = {"Playlists":{}}
        self.playlists = self.rules['Playlists']

    def restart(self):
        import sys
        os.execv(sys.executable, ['python'] + sys.argv)

    def playlistFUNC(self, ev=None):
        self.doing=False
        if self.plRoot:
            return
        self.plRoot=tk.Tk()
        self.plRoot.title("Playlists")
        self.plRoot.geometry("640x480")
        def deletedpl():
            self.plRoot.destroy()
            self.plRoot=None
        self.plRoot.protocol("WM_DELETE_WINDOW", deletedpl)
        all={}
        try:
            for pl in tuple(self.playlists.keys()):
                all[pl]=tk.StringVar(self.plRoot)
                all[pl].set(pl)
                tk.OptionMenu(self.plRoot, all[pl], *[thing for thing in self.playlists[pl]], command=lambda arg1, arg2=pl: all[arg2].set(arg2)).pack()
        except Exception as e:
            print(e)

        s = tk.StringVar(self.plRoot)
        s.set("Playlists")

        def playy(playlist):
            s.set("Playlists")
            self.ls=self.playlists[playlist]
            random.shuffle(self.ls)
            self.n=0
            if self.med:
                self.med.stop()
            else:
                self.play(self.ls[0])
            #self.playlistplay()


        if len(tuple(self.playlists.keys()))>0:
            p = tk.OptionMenu(self.plRoot, s, *list(self.playlists.keys()), command=playy)
            p.pack()
            
        def addp(e=None):
            if self.doing:
                return
            self.doing=True
            v=tk.StringVar(self.plRoot, "")
            l = tk.Entry(self.plRoot)
            l.pack(side='top')

            def change(e):
                v.set(l.get())
                l.destroy()
            l.bind("<Return>", change)
            self.plRoot.wait_variable(v)
            t = tk.Text(master=self.plRoot)
            t.pack(side='top')
            v2=tk.StringVar(self.plRoot, "")

            def change2():
                v2.set(t.get("1.0", tk.END))
                t.destroy()

            tk.Button(master=self.plRoot, command=change2, text="Done", width=8, height=1).pack(side='top')
            self.plRoot.wait_variable(v2)
            self.playlists[v.get()] = v2.get().strip().split("\n")
            self.rules['Playlists'] = self.playlists
            with open("settings.json", "w") as f:
                json.dump(self.rules, f)
            self.plRoot.destroy()
            self.plRoot=None

        def remp(e=None):
            if self.doing:
                return
            self.doing=True
            vv = tk.StringVar(self.plRoot, "")
            l = tk.Entry(self.plRoot)
            l.pack(side='top')

            def cccc(e):
                vv.set(l.get())
                l.destroy()
            l.bind("<Return>", cccc)
            self.plRoot.wait_variable(vv)
            if vv.get() in self.playlists:
                self.playlists.pop(vv.get())
                self.rules['Playlists'] = self.playlists
                with open("settings.json", "w") as f:
                    json.dump(self.rules, f)
            self.plRoot.destroy()
            self.plRoot=None

        tk.Button(master=self.plRoot, text="Add", command=addp, width=8, height=1).place(x=0, y=0)
        tk.Button(master=self.plRoot, command=remp, text="Remove", width=8, height=1).place(x=576, y=0)

    def inp(self, e=None):
        if self.root2:
            return
        self.root2 = tk.Tk()
        def deleted():
            self.root2.destroy()
            self.root2=None
        self.root2.protocol("WM_DELETE_WINDOW", deleted)
        t = tk.Entry(master=self.root2)
        def b(e=None):
            i = t.get()
            self.root2.destroy()
            self.root2=None
            if 'playlist' in i:
                self.ls = [link for link in pytube.Playlist(i)]
                self.play(self.ls[0])
                
            else:
                self.play(i)
        t.pack()
        t.bind("<Return>", b)
        self.root2.mainloop()

    # def playlistplay(self):
    #     if not self.loopBool and not (self.med and self.med.is_playing()) and self.p:
    #         self.play(self.ls[self.n%len(self.ls)])
    #         self.n+=1
    #         self.root.after(4000, self.playlistplay)
    #     else:
    #         self.root.after(1, self.playlistplay)

    def play(self, name, a=True, out=False):
        qs=urllib.parse.urlencode({"search_query":name})
        fURL = urllib.request.urlopen("https://www.youtube.com/results?"+qs)
        res=re.findall(r"watch\?v=(\S{11})", fURL.read().decode())
        clip = f"https://www.youtube.com/watch?v={res[0]}"
        while True:
            try:
                vid=pafy.new(clip)
                break
            except KeyError:
                pass
        l=vid.getbestaudio() if a else vid.getbest()
        self.curson=name
        if self.med:
            self.med.stop()
        self.med = vlc.MediaPlayer()
        #print(l.__dict__)
        self.med.set_media(vlc.Media(l.url))
        self.med.set_rate(self.speed)
        #self.med = vlc.MediaPlayer(l.url)
        self.med.play()
        self.p=True
        if not out:
            if not self.l:
                self.l = tk.Label(self.root, text=f"Now playing {l.title}")
                self.l.place(relx=0.5, rely=0.5, anchor='center')
            else:
                self.l.config(text=f"Now playing {l.title}")
    
    def loop(self, e=None):
        if not self.med:
            return
        self.loopBool = not self.loopBool
        self.loopButton.config(text="loop " + ("(on)" if self.loopBool else "(off)"))
        def wait():
            if not self.loopBool:
                return
            if (self.med.is_playing() or not self.p):
                self.root.after(1, wait)
            else:
                self.play(self.curson)
                self.root.after(4000, wait)
    
    def pause(self, e=None):
        if self.med:
            if self.p:
                self.p = False
                self.med.pause()
            else:
                self.med.play()
                self.p = True

if __name__=="__main__":
    MP()
