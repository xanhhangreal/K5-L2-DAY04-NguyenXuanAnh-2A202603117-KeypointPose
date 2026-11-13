"""Local contact sheets for visual QC; never used as model inputs."""
from pathlib import Path
import argparse
from PIL import Image, ImageDraw

p=argparse.ArgumentParser()
p.add_argument('--raw',action='store_true')
args=p.parse_args()
root=Path('/workspace')
for kind in ('persons','faces'):
    folder=root/('data' if args.raw else 'automation_previews')/kind
    if not folder.exists(): continue
    images=sorted(x for x in folder.iterdir() if x.suffix in ('.jpg','.png'))
    for start in range(0,len(images),4):
        chunk=images[start:start+4]
        canvas=Image.new('RGB',(1600,1240),'#202020'); d=ImageDraw.Draw(canvas)
        for i,path in enumerate(chunk):
            im=Image.open(path).convert('RGB'); im.thumbnail((790,580))
            x=(i%2)*800; y=(i//2)*620
            canvas.paste(im,(x,y+30)); d.text((x+8,y+8),path.name,fill='white')
        out=root/'automation_previews'/f"{'raw' if args.raw else 'overlay'}-{kind}-{start//4}.png"
        out.parent.mkdir(parents=True,exist_ok=True); canvas.save(out)
