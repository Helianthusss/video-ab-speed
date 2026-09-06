import av, json, hashlib, io, os
from pathlib import Path
from functools import lru_cache
ROOT=Path(__file__).resolve().parent
DATA_DIR=Path(os.environ.get('AB_DATA_DIR',ROOT/'data')).expanduser().resolve()
MEDIA=DATA_DIR/'media';MEDIA.mkdir(parents=True,exist_ok=True)
def index_video(path):
    path=Path(path).resolve()
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    key=h.hexdigest();out=MEDIA/key;out.mkdir(exist_ok=True)
    dest=out/path.name
    if not dest.exists():
        import shutil;shutil.copyfile(path,dest)
    if (out/'index.json').exists():return json.loads((out/'index.json').read_text())
    with av.open(str(dest)) as c:
        st=c.streams.video[0];frames=[]
        for i,f in enumerate(c.decode(st)):
            if f.pts is None:raise ValueError('Video thiếu PTS; không thể dùng đo chính xác')
            frames.append({'index':i,'pts':f.pts,'time_base':str(f.time_base),'time':float(f.pts*f.time_base)})
        if len(frames)<2 or any(b['time']<=a['time'] for a,b in zip(frames,frames[1:])):raise ValueError('PTS không tăng nghiêm ngặt')
        gaps=[b['time']-a['time'] for a,b in zip(frames,frames[1:])]
        meta=dict(id=key,path=str(dest),name=path.name,width=st.width,height=st.height,fps=str(st.average_rate),time_base=str(st.time_base),timing='VFR' if max(gaps)-min(gaps)>1e-5 else 'CFR',frames=frames,first=frames[0]['time'],last=frames[-1]['time'])
    (out/'index.json').write_text(json.dumps(meta));return meta

def metadata(key):
    meta=json.loads((MEDIA/key/'index.json').read_text())
    # Resolve from the current storage root so a backup remains usable after
    # moving the project to another directory or machine.
    stored=Path(meta.get('path','')).name
    candidate=MEDIA/key/stored
    if not candidate.exists():
        files=[p for p in (MEDIA/key).iterdir() if p.name!='index.json']
        if len(files)!=1:raise ValueError('Không xác định được file video trong kho media')
        candidate=files[0]
    meta['path']=str(candidate.resolve())
    return meta
@lru_cache(maxsize=256)
def frame_bytes(key,index):
    m=metadata(key);target=m['frames'][index]
    with av.open(m['path']) as c:
        st=c.streams.video[0];c.seek(target['pts'],stream=st,backward=True,any_frame=False)
        for f in c.decode(st):
            if float(f.pts*f.time_base)==target['time']:
                image=f.to_image();image.thumbnail((1280,720));b=io.BytesIO();image.save(b,'JPEG',quality=90);return b.getvalue()
    raise ValueError('Không giải mã được khung hình có PTS yêu cầu')
