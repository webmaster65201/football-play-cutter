#!/usr/bin/env python3
"""Football Play Cutter v2: review-first and automatic export modes."""
import csv
import tempfile
import os
import sys
import imageio_ffmpeg
import pathlib
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from play_cutter import analyze, candidates, write_csv, export
from odk_suggest import suggest_odk

FIELDS=('clip','start_seconds','end_seconds','include','odk','notes')

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Football Play Cutter V5.1 — Mac')
        self.geometry('1100x780')
        self.videos=[]
        self.current=None
        self.busy=False
        self.mode=tk.StringVar(value='review')
        self.home_team=tk.StringVar(value='')
        self.away_team=tk.StringVar(value='')
        self.home_color=tk.StringVar(value='Select color')
        self.away_color=tk.StringVar(value='Select color')
        self.scout_side=tk.StringVar(value='Home')
        self.scouting_team=tk.StringVar(value='')
        self.attack_direction=tk.StringVar(value='unknown')
        self.status=tk.StringVar(value='Select one or more recordings to begin.')
        root=ttk.Frame(self,padding=14);root.pack(fill='both',expand=True)
        ttk.Label(root,text='Football Play Cutter',font=('Arial',20,'bold')).pack(anchor='w')
        ttk.Label(root,text='Experimental motion-based play detection. ODK suggestions are low-confidence and must be reviewed.').pack(anchor='w',pady=(0,10))
        game=ttk.LabelFrame(root,text='Game Setup — teams and jersey colors',padding=8);game.pack(fill='x',pady=(0,5))
        colors=['Select color','White','Off-white / Cream','Black','Gray / Silver','Royal Blue','Blue','Navy Blue','Light Blue','Sky Blue','Red','Maroon / Burgundy','Green','Dark Green','Kelly Green','Lime Green','Yellow','Gold','Orange','Purple','Violet','Pink','Brown','Teal','Turquoise','Other / Unknown']
        for side,name,color in [('Home',self.home_team,self.home_color),('Away',self.away_team,self.away_color)]:
            line=ttk.Frame(game);line.pack(fill='x',pady=2)
            ttk.Label(line,text=side+' team:',width=13).pack(side='left')
            ttk.Entry(line,textvariable=name,width=28).pack(side='left',padx=(0,12))
            ttk.Label(line,text='Jersey:').pack(side='left')
            ttk.Combobox(line,textvariable=color,values=colors,state='readonly',width=22).pack(side='left',padx=6)
        line=ttk.Frame(game);line.pack(fill='x',pady=2)
        ttk.Label(line,text='Scouting:',width=13).pack(side='left')
        ttk.Combobox(line,textvariable=self.scout_side,values=['Home','Away'],state='readonly',width=12).pack(side='left')
        ttk.Label(line,text='  Scouting team attack direction (for this segment):').pack(side='left')
        ttk.Combobox(line,textvariable=self.attack_direction,values=['unknown','left','right'],state='readonly',width=12).pack(side='left',padx=6)
        ttk.Label(game,text='Enter both teams for each game. ODK follows the scouting side. Colors alone cannot establish possession.').pack(anchor='w')
        bar=ttk.Frame(root);bar.pack(fill='x',pady=4)
        ttk.Button(bar,text='Add videos (MP4/MOV)',command=self.add_videos).pack(side='left',padx=3)
        ttk.Button(bar,text='Remove selected',command=self.remove_video).pack(side='left',padx=3)
        ttk.Button(bar,text='Run selected mode',command=self.run_mode).pack(side='left',padx=3)
        modes=ttk.LabelFrame(root,text='Processing mode',padding=8);modes.pack(fill='x',pady=6)
        ttk.Radiobutton(modes,text='Review first: detect, inspect/edit, then export',variable=self.mode,value='review').pack(anchor='w')
        ttk.Radiobutton(modes,text='Automatic: detect and export all candidates without review',variable=self.mode,value='auto').pack(anchor='w')
        ttk.Label(modes,text='Automatic mode can include downtime, miss plays, or split plays incorrectly. Keep your original video.').pack(anchor='w')
        ttk.Label(root,text='Video queue (select a video to view its saved cuts):').pack(anchor='w')
        qframe=ttk.Frame(root);qframe.pack(fill='x')
        self.queue=tk.Listbox(qframe,height=4,exportselection=False);self.queue.pack(side='left',fill='x',expand=True)
        self.queue.bind('<<ListboxSelect>>',self.select_video)
        ttk.Scrollbar(qframe,orient='vertical',command=self.queue.yview).pack(side='right',fill='y')
        ttk.Label(root,text='Double-click ODK to choose O, D, K, or ? (unclassified). Save before export.').pack(anchor='w',pady=(8,0))
        area=ttk.Frame(root);area.pack(fill='both',expand=True,pady=5)
        self.tree=ttk.Treeview(area,columns=FIELDS,show='headings',selectmode='browse')
        for key,width in zip(FIELDS,(125,100,100,70,65,410)):
            self.tree.heading(key,text=key.replace('_',' ').title());self.tree.column(key,width=width,stretch=(key=='notes'))
        self.tree.pack(side='left',fill='both',expand=True)
        scroll=ttk.Scrollbar(area,orient='vertical',command=self.tree.yview);scroll.pack(side='right',fill='y');self.tree.configure(yscrollcommand=scroll.set)
        self.tree.bind('<Double-1>',self.edit_cell)
        buttons=ttk.Frame(root);buttons.pack(fill='x',pady=5)
        for title,fn in [('Preview selected clip',self.preview),('Add clip',self.add_clip),('Delete clip',self.delete_clip),('Save edits',self.save),('Suggest ODK',self.suggest_odk),('Export reviewed clips',self.export_reviewed)]:
            ttk.Button(buttons,text=title,command=fn).pack(side='left',padx=3)
        ttk.Label(root,textvariable=self.status,wraplength=990).pack(anchor='w',pady=8)

    def add_videos(self):
        paths=filedialog.askopenfilenames(filetypes=[('Video files','*.mp4 *.mov *.mkv *.avi'),('All files','*.*')])
        for raw in paths:
            path=pathlib.Path(raw)
            if path not in self.videos:self.videos.append(path);self.queue.insert('end',str(path))
        if self.videos and not self.queue.curselection():self.queue.selection_set(0);self.select_video()

    def remove_video(self):
        idx=self.queue.curselection()
        if not idx:return
        self.videos.pop(idx[0]);self.queue.delete(idx[0]);self.current=None;self.clear()
        if self.videos:self.queue.selection_set(0);self.select_video()

    def csv_path(self,video):return video.with_name(video.stem+'_candidates.csv')
    def out_path(self,video):return video.with_name(video.stem+'_clips')
    def clear(self):
        for item in self.tree.get_children():self.tree.delete(item)

    def select_video(self,_=None):
        idx=self.queue.curselection()
        if not idx:return
        self.current=self.videos[idx[0]];self.clear()
        if self.csv_path(self.current).exists():
            with self.csv_path(self.current).open(newline='',encoding='utf-8') as f:
                for row in csv.DictReader(f):self.tree.insert('','end',values=[row.get(k,'?') if k=='odk' else row.get(k,'') for k in FIELDS])
        self.status.set(f'{self.current.name}: {len(self.tree.get_children())} saved candidates.')

    def save(self):
        if not self.current:messagebox.showwarning('Choose video','Select a video first.');return False
        rows=[self.tree.item(item,'values') for item in self.tree.get_children()]
        try:
            for row in rows:
                if float(row[1])<0 or float(row[2])<=float(row[1]):raise ValueError('Each clip must have a nonnegative start and an end after its start.')
                if str(row[4]).strip().upper() not in ('O','D','K','?'):raise ValueError('ODK must be O, D, K, or ?.')
            with self.csv_path(self.current).open('w',newline='',encoding='utf-8') as f:
                writer=csv.writer(f);writer.writerow(FIELDS);writer.writerows(rows)
        except (ValueError,OSError) as exc:messagebox.showerror('Save failed',str(exc));return False
        self.status.set(f'Saved {len(rows)} clips for {self.current.name} — ODK CSV ready; ? means not classified.')
        return True

    def background(self,label,work,done):
        if self.busy:return
        self.busy=True;self.status.set(label)
        def worker():
            try:
                result=work();self.after(0,lambda:self.finish(done,result,None))
            except Exception as exc:self.after(0,lambda err=str(exc):self.finish(done,None,err))
        threading.Thread(target=worker,daemon=True).start()

    def finish(self,done,result,error):
        self.busy=False
        if error:self.status.set('Error: '+error);messagebox.showerror('Processing error',error)
        else:done(result)

    def run_mode(self):
        if not self.videos:messagebox.showwarning('No video','Add a recording first.');return
        videos=list(self.videos);mode=self.mode.get()
        scout_name=self.home_team.get().strip() if self.scout_side.get()=='Home' else self.away_team.get().strip()
        if not scout_name:messagebox.showwarning('Game setup','Enter a name for the scouting team.');return
        existing=[v.name for v in videos if self.csv_path(v).exists()]
        if existing and not messagebox.askyesno('Overwrite existing edits?',f'Detection will replace saved candidate lists for {len(existing)} video(s). Continue?'):return
        if mode=='auto' and not messagebox.askyesno('Automatic export', 'Export all detected motion segments without reviewing them? These may not be complete plays.'):return
        def work():
            report=[]
            for i,video in enumerate(videos,1):
                self.after(0,lambda v=video,i=i:self.status.set(f'Analyzing {i}/{len(videos)}: {v.name}'))
                duration,samples=analyze(video)
                spans=candidates(samples)
                write_csv(self.csv_path(video),spans,duration,scouting_team=scout_name)
                if mode=='auto' and spans:
                    self.after(0,lambda v=video:self.status.set(f'Exporting: {v.name}'))
                    export(video,self.csv_path(video),self.out_path(video))
                report.append(f'{video.name}: {len(spans)} candidates')
            return report
        def done(report):
            self.select_video()
            self.status.set('Finished. '+' | '.join(report)+(' — MP4 clips exported.' if mode=='auto' else ' — review/edit candidates, then click Export reviewed clips.'))
        self.background('Starting analysis...',work,done)

    def suggest_odk(self):
        if not self.current or not self.tree.get_children():
            messagebox.showinfo('No clips','Detect or load clips first.');return
        if self.attack_direction.get()=='unknown':
            messagebox.showinfo('Direction required',
                'Select the direction your scouting team is attacking for these clips (left or right). '
                'If the direction changes, process those clips separately. '
                'Without direction, leave ODK as ? and label manually.')
            return
        scout_color=self.home_color.get() if self.scout_side.get()=='Home' else self.away_color.get()
        opponent_color=self.away_color.get() if self.scout_side.get()=='Home' else self.home_color.get()
        if scout_color.lower() not in ('white','blue') or opponent_color.lower() not in ('white','blue') or scout_color==opponent_color:
            messagebox.showinfo('ODK color support', 'This experimental suggestion engine currently supports one White team and one Blue team. Other color combinations remain manual (?); no guesses will be made.');return
        video=self.current
        items=list(self.tree.get_children())
        direction=self.attack_direction.get()
        def work():
            results=[]
            for item in items:
                row=self.tree.item(item,'values')
                if str(row[4]).upper() in ('O','D','K'):
                    results.append((item,None,None));continue  # never overwrite manually set ODK
                label,reason=suggest_odk(video,float(row[1]),float(row[2]),direction)
                if scout_color.lower()=='blue' and label in ('O','D'):
                    label='D' if label=='O' else 'O'
                reason=f'{self.scout_side.get()} scouting team ({scout_color}) vs opponent ({opponent_color}). '+reason
                results.append((item,label,reason))
            return results
        def done(results):
            suggested=0
            for item,label,reason in results:
                if label is None:continue
                row=list(self.tree.item(item,'values'))
                row[4]=label
                row[5]=reason
                self.tree.item(item,values=row)
                suggested+=label in ('O','D')
            self.status.set(f'{suggested} tentative O/D suggestions; review EVERY play, correct errors, then Save edits. K remains manual.')
            messagebox.showinfo('ODK suggestions',
                f'{suggested} low-confidence O/D suggestions. These are NOT verified. '
                'Review every clip and assign K manually for special teams. Save edits when finished.')
        self.background('Analyzing jersey-color layout...',work,done)

    def export_reviewed(self):
        if not self.current:return
        if not self.save():return
        video=self.current
        if not messagebox.askyesno('Export reviewed clips?',f'Export included clips for {video.name}?'):return
        self.background('Exporting reviewed clips...',lambda:export(video,self.csv_path(video),self.out_path(video)),lambda _:self.status.set(f'Export complete: {self.out_path(video)}'))

    def add_clip(self):
        n=len(self.tree.get_children())+1
        self.tree.insert('','end',values=(f'play_{n:04d}','0','10','yes','?','MANUAL: adjust timestamps'))
    def delete_clip(self):
        for item in self.tree.selection():self.tree.delete(item)

    def edit_cell(self,event):
        item=self.tree.identify_row(event.y);col=self.tree.identify_column(event.x)
        if not item or not col:return
        idx=int(col[1:])-1;bbox=self.tree.bbox(item,col)
        if not bbox:return
        original=list(self.tree.item(item,'values'))
        if idx==4:
            chooser=ttk.Combobox(self.tree,values=['?','O','D','K'],state='readonly')
            chooser.set(original[idx]);chooser.place(x=bbox[0],y=bbox[1],width=bbox[2],height=bbox[3]);chooser.focus_set()
            def pick(_=None):
                if not chooser.winfo_exists():return
                values=list(self.tree.item(item,'values'));values[idx]=chooser.get();self.tree.item(item,values=values);chooser.destroy()
            chooser.bind('<<ComboboxSelected>>',pick)
            chooser.bind('<FocusOut>',lambda _:chooser.destroy() if chooser.winfo_exists() else None)
            return
        entry=ttk.Entry(self.tree);entry.insert(0,original[idx]);entry.select_range(0,'end')
        entry.place(x=bbox[0],y=bbox[1],width=bbox[2],height=bbox[3]);entry.focus_set()
        def commit(_=None):
            if not entry.winfo_exists():return
            values=list(self.tree.item(item,'values'));values[idx]=entry.get();self.tree.item(item,values=values);entry.destroy()
        entry.bind('<Return>',commit);entry.bind('<FocusOut>',commit)
        entry.bind('<Escape>',lambda _:entry.destroy() if entry.winfo_exists() else None)

    def preview(self):
        if not self.current or not self.tree.selection():return
        row=self.tree.item(self.tree.selection()[0],'values')
        try:
            start=float(row[1]);end=float(row[2]);assert start>=0 and end>start
        except (ValueError,AssertionError):messagebox.showerror('Invalid times','Check start and end times.');return
        def work():
            preview_dir=pathlib.Path(tempfile.gettempdir())/'football_play_cutter_previews'
            preview_dir.mkdir(parents=True,exist_ok=True)
            preview_file=preview_dir/'current_preview.mp4'
            cmd=[imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-loglevel','error','-y','-ss',str(start),'-i',str(self.current),'-t',str(end-start),'-c:v','libx264','-preset','ultrafast','-crf','25','-c:a','aac',str(preview_file)]
            subprocess.run(cmd,check=True)
            return preview_file
        def done(path):
            if sys.platform=='darwin': subprocess.Popen(['open',str(path)])
            elif os.name=='nt': os.startfile(str(path))
            else: subprocess.Popen(['xdg-open',str(path)])
            self.status.set('Opened clip preview in your video player.')
        self.background('Preparing clip preview...',work,done)

if __name__=='__main__':App().mainloop()
