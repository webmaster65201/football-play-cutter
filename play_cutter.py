#!/usr/bin/env python3
"""Experimental broadcast football play candidate detector and clip exporter."""
import argparse, csv, pathlib, subprocess, sys
import cv2
import imageio_ffmpeg
import numpy as np

def analyze(path, sample_interval=0.5):
    cap=cv2.VideoCapture(str(path))
    if not cap.isOpened(): raise RuntimeError('Cannot open video')
    fps=cap.get(cv2.CAP_PROP_FPS) or 30
    duration=cap.get(cv2.CAP_PROP_FRAME_COUNT)/fps
    prev=None; samples=[]; t=0.0
    while t<duration:
        cap.set(cv2.CAP_PROP_POS_MSEC,t*1000)
        ok,frame=cap.read()
        if not ok: break
        h,w=frame.shape[:2]
        small=cv2.resize(frame,(320,180))
        hsv=cv2.cvtColor(small,cv2.COLOR_BGR2HSV)
        # Broad grass/turf color mask; works best on green-field broadcasts.
        grass=cv2.inRange(hsv,np.array([28,35,25]),np.array([95,255,255]))
        field=float(np.mean(grass>0))
        gray=cv2.cvtColor(small,cv2.COLOR_BGR2GRAY)
        motion=float(np.mean(cv2.absdiff(gray,prev)))/255 if prev is not None else 0
        samples.append((t,field,motion))
        prev=gray; t+=sample_interval
    cap.release()
    return duration,samples

def candidates(samples, min_length=3, max_length=35, pad_before=2, pad_after=2):
    if not samples: return []
    motions=np.array([x[2] for x in samples]); fields=np.array([x[1] for x in samples]);
    # Robust motion threshold, intentionally conservative; not a snap classifier.
    threshold=max(.035,float(np.percentile(motions,60)))
    active=(motions>threshold)&(fields>.18)
    # Smooth 3 sample window and merge nearby activity, retaining longer stretches.
    active=np.convolve(active.astype(int),np.ones(3),mode='same')>=2
    spans=[]; start=None
    for i,yes in enumerate(active):
        if yes and start is None: start=i
        if start is not None and (not yes or i==len(active)-1):
            end=i if not yes else i+1
            spans.append([samples[start][0],samples[end-1][0]+.5]);start=None
    merged=[]
    for a,b in spans:
        if merged and a-merged[-1][1]<=3: merged[-1][1]=b
        else: merged.append([a,b])
    output=[]
    for a,b in merged:
        if b-a<min_length: continue
        # Split overlong stretches for review rather than silently discarding.
        while b-a>max_length:
            output.append((max(0,a-pad_before),a+max_length+pad_after))
            a+=max_length
        output.append((max(0,a-pad_before),b+pad_after))
    return output

def write_csv(path,spans,duration,scouting_team='Southside'):
    with open(path,'w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['clip','start_seconds','end_seconds','include','odk','notes'])
        for i,(a,b) in enumerate(spans,1):writer.writerow([f'play_{i:04d}',f'{a:.2f}',f'{min(duration,b):.2f}','yes','?',f'REVIEW: candidate, not verified play; scouting team: {scouting_team}'])

def export(path,csv_path,out):
    out.mkdir(parents=True,exist_ok=True)
    with open(csv_path,newline='') as f: rows=list(csv.DictReader(f))
    count=0
    for row in rows:
        if row.get('include','yes').strip().lower() not in ('yes','y','1','true'):continue
        a=float(row['start_seconds']);b=float(row['end_seconds'])
        if b<=a:continue
        name=''.join(c for c in row['clip'] if c.isalnum() or c in '_-') or f'clip_{count+1}'
        cmd=[imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-loglevel','error','-y','-ss',str(a),'-i',str(path),'-t',str(b-a),'-c:v','libx264','-preset','veryfast','-crf','20','-c:a','aac',str(out/(name+'.mp4'))]
        subprocess.run(cmd,check=True);count+=1
    print(f'Exported {count} clips to {out}')

def main():
    p=argparse.ArgumentParser(description='Experimental football broadcast candidate cutter')
    p.add_argument('video',type=pathlib.Path);p.add_argument('--export',action='store_true',help='Export clips from reviewed CSV')
    p.add_argument('--csv',type=pathlib.Path,help='CSV path (defaults to video_name_candidates.csv)')
    p.add_argument('--interval',type=float,default=.5)
    args=p.parse_args()
    if not args.video.exists():p.error('Video file not found')
    csv_path=args.csv or args.video.with_name(args.video.stem+'_candidates.csv')
    if args.export:
        if not csv_path.exists():p.error('Candidate CSV not found; run analysis first')
        export(args.video,csv_path,args.video.with_name(args.video.stem+'_clips'))
    else:
        duration,samples=analyze(args.video,args.interval)
        spans=candidates(samples)
        write_csv(csv_path,spans,duration)
        print(f'Found {len(spans)} possible action segments. Review/edit {csv_path} before exporting.')
        print('WARNING: These are motion-based candidates, not reliably identified football plays.')
if __name__=='__main__':main()
