(() => {
 const el=id=>document.getElementById(id), results={};
 let active,timer,last;
 const live={seen:{A:new Set(),B:new Set()},pending:{A:[],B:[]},rows:[]};
 const status=t=>el('aiStatus').textContent=t;
 const esc=t=>String(t??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
 function side(line,point){const [[x1,y1],[x2,y2]]=line,[x,y]=point,v=(x2-x1)*(y-y1)-(y2-y1)*(x-x1);return v>1e-9?1:v<-1e-9?-1:0}
 function labelToType(label){return {motorcycle:'MC',bicycle:'MC',car:'Car',bus:'Bus',truck:'Truck'}[label]||'Other'}
 function normTime(camera,time){try{return typeof corr==='function'?corr(time,camera):time}catch{return time}}
 function renderLog(){const box=el('aiLiveLog');if(!box)return;if(!live.rows.length){box.innerHTML='<p class="hint">Chưa có log. Hãy chạy AI nhận diện, rồi bấm Phát video.</p>';return}box.innerHTML='<table><tr><th>Thời điểm</th><th>Sự kiện</th><th>Ghi chú</th></tr>'+live.rows.slice(-80).reverse().map(r=>`<tr><td>${esc(r.time)}</td><td class="${r.kind==='speed'?'ai-event-speed':r.kind==='review'?'ai-event-review':''}">${esc(r.event)}</td><td>${esc(r.note)}</td></tr>`).join('')+'</table>'}
 function addLog(kind,event,note,time){live.rows.push({kind,event,note,time});renderLog()}
 function resetLive(){live.seen={A:new Set(),B:new Set()};live.pending={A:[],B:[]};live.rows=[];renderLog()}
 function trackCrossings(data){if(!data||data.crossingsReady)return;const line=s?.lines?.[data.camera];data.crossingsReady=true;data.crossings=new Map();if(!line?.length)return;const paths=new Map();for(const row of data.frames||[]){for(const b of row.boxes||[]){if(b.track_id==null)continue;const [x1,,x2,y2]=b.xyxyn, point=[(x1+x2)/2,y2];if(!paths.has(b.track_id))paths.set(b.track_id,{track_id:b.track_id,label:b.label,type:labelToType(b.label),points:[]});paths.get(b.track_id).points.push({point,time:row.time,frame:row.frame,confidence:b.confidence});}}
  for(const tr of paths.values()){let previous=null;for(const p of tr.points){const cur=side(line,p.point);if(previous&&cur&&cur!==previous){data.crossings.set(tr.track_id,{...tr,time:p.time,frame:p.frame,confidence:p.confidence});break}if(cur)previous=cur}}
 }
 function findMatch(ev){const other=ev.camera==='A'?'B':'A';let best=null,bestIdx=-1;for(let i=0;i<live.pending[other].length;i++){const cand=live.pending[other][i];if(cand.matched||cand.type!==ev.type)continue;const tA=ev.camera==='A'?ev.corrected:cand.corrected,tB=ev.camera==='B'?ev.corrected:cand.corrected;const dt=tB-tA;if(!Number.isFinite(dt)||dt===0||!s?.L)continue;const speed=3.6*s.L/Math.abs(dt);const range=s.protocol?.pilot_speed||[5,120];const plausible=speed>=Math.min(...range)*0.5&&speed<=Math.max(...range)*1.8;if(!plausible)continue;const gap=Math.abs(dt);if(!best||gap<best.gap)best={cand,dt,speed,direction:dt>0?'A→B':'B→A',gap},bestIdx=i;}
  if(best){live.pending[other].splice(bestIdx,1);return best}return null}
 function processCrossing(camera,index){if(!el('aiLive')?.checked)return;const data=results[camera];if(!data||data.session_id!==s?.id||data.media_id!==meta[camera]?.id)return;trackCrossings(data);if(!data.crossings?.size)return;for(const ev of data.crossings.values()){if(ev.frame>index)continue;const key=camera+':'+ev.track_id;if(live.seen[camera].has(key))continue;live.seen[camera].add(key);const corrected=normTime(camera,ev.time);const full={...ev,camera,corrected};addLog('cross',`Camera ${camera}: xe ${ev.type} #${ev.track_id} qua vạch`,`Hình ${ev.frame}, thời điểm ${ev.time.toFixed(3)} giây trong video`,corrected?.toFixed?corrected.toFixed(3)+' s':ev.time.toFixed(3)+' s');const match=findMatch(full);if(match){match.cand.matched=true;const speed=match.speed;const note=`${match.direction}, Δt=${Math.abs(match.dt).toFixed(3)} giây, L=${s.L} m. Cần rà soát đúng cùng xe trước khi dùng chính thức.`;addLog('speed',`Đề xuất tốc độ: ${speed.toFixed(2)} km/h`,note,(Math.max(full.corrected,match.cand.corrected)).toFixed(3)+' s')}else live.pending[camera].push(full);}}
 window.drawYolo=(camera,index,ctx,canvas)=>{
  const data=results[camera];
  if(!el('aiVisible').checked||!data||data.session_id!==s.id||data.media_id!==meta[camera]?.id){processCrossing(camera,index);return;}
  const row=data.byFrame.get(index);if(row){
   ctx.save();ctx.lineWidth=Math.max(2,canvas.width/500);ctx.font=`${Math.max(15,canvas.width/65)}px sans-serif`;
   for(const b of row.boxes){let [x,y,r,t]=b.xyxyn;x*=canvas.width;r*=canvas.width;y*=canvas.height;t*=canvas.height;const track=b.track_id!=null?data.byTrack?.get(b.track_id):null;ctx.strokeStyle=track?.speed_kmh!=null?'#ffd23f':'#41ff84';ctx.strokeRect(x,y,r-x,t-y);const label=(b.track_id!=null?'#'+b.track_id+' ':'')+b.label+(track?.speed_kmh!=null?' · '+track.speed_kmh+' km/h':' '+Math.round(b.confidence*100)+'%');ctx.fillStyle='#102c20';ctx.fillRect(x,Math.max(0,y-24),ctx.measureText(label).width+8,24);ctx.fillStyle='#fff';ctx.fillText(label,x+4,Math.max(18,y-5));}
   ctx.restore();
  }
  processCrossing(camera,index);
 };
 const JOBS='video-ab-yolo-jobs';
 const readJobs=()=>{try{return JSON.parse(localStorage.getItem(JOBS))||{}}catch{return {}}};
 const saveJob=(camera,id)=>{const all=readJobs();all[camera]=id;localStorage.setItem(JOBS,JSON.stringify(all))};
 async function restore(){
  for(const [camera,id] of Object.entries(readJobs())){
   try{
    const job=await api('/api/yolo/job/'+id);
    if(job.status!=='done')continue;
    const data=await api('/api/yolo/job/'+id+'/result');
    data.byFrame=new Map(data.frames.map(r=>[r.frame,r]));
    data.byTrack=new Map((data.tracks||[]).map(r=>[r.track_id,r]));
    results[camera]=data;last=data;
    el('aiShow').hidden=false;el('aiDownload').hidden=false;el('aiDownload').href='/api/yolo/job/'+id+'/result';
   }catch{}
  }
  const co=Object.keys(results);
  if(co.length)status('Đã nạp lại kết quả camera '+co.join(' và ')+'. Bấm Xem đoạn đã nhận diện, rồi bấm Phát video để ghi log AI.');
 }
 async function poll(id){try{
  const job=await api('/api/yolo/job/'+id);if(active!==id)return;
  el('aiProgress').value=100*job.processed/Math.max(1,job.total);
  status(`Camera ${job.camera}: ${job.processed}/${job.total} hình · ${job.status}`);
  if(job.status==='done'){saveJob(job.camera,id);
   const data=await api('/api/yolo/job/'+id+'/result');data.byFrame=new Map(data.frames.map(r=>[r.frame,r]));data.byTrack=new Map((data.tracks||[]).map(r=>[r.track_id,r]));results[data.camera]=data;last=data;
   el('aiRun').disabled=false;el('aiShow').hidden=false;el('aiDownload').hidden=false;el('aiDownload').href='/api/yolo/job/'+id+'/result';
   data.crossingsReady=false;trackCrossings(data);
   status(`Hoàn tất Camera ${job.camera}: ${job.total} hình trong ${job.elapsed_seconds} giây. Có ${job.detections} lượt phát hiện và ${job.tracks??0} xe được theo dõi. Bấm Xem đoạn đã nhận diện, rồi bấm Phát video để xem log xe qua vạch.`);
  }else if(job.status==='failed'){el('aiRun').disabled=false;status('YOLO: '+job.error)}else timer=setTimeout(()=>poll(id),1500);
 }catch(e){el('aiRun').disabled=false;status('Không đọc được tác vụ: '+e.message)}}
 el('aiRun').onclick=async()=>{if(!s)return status('Chọn phiên trước.');el('aiRun').disabled=true;el('aiShow').hidden=true;el('aiDownload').hidden=true;clearTimeout(timer);status('Khởi tạo AI nhận diện…');try{const job=await api('/api/yolo/'+s.id,{camera:el('aiCamera').value,start:Number(el('aiStart').value),duration:Number(el('aiDuration').value),confidence:Number(el('aiConf').value)});active=job.id;localStorage.setItem('video-ab-yolo',active);poll(active)}catch(e){el('aiRun').disabled=false;status(e.message)}};
 el('aiShow').onclick=safe(async()=>{
  const moved=[];
  for(const camera of ['A','B']){
   const data=results[camera];
   if(!data||data.session_id!==s.id||meta[camera]?.id!==data.media_id)continue;
   await show(camera,data.frames[0].frame);moved.push(camera);
  }
  if(!moved.length)return status('Chưa có kết quả đúng phiên và video này. Hãy chạy AI nhận diện trước.');
  el('camera'+moved[0]).scrollIntoView({block:'center'});
  status('Đã nhảy tới đoạn đã nhận diện của camera '+moved.join(' và ')+'. Bấm Phát video để log xe qua vạch.');
 });
 el('aiVisible').onchange=safe(async()=>{for(const c of ['A','B'])if(meta[c]&&!playing[c])await show(c,frames[c]);});
 el('aiClearLog').onclick=resetLive;
 el('aiRun').disabled=false;renderLog();restore();
})();
