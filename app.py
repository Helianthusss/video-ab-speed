import sys,os
from pathlib import Path
ROOT=Path(__file__).resolve().parent
import json,sqlite3,uuid,datetime,copy,io,zipfile,threading
from flask import Flask,request,jsonify,send_file,send_from_directory
from core import *
from media import index_video,metadata,frame_bytes
app=Flask(__name__,static_folder='static');app.config['MAX_CONTENT_LENGTH']=16*1024**3
DATA_DIR=Path(os.environ.get('AB_DATA_DIR',ROOT/'data')).expanduser().resolve()
DB=DATA_DIR/'survey.sqlite';DB.parent.mkdir(parents=True,exist_ok=True);LOCK=threading.RLock()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def db():
 c=sqlite3.connect(DB);c.execute('CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY, body TEXT)');c.execute('CREATE TABLE IF NOT EXISTS history(seq INTEGER PRIMARY KEY AUTOINCREMENT,session TEXT,at TEXT,action TEXT,body TEXT)');return c
def get(sid):
 with db() as c:r=c.execute('SELECT body FROM sessions WHERE id=?',(sid,)).fetchone()
 if not r:raise ValueError('Không có phiên')
 return json.loads(r[0])
def save(s,action):
 s['updated']=now();s['revision']=s.get('revision',0)+1
 with db() as c:
  c.execute('INSERT OR REPLACE INTO sessions VALUES (?,?)',(s['id'],json.dumps(s,ensure_ascii=False)));c.execute('INSERT INTO history(session,at,action,body) VALUES (?,?,?,?)',(s['id'],now(),action,json.dumps(s,ensure_ascii=False)))
 return s

def new_session(mode):
 if mode not in ['Demo','Research']:raise ValueError('Chế độ không hợp lệ')
 return dict(id=str(uuid.uuid4()),mode=mode,project='Pedestrian safety',site='',location='',observer='',session_start='',timezone='Asia/Ho_Chi_Minh',reference='A',L=None,uL=None,uT=None,start=0,end=900,interval_seconds=900,videoA=None,videoB=None,setup={},site_changes=[],events=[],records=[],flow=[],plans=[],audits=[],lines={'A':None,'B':None},line_locked={'A':False,'B':False},sync={'verified':False,'offset_start':0,'offset_end':0,'anchor_start':0,'anchor_end':900,'references':[],'version':1,'convention':'tB corrected=tB raw+offset(tB raw); A reference'},protocol={'version':'V4-implementation-1','locked':False,'estimand':'prevailing segment travel speed','sampling':'census','pilot_speed':[10,80],'warning_speed':[1,160],'bootstrap':1000,'seed':20260906,'iid_ci':False,'allow_percentile':True,'qc_rules':'Quyết định giữ/loại thủ công; phải ghi lý do và người duyệt','percentile':'Hyndman-Fan type 7 / numpy linear','audit_fraction':.1},created=now())

@app.errorhandler(Exception)
def error(e):return jsonify(error=str(e)),400
@app.before_request
def local_only():
 if request.host.split(':')[0] not in ['127.0.0.1','localhost']:raise ValueError('Chỉ truy cập cục bộ')
 if request.method=='POST' and request.headers.get('Origin') and request.headers['Origin'] not in ['http://127.0.0.1:8765','http://localhost:8765']:raise ValueError('Nguồn yêu cầu không hợp lệ')
@app.get('/')
def home():return send_from_directory('static','index.html')
@app.get('/api/sessions')
def sessions():
 with db() as c:rows=[json.loads(x[0]) for x in c.execute('SELECT body FROM sessions')]
 return jsonify([{'id':s['id'],'site':s['site'],'mode':s['mode'],'updated':s['updated']} for s in rows])
@app.post('/api/new')
def create():return jsonify(save(new_session(request.json['mode']),'create'))
@app.get('/api/session/<sid>')
def session(sid):return jsonify(get(sid))
@app.get('/api/summary/<sid>')
def sums(sid):return jsonify(summary(get(sid)))
@app.get('/api/media/<key>')
def meta(key):return jsonify(metadata(key))
@app.get('/api/frame/<key>/<int:index>')
def frame(key,index):return send_file(io.BytesIO(frame_bytes(key,index)),mimetype='image/jpeg')
@app.post('/api/import/<sid>/<cam>')
def imp(sid,cam):
 if cam not in ['A','B']:raise ValueError('Camera không hợp lệ')
 s=get(sid)
 if s['protocol']['locked'] or s['records']:raise ValueError('Tạo phiên mới để đổi video sau khi đã click / khóa')
 f=request.files['file'];temp=DATA_DIR/('upload_'+uuid.uuid4().hex+Path(f.filename).suffix);f.save(temp)
 try:m=index_video(temp)
 finally:temp.unlink(missing_ok=True)
 s['video'+cam]=m['id'];save(s,'import video '+cam);return jsonify(s)

def validate_session(s):
 if s['end']<=s['start'] or s['interval_seconds']<=0:raise ValueError('Khoảng thời gian không hợp lệ')
 sy=s['sync']
 if sy['anchor_end']<=sy['anchor_start']:raise ValueError('Mốc đồng bộ cuối phải sau mốc đầu')
 if 1+(sy['offset_end']-sy['offset_start'])/(sy['anchor_end']-sy['anchor_start'])<=0:raise ValueError('Drift làm đảo thứ tự thời gian')
 if s['L'] is not None and s['L']<=0:raise ValueError('L phải dương')
 p=s['protocol']
 if not 100<=p['bootstrap']<=10000:raise ValueError('Bootstrap 100–10000 lần')
 if not 0<p['pilot_speed'][0]<p['pilot_speed'][1]:raise ValueError('Khoảng tốc độ pilot không hợp lệ')
 if p['locked'] and (not s['site'] or not s['observer'] or not s['L'] or not sy['verified'] or not sy['references'] or not all(s['line_locked'].values())):raise ValueError('Khóa cần site, người đo, L, mốc đồng bộ và hai vạch đã khóa')

def stamp(s,r,cam,index):
 m=metadata(s['video'+cam]);f=m['frames'][index]
 r['frame'+cam]=index;r['t'+cam]=f['time'];r['pts'+cam]=f['pts'];r['time_base'+cam]=f['time_base'];r['video'+cam]=m['id']

@app.post('/api/action/<sid>')
def action(sid):
 with LOCK:
  s=get(sid);d=request.json
  if d.get('revision')!=s['revision']:raise ValueError('Phiên đã thay đổi. Tải lại trước khi lưu để tránh ghi đè.')
  op=d['op'];v=d.get('value',{})
  if op=='settings':
   allowed=['project','site','location','observer','session_start','timezone','reference','L','uL','uT','start','end','interval_seconds','setup','protocol','sync']
   if s['protocol']['locked'] and any(k in v and v[k]!=s[k] for k in ['protocol','L','start','end','interval_seconds','reference']):raise ValueError('Protocol đã khóa. Tạo phiên mới cho thay đổi thiết kế.')
   old=copy.deepcopy(s['sync'])
   for k in allowed:
    if k in v:s[k]=v[k]
   if old!=s['sync']:s['sync']['version']=old['version']+1
   validate_session(s)
  elif op=='line':
   cam=v['camera']
   if s['line_locked'][cam]:raise ValueError('Vạch đã khóa')
   s['lines'][cam]=v['points'];s['line_locked'][cam]=v['locked']
  elif op=='entry':
   if not s['videoA'] or not s['videoB']:raise ValueError('Cần hai video')
   cam='A' if v['direction']=='A→B' else 'B'
   r=dict(id=v.get('id') or 'V'+uuid.uuid4().hex[:10],type=v['type'],direction=v['direction'],observer=s['observer'],protocol_version=s['protocol']['version'],sync_version=s['sync']['version'],qc=[0],decision='review',matching='pending',reason='',sampling_status=v.get('sampling_status','census'),description=v.get('description',''),created=now(),updated=now())
   if any(x['id']==r['id'] for x in s['records']):raise ValueError('Trùng ID')
   stamp(s,r,cam,v['frame']);s['records'].append(r)
  elif op in ['exit','record']:
   r=next(x for x in s['records'] if x['id']==v['id'])
   if op=='exit':stamp(s,r,'B' if r['direction']=='A→B' else 'A',v['frame']);r['matching']='review'
   else:
    for k in ['type','direction','qc','decision','matching','reason','reviewer','description','sampling_status']:
     if k in v:r[k]=v[k]
    for cam in ['A','B']:
     if 'frame'+cam in v and v['frame'+cam] is not None:stamp(s,r,cam,int(v['frame'+cam]))
   if not set(r['qc']).issubset(set(range(7))) or (0 in r['qc'] and len(r['qc'])>1):raise ValueError('QC=0 không đi với mã lỗi')
   if r['decision'] in ['keep','exclude'] and (not r.get('reviewer') or not r.get('reason')):raise ValueError('Quyết định cần người duyệt và lý do')
   r['updated']=now()
  elif op=='flow':
   if v['count']<0 or int(v['count'])!=v['count'] or v['type'] not in CLASSES:raise ValueError('Số đếm nguyên không âm và class hợp lệ')
   v['id']=v.get('id',uuid.uuid4().hex);v['source']='Nhập tay';v['observer']=s['observer'];s['flow']=[f for f in s['flow'] if f['id']!=v['id']]+[v]
  elif op=='plan':
   p=plan(int(v['N']),v['cv'],v['precision'],int(v['seed']),v['fpc'],v['eligible'],v['rare']);p.update(type=v['type'],direction=v['direction'],interval=v['interval'],id=uuid.uuid4().hex);s['plans'].append(p)
  elif op=='log':s[v['kind']].append(dict(v['record'],created=now(),observer=s['observer']))
  elif op=='audit_select':
   pool=[r for r in s['records'] if r.get('tA') is not None and r.get('tB') is not None];rng=random.Random(v['seed']);n=math.ceil(len(pool)*v['fraction']);chosen=rng.sample(pool,n)
   for r in chosen:s['audits'].append(dict(id=uuid.uuid4().hex,record_id=r['id'],seed=v['seed'],fraction=v['fraction'],observer=v['observer'],kind=v['kind'],matching='uncertain',status='pending'))
  elif op=='audit_save':
   a=next(a for a in s['audits'] if a['id']==v['id']);r=next(r for r in s['records'] if r['id']==a['record_id']);rep=dict(r)
   stamp(s,rep,'A',v['frameA']);stamp(s,rep,'B',v['frameB'])
   a.update(v,status='done',tA=rep['tA'],tB=rep['tB'],speed=measure(rep,s)['speed'])
  else:raise ValueError('Thao tác không hỗ trợ')
  # Duplicate matching event is flagged, never silently removed. Same-frame vehicles are allowed with review.
  for r in s['records']:
   r['duplicate_event']=any(x['id']!=r['id'] and x.get('frameA')==r.get('frameA') and x.get('frameB')==r.get('frameB') and r.get('frameB') is not None for x in s['records'])
  return jsonify(save(s,op))
@app.get('/api/history/<sid>')
def history(sid):
 with db() as c:return jsonify([dict(seq=r[0],at=r[1],action=r[2]) for r in c.execute('SELECT seq,at,action FROM history WHERE session=? ORDER BY seq DESC',(sid,))])
@app.post('/api/restore/<sid>/<int:seq>')
def restore(sid,seq):
 with db() as c:r=c.execute('SELECT body FROM history WHERE session=? AND seq=?',(sid,seq)).fetchone()
 if not r:raise ValueError('Không có phiên bản')
 s=json.loads(r[0]);s['revision']=get(sid)['revision'];return jsonify(save(s,'restore '+str(seq)))
@app.get('/api/export/<sid>')
def export(sid):
 from exports import export_bundle
 return send_file(export_bundle(get(sid)),as_attachment=True)
@app.get('/api/backup')
def backup():
 out=DATA_DIR/'backup.sqlite'
 with db() as src:
  with sqlite3.connect(out) as dst:src.backup(dst)
 return send_file(out,as_attachment=True)
@app.post('/api/restore_file')
def restore_file():
 s=json.load(request.files['file']);validate_session(s)
 s['id']=str(uuid.uuid4());return jsonify(save(s,'restore snapshot as new session'))
if __name__=='__main__':
 app.run(host=os.environ.get('AB_HOST','127.0.0.1'),port=int(os.environ.get('AB_PORT','8765')),threaded=True)
