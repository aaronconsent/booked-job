#!/usr/bin/env python3
"""Vertical promo audiogram: hazard-branded bg + hook quote + live waveform.
   python3 scripts/clip.py SRC.mp3 START DUR "EP. 1" "Hook quote here" out.mp4"""
import sys, subprocess, textwrap, tempfile, os
from PIL import Image, ImageDraw, ImageFont
ORANGE=(255,106,0); BLACK=(17,17,17); WHITE=(248,247,243)
IMPACT="/System/Library/Fonts/Supplemental/Impact.ttf"; BLACKF="/System/Library/Fonts/Supplemental/Arial Black.ttf"; MARKER="doodle/assets/PermanentMarker.ttf"
def f(p,s): return ImageFont.truetype(p,int(s))
def fit(d,t,p,tw,start):
    s=start
    while s>30:
        ft=f(p,s)
        if d.textlength(t,font=ft)<=tw: return ft
        s-=3
    return f(p,30)
def hazard(img,x0,y0,x1,y1):
    d=ImageDraw.Draw(img); d.rectangle([x0,y0,x1,y1],fill=BLACK); H=y1-y0; w=int(H*0.43); x=x0-H
    while x<x1+H: d.polygon([(x,y0),(x+w,y0),(x+w-H,y1),(x-H,y1)],fill=ORANGE); x+=2*w

def bg(eptag, hook, out):
    W,Hh=1080,1920; img=Image.new("RGB",(W,Hh),BLACK); d=ImageDraw.Draw(img)
    hazard(img,0,0,W,150); hazard(img,0,Hh-150,W,Hh)
    d.rectangle([0,0,W-1,Hh-1],outline=ORANGE,width=9)
    # show title (2 lines, small)
    d.text((W/2,300),"GET BOOKED,",font=fit(d,"GET BOOKED,",IMPACT,W-200,120),fill=WHITE,anchor="mm")
    d.text((W/2,400),"NOT F***ED",font=fit(d,"NOT F***ED",IMPACT,W-220,140),fill=ORANGE,anchor="mm")
    # ep chip
    d.rounded_rectangle([W/2-120,470,W/2+120,548],radius=14,outline=ORANGE,width=5); d.text((W/2,509),eptag,font=f(BLACKF,46),fill=ORANGE,anchor="mm")
    # hook quote, wrapped
    hf=f(BLACKF,76); 
    # wrap to width
    words=hook.split(); lines=[]; cur=""
    for wd in words:
        t=(cur+" "+wd).strip()
        if d.textlength(t,font=hf)<=W-150: cur=t
        else: lines.append(cur); cur=wd
    lines.append(cur)
    y=720
    for ln in lines:
        d.text((W/2,y),ln,font=hf,fill=WHITE,anchor="mm"); y+=92
    # footer
    d.text((W/2,Hh-250),"LISTEN NOW  ·  SPOTIFY",font=f(BLACKF,46),fill=WHITE,anchor="mm")
    d.text((W/2,Hh-195),"booked-job.com",font=f(MARKER,52),fill=ORANGE,anchor="mm")
    img.save(out)

def main():
    src,start,dur,eptag,hook,out=sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5],sys.argv[6]
    tmp=tempfile.mkdtemp(); png=os.path.join(tmp,"bg.png"); bg(eptag,hook,png)
    fc=("[1:a]aformat=channel_layouts=mono,showwaves=s=1000x300:mode=cline:rate=25:colors=0xFF6A00[w];"
        "[0:v][w]overlay=(main_w-overlay_w)/2:1330,format=yuv420p[v]")
    subprocess.run(["ffmpeg","-y","-loglevel","error","-loop","1","-i",png,"-ss",start,"-t",dur,"-i",src,
        "-filter_complex",fc,"-map","[v]","-map","1:a","-t",dur,"-r","25","-c:v","libx264","-c:a","aac","-b:a","192k","-pix_fmt","yuv420p","-movflags","+faststart",out],check=True)
    print("built",out)
if __name__=="__main__": main()
