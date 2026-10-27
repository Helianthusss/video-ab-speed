(() => {
 const el=id=>document.getElementById(id), results={};
 let runToken=0;
 const live={seen:{A:new Set(),B:new Set()},pending:{A:[],B:[]},rows:[],reports:[],matches:[],compared:new Set(),rejected:new Set()};
 const status=t=>el('aiStatus').textContent=t;
 const esc=t=>String(t??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
 const wait=ms=>new Promise(r=>setTimeout(r,ms));
 function side(line,point){const [[x1,y1],[x2,y2]]=line,[x,y]=point,v=(x2-x1)*(y-y1)-(y2-y1)*(x-x1);return v>1e-9?1:v<-1e-9?-1:0}
 function ccw(ax,ay,bx,by,cx,cy){return (cy-ay)*(bx-ax)>(by-ay)*(cx-ax)}
 function segsIntersect(p1,p2,p3,p4){
  return (ccw(p1[0],p1[1],p3[0],p3[1],p4[0],p4[1])!==ccw(p2[0],p2[1],p3[0],p3[1],p4[0],p4[1])) &&
         (ccw(p1[0],p1[1],p2[0],p2[1],p3[0],p3[1])!==ccw(p1[0],p1[1],p2[0],p2[1],p4[0],p4[1]));
 }
 function bottomCenterCrossed(line,prev,cur){
  if(!prev)return false;
  const [[x1,y1],[x2,y2]]=line;
  const signed=p=>(x2-x1)*(p[1]-y1)-(y2-y1)*(p[0]-x1);
  const a=signed(prev),b=signed(cur);
  if(Math.abs(a)<1e-9&&Math.abs(b)<1e-9)return false;
  if(a*b>0)return false;
  const fraction=a/(a-b);
  if(fraction<0||fraction>1)return false;
  const x=prev[0]+fraction*(cur[0]-prev[0]),y=prev[1]+fraction*(cur[1]-prev[1]);
  return x>=Math.min(x1,x2)-1e-6&&x<=Math.max(x1,x2)+1e-6&&y>=Math.min(y1,y2)-1e-6&&y<=Math.max(y1,y2)+1e-6;
 }
 function lineIntersectsBox(line,b){
  const [[lx1,ly1],[lx2,ly2]]=line, [bx1,by1,bx2,by2]=b;
  if((lx1>=bx1&&lx1<=bx2&&ly1>=by1&&ly1<=by2)||(lx2>=bx1&&lx2<=bx2&&ly2>=by1&&ly2<=by2))return true;
  const corners=[[bx1,by1],[bx2,by1],[bx2,by2],[bx1,by2]];
  for(let i=0;i<4;i++){
   if(segsIntersect([lx1,ly1],[lx2,ly2],corners[i],corners[(i+1)%4]))return true;
  }
  return false;
 }
 function labelToType(label){return {motorcycle:'MC',bicycle:'MC',car:'Car',bus:'Bus',truck:'Truck'}[label]||'Other'}
 function normTime(camera,time){try{return typeof corr==='function'?corr(time,camera):time}catch{return time}}
 function confidenceFor(match){const speed=match.speed,range=s.protocol?.pilot_speed||[5,120],lo=Math.min(...range),hi=Math.max(...range);if(speed<lo*.65||speed>hi*1.45)return {level:'low',text:'ưu tiên rà soát thời gian'};return {level:'review',text:'chưa xác nhận cùng xe'}}
 function visibleRows(){const type=el('aiLogType')?.value||'all',kind=el('aiLogKind')?.value||'all';return live.rows.filter(r=>(type==='all'||r.type===type)&&(kind==='all'||r.kind===kind||r.level===kind))}
 function renderLog(){const box=el('aiLiveLog');if(!box)return;const rows=visibleRows();if(!live.rows.length){box.innerHTML='<p class="hint">Chưa có log. Hãy chạy AI nhận diện xe A và B, rồi bấm Phát video.</p>';return}if(!rows.length){box.innerHTML='<p class="hint">Không có dòng nào theo bộ lọc hiện tại.</p>';return}box.innerHTML='<table><tr><th>Thời điểm</th><th>Sự kiện</th><th>Ghi chú</th><th>Độ tin cậy</th></tr>'+rows.slice(-120).reverse().map(r=>`<tr><td>${esc(r.time)}</td><td class="${r.kind==='speed'?'ai-event-speed':r.level==='low'?'ai-event-review':''}">${esc(r.event)}</td><td>${esc(r.note)}</td><td>${esc(r.confidenceText||'—')}</td></tr>`).join('')+'</table>'}
 function addLog(row){live.rows.push(row);renderLog()}
 function resetLive(){live.seen={A:new Set(),B:new Set()};live.pending={A:[],B:[]};live.rows=[];live.reports=[];live.matches=[];live.compared=new Set();live.rejected=new Set();el('aiResultsPanel').hidden=true;renderLog()}
 function prepareData(data){data.byFrame=new Map(data.frames.map(r=>[r.frame,r]));data.byTrack=new Map((data.tracks||[]).map(r=>[r.track_id,r]));data.crossingsReady=false;trackCrossings(data);return data}
 function trackCrossings(data){
  if(!data||data.crossingsReady)return;
  const line=s?.lines?.[data.camera];
  data.crossingsReady=true;
  data.crossings=new Map();
  if(!line||line.length<2)return;
  const paths=new Map();
  for(const row of data.frames||[]){
   for(const b of row.boxes||[]){
    if(b.track_id==null)continue;
    if(!paths.has(b.track_id))paths.set(b.track_id,{track_id:b.track_id,label:b.label,type:labelToType(b.label),points:[]});
    paths.get(b.track_id).points.push({box:b.xyxyn,time:row.time,frame:row.frame,confidence:b.confidence});
   }
  }
  for(const tr of paths.values()){
   let prevBottom=null;
   for(const p of tr.points){
    const [x1,y1,x2,y2]=p.box;
    const bottom=[(x1+x2)/2,y2];
    if(bottomCenterCrossed(line,prevBottom,bottom)){
     data.crossings.set(tr.track_id,{...tr,time:p.time,frame:p.frame,confidence:p.confidence});
     break;
    }
    prevBottom=bottom;
   }
  }
 }
 function findMatch(ev){const other=ev.camera==='A'?'B':'A';let best=null,bestIdx=-1;for(let i=0;i<live.pending[other].length;i++){const cand=live.pending[other][i];if(cand.matched||cand.type!==ev.type)continue;const tA=ev.camera==='A'?ev.corrected:cand.corrected,tB=ev.camera==='B'?ev.corrected:cand.corrected;const dt=tB-tA;if(!Number.isFinite(dt)||dt===0||!s?.L)continue;const speed=3.6*s.L/Math.abs(dt);const range=s.protocol?.pilot_speed||[5,120];const plausible=speed>=Math.min(...range)&&speed<=Math.max(...range);if(!plausible)continue;const gap=Math.abs(dt);if(!best||gap<best.gap)best={cand,dt,speed,direction:dt>0?'A→B':'B→A',gap},bestIdx=i;}
  if(best){live.pending[other].splice(bestIdx,1);return best}return null}
 function reportRow(full,match,conf){const a=full.camera==='A'?full:match.cand,b=full.camera==='B'?full:match.cand;return {direction:match.direction,type:full.type,speed:match.speed,travel_seconds:Math.abs(match.dt),time_A:a.corrected,time_B:b.corrected,frame_A:a.camera==='A'?a.frame:match.cand.frame,frame_B:b.camera==='B'?b.frame:match.cand.frame,track_A:a.track_id,track_B:b.track_id,confidence:conf.text,note:'AI đề xuất, cần rà soát đúng cùng xe trước khi dùng chính thức'}}
 function processCrossing(camera,index){if(!el('aiLive')?.checked)return;const data=results[camera];if(!data||data.session_id!==s?.id||data.media_id!==meta[camera]?.id)return;trackCrossings(data);if(!data.crossings?.size)return;for(const ev of data.crossings.values()){if(ev.frame>index)continue;const key=camera+':'+ev.track_id;if(live.seen[camera].has(key))continue;live.seen[camera].add(key);const corrected=normTime(camera,ev.time);const full={...ev,camera,corrected};addLog({kind:'cross',level:'',type:ev.type,event:`Camera ${camera}: xe ${ev.type} #${ev.track_id} qua vạch`,note:`Hình ${ev.frame}, thời điểm ${ev.time.toFixed(3)} giây trong video`,time:corrected?.toFixed?corrected.toFixed(3)+' s':ev.time.toFixed(3)+' s'});const match=findMatch(full);if(match){match.cand.matched=true;const conf=confidenceFor(match,full);const note=`${match.direction}, Δt=${Math.abs(match.dt).toFixed(3)} giây, L=${s.L} m. ${conf.text}.`;addLog({kind:'speed',level:conf.level,type:full.type,event:`Đề xuất tốc độ: ${match.speed.toFixed(2)} km/h`,note,time:(Math.max(full.corrected,match.cand.corrected)).toFixed(3)+' s',confidenceText:conf.text});live.reports.push(reportRow(full,match,conf))}else live.pending[camera].push(full);}}
 window.drawYolo=(camera,index,ctx,canvas)=>{
  const data=results[camera];
  if(!data||data.session_id!==s.id||data.media_id!==meta[camera]?.id)return;
  processCrossing(camera,index);
  if(!el('aiVisible').checked)return;
  let row=data.byFrame.get(index);
  if(!row&&data.frames?.length){
   const stride=data.stride||10;
   let lo=0,hi=data.frames.length-1;
   while(lo<=hi){
    const mid=(lo+hi)>>1;
    if(data.frames[mid].frame===index){row=data.frames[mid];break;}
    if(data.frames[mid].frame<index)lo=mid+1;
    else hi=mid-1;
   }
   if(!row){
    const c1=data.frames[hi],c2=data.frames[lo];
    let best=c1;
    if(!best||(c2&&Math.abs(c2.frame-index)<Math.abs(c1.frame-index)))best=c2;
    if(best&&Math.abs(best.frame-index)<=Math.max(stride,15))row=best;
   }
  }
  if(!row||!row.boxes?.length)return;
  ctx.save();
  ctx.lineWidth=Math.max(2.5,canvas.width/400);
  ctx.font=`bold ${Math.max(14,canvas.width/65)}px sans-serif`;
  for(const b of row.boxes){
   const cross=b.track_id!=null?data.crossings?.get(b.track_id):null;
   const hasCrossed=Boolean(cross&&index>=cross.frame);
   let [x,y,r,t]=b.xyxyn;
   x*=canvas.width;r*=canvas.width;y*=canvas.height;t*=canvas.height;
   ctx.strokeStyle=hasCrossed?'#ffd23f':'#22c55e';
   ctx.strokeRect(x,y,r-x,t-y);
   const typeName=labelToType(b.label);
   const label=(b.track_id!=null?'#'+b.track_id+' ':'')+typeName+(hasCrossed?' · qua vạch':' '+Math.round((b.confidence||0)*100)+'%');
   const textW=ctx.measureText(label).width;
   const pad=6, tagH=22;
   const tagY=Math.max(0,y-tagH);
   ctx.fillStyle=hasCrossed?'rgba(202,138,4,0.92)':'rgba(16,44,32,0.88)';
   ctx.fillRect(x,tagY,textW+pad*2,tagH);
   ctx.fillStyle='#ffffff';
   ctx.fillText(label,x+pad,tagY+16);
  }
  ctx.restore();
 };
 const JOBS='video-ab-yolo-jobs';
 const readJobs=()=>{try{return JSON.parse(localStorage.getItem(JOBS))||{}}catch{return {}}};
 const saveJob=(camera,id)=>{const all=readJobs();all[camera]=id;localStorage.setItem(JOBS,JSON.stringify(all))};
 const pairKey=(a,b)=>`${a}:${b}`;
 function rejectedStorageKey(){const jobs=readJobs();return s?.id&&jobs.A&&jobs.B?`video-ab-rejected:${s.id}:${jobs.A}:${jobs.B}`:null}
 function loadRejected(){const key=rejectedStorageKey();try{live.rejected=new Set(key?JSON.parse(localStorage.getItem(key)||'[]'):[])}catch{live.rejected=new Set()}}
 function saveRejected(){const key=rejectedStorageKey();if(key)localStorage.setItem(key,JSON.stringify([...live.rejected]))}

 function matchAllCrossings(){
  const dataA=results['A'], dataB=results['B'];
  if(!dataA||!dataB)return;
  loadRejected();
  trackCrossings(dataA);
  trackCrossings(dataB);
  const crossA=[...(dataA.crossings?.values()||[])].sort((a,b)=>a.time-b.time);
  const crossB=[...(dataB.crossings?.values()||[])].sort((a,b)=>a.time-b.time);
  const L=Number(s?.L||0);
  const range=s?.protocol?.pilot_speed||[10,80];
  const loSpeed=Math.min(...range);
  const hiSpeed=Math.max(...range);

  function compatible(t1,t2){
   if(t1===t2)return true;
   const heavy=new Set(['Bus','Truck','Light truck/Van']);
   if(heavy.has(t1)&&heavy.has(t2))return true;
   const cars=new Set(['Car','Light truck/Van']);
   if(cars.has(t1)&&cars.has(t2))return true;
   const twoW=new Set(['MC','Other']);
   if(twoW.has(t1)&&twoW.has(t2))return true;
   return false;
  }

  const matches=[];
  const usedB=new Set();

  for(const a of crossA){
   const tA=normTime('A',a.time);
   let best=null, bestGap=Infinity;
   for(const b of crossB){
    if(usedB.has(b.track_id))continue;
    if(live.rejected.has(pairKey(a.track_id,b.track_id)))continue;
    if(!compatible(a.type,b.type))continue;
    const tB=normTime('B',b.time);
    const dt=tB-tA;
    if(dt<=0.2||!Number.isFinite(dt))continue;
    const speed=L>0?(3.6*L/dt):0;
    if(L>0&&(speed<loSpeed||speed>hiSpeed))continue;
    if(dt<bestGap){
     best={cand:b,tB,dt,speed,direction:'A→B'};
     bestGap=dt;
    }
   }
   if(best){
    usedB.add(best.cand.track_id);
    const conf=confidenceFor(best,a);
    matches.push({
     id:`AI_A${a.track_id}_B${best.cand.track_id}`,
     trackA:a.track_id,
     trackB:best.cand.track_id,
     type:a.type===best.cand.type?a.type:(a.type==='Car'?best.cand.type:a.type),
     direction:best.direction,
     frameA:a.frame,
     frameB:best.cand.frame,
     timeA:a.time,
     timeB:best.cand.time,
     corrA:tA,
     corrB:best.tB,
     dt:best.dt,
     speed:best.speed,
     conf:conf.text,
     level:conf.level
    });
   }
  }

  const usedA=new Set(matches.map(m=>m.trackA));
  for(const b of crossB){
   if(usedB.has(b.track_id))continue;
   const tB=normTime('B',b.time);
   let best=null, bestGap=Infinity;
   for(const a of crossA){
    if(usedA.has(a.track_id))continue;
    if(live.rejected.has(pairKey(a.track_id,b.track_id)))continue;
    if(!compatible(a.type,b.type))continue;
    const tA=normTime('A',a.time);
    const dt=tA-tB;
    if(dt<=0.2||!Number.isFinite(dt))continue;
    const speed=L>0?(3.6*L/dt):0;
    if(L>0&&(speed<loSpeed||speed>hiSpeed))continue;
    if(dt<bestGap){
     best={cand:a,tA,dt,speed,direction:'B→A'};
     bestGap=dt;
    }
   }
   if(best){
    usedA.add(best.cand.track_id);
    usedB.add(b.track_id);
    const conf=confidenceFor(best,b);
    matches.push({
     id:`AI_B${b.track_id}_A${best.cand.track_id}`,
     trackA:best.cand.track_id,
     trackB:b.track_id,
     type:b.type===best.cand.type?b.type:(b.type==='Car'?best.cand.type:b.type),
     direction:best.direction,
     frameA:best.cand.frame,
     frameB:b.frame,
     timeA:best.cand.time,
     timeB:b.time,
     corrA:best.tA,
     corrB:tB,
     dt:best.dt,
     speed:best.speed,
     conf:conf.text,
     level:conf.level
    });
   }
  }

  live.matches=matches;
  renderMatchedResults();
 }

 function renderMatchedResults(){
  const panel=el('aiResultsPanel');
  if(!panel)return;
  const matches=live.matches||[];
  const cA=results.A?.crossings?.size||0;
  const cB=results.B?.crossings?.size||0;
  panel.hidden=false;
  const speedRange=s?.protocol?.pilot_speed||[10,80];
  const stride=results.A?.stride||1;
  el('aiResultsSummary').textContent=`A: ${cA} lượt · B: ${cB} lượt · ${matches.length} cặp gợi ý · ${Math.max(0,cA-matches.length)} lượt A và ${Math.max(0,cB-matches.length)} lượt B chưa có cặp${live.rejected.size?` · đã loại ${live.rejected.size} cặp sai`:''}. Lọc theo loại xe và ${speedRange.join('–')} km/h.${stride>1?` Chế độ mỗi ${stride} frame có thể bỏ sót xe.`:''} Chưa xác nhận cùng phương tiện.`;
  const body=el('aiResultsBody');
  if(!matches.length){
   body.innerHTML=`<tr><td colspan="9" class="hint" style="text-align:center;padding:16px;">Chưa có cặp gợi ý. Kiểm tra vạch A/B, đồng bộ thời gian và khoảng cách L; thử tắt “Quét gần vạch” nếu xe bị che khuất.</td></tr>`;
   return;
  }
  body.innerHTML=matches.map((m,idx)=>`
   <tr class="ai-match-row">
    <td><b>#A${esc(m.trackA)} → #B${esc(m.trackB)}</b></td>
    <td><span class="badge">${esc(m.type)}</span></td>
    <td>${esc(m.direction)}</td>
    <td>Hình ${m.frameA} (${m.timeA.toFixed(2)}s)</td>
    <td>Hình ${m.frameB} (${m.timeB.toFixed(2)}s)</td>
    <td><b>${m.dt.toFixed(2)}s</b></td>
    <td style="color:var(--success,#16a34a);font-weight:700;font-size:1.1em;">${m.speed.toFixed(1)} km/h</td>
    <td><span class="status-warn">${esc(m.conf)}</span></td>
    <td style="display:flex;gap:6px;flex-wrap:wrap;">
     <button class="secondary btn-verify-pair" data-idx="${idx}" title="Nhảy cả Camera A và B tới đúng frame xe này chạm vạch">👁 So sánh</button>
     <button class="btn-import-pair" data-idx="${idx}" title="Đưa cặp đã đối chiếu vào danh sách rà soát" ${live.compared.has(m.id)?'':'disabled'}>Đưa vào rà soát</button>
     <button class="secondary btn-reject-pair" data-idx="${idx}" title="Loại cặp sai và tìm ứng viên khác">Không cùng xe</button>
    </td>
   </tr>
  `).join('');

  body.querySelectorAll('.btn-verify-pair').forEach(btn=>{
   btn.onclick=()=>verifyPair(Number(btn.dataset.idx));
  });
  body.querySelectorAll('.btn-import-pair').forEach(btn=>{
   btn.onclick=safe(()=>importPair(Number(btn.dataset.idx)));
  });
  body.querySelectorAll('.btn-reject-pair').forEach(btn=>{
   btn.onclick=()=>rejectPair(Number(btn.dataset.idx));
  });
 }

 function rejectPair(idx){
  const m=live.matches?.[idx];
  if(!m)return;
  live.rejected.add(pairKey(m.trackA,m.trackB));
  live.compared.delete(m.id);
  saveRejected();
  matchAllCrossings();
  status(`Đã loại cặp A#${m.trackA} – B#${m.trackB}. Danh sách đã thử ghép lại các xe còn lại; hãy kiểm tra ứng viên mới.`);
 }

 async function verifyPair(idx){
  const m=live.matches?.[idx];
  if(!m)return;
  stopPlayback('A');
  stopPlayback('B');
  await Promise.all([show('A',m.frameA), show('B',m.frameB)]);
  live.compared.add(m.id);
  renderMatchedResults();
  el('videos')?.scrollIntoView({behavior:'smooth',block:'start'});
  status(`Đã mở hai frame của cặp gợi ý A#${m.trackA} – B#${m.trackB}. Hãy đối chiếu màu, hình dáng và thứ tự xe trước khi đưa vào rà soát.`);
 }

 async function importPair(idx){
  const m=live.matches?.[idx];
  if(!m)return;
  if(!live.compared.has(m.id))return status('Hãy bấm So sánh và xem hai frame trước khi nhập cặp xe.');
  if(!confirm(`Bạn đã đối chiếu A#${m.trackA} và B#${m.trackB} là cùng một xe? Cặp này sẽ vào danh sách chờ rà soát, chưa được dùng làm kết quả nghiên cứu.`))return;
  const rec={
   id:m.id,
   type:m.type.includes('/')?m.type.split('/')[0]:m.type,
   direction:m.direction,
   frameA:m.frameA,
   frameB:m.frameB,
   description:`AI YOLO ghép A#${m.trackA}-B#${m.trackB} (v=${m.speed.toFixed(1)} km/h)`
  };
  await act('batch_ai_records',{records:[rec]});
  status(`Đã đưa cặp A#${m.trackA} – B#${m.trackB} vào danh sách chờ rà soát.`);
 }

 function exportMatchedCsv(){
  const matches=live.matches||[];
  if(!matches.length)return status('Chưa có danh sách xe ghép cặp để xuất.');
  const cols=['id','type','direction','frameA','timeA','frameB','timeB','delta_t','speed_kmh','confidence'];
  const rows=matches.map(m=>[
   m.id, m.type, m.direction, m.frameA, m.timeA.toFixed(3),
   m.frameB, m.timeB.toFixed(3), m.dt.toFixed(3), m.speed.toFixed(2), m.conf
  ]);
  const csv='\ufeff'+[cols.join(','),...rows.map(r=>r.map(v=>'"'+String(v??'').replaceAll('"','""')+'"').join(','))].join('\n');
  const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));
  const a=document.createElement('a');
  a.href=url;
  a.download=`ai-van-toc-de-xuat-${new Date().toISOString().slice(0,19).replace(/[:T]/g,'-')}.csv`;
  a.click();
  setTimeout(()=>URL.revokeObjectURL(url),2000);
  status('Đã xuất file CSV bảng vận tốc đề xuất.');
 }

 async function restore(){
  const sessionId=s?.id;
  if(!sessionId)return;
  const restoredJobs={};
  let staleFound=false;
  for(const [camera,id] of Object.entries(readJobs())){
   if(s?.id!==sessionId)return;
   try{
    const job=await api('/api/yolo/job/'+id);
    if(job.status!=='done')continue;
    if(job.session_id!==sessionId||job.camera!==camera||job.media_id!==meta[camera]?.id){staleFound=true;continue}
    const raw=await api('/api/yolo/job/'+id+'/result');
    if(s?.id!==sessionId||raw.session_id!==sessionId||raw.camera!==camera||raw.media_id!==meta[camera]?.id||raw.crossing_method!=='bottom-center-v2'||raw.distance_m!==s.L||JSON.stringify(raw.lines)!==JSON.stringify(s.lines)){staleFound=true;continue}
    const data=prepareData(raw);
    results[camera]=data;
    restoredJobs[camera]=job;
    el('aiShow').hidden=false;
    el('aiDownload'+camera).hidden=false;
    el('aiDownload'+camera).href='/api/yolo/job/'+id+'/result';
   }catch{}
  }
  const co=Object.keys(results);
  if(co.length===2){
   if(restoredJobs.A.stride!==restoredJobs.B.stride||restoredJobs.A.confidence!==restoredJobs.B.confidence||results.A.roi!==results.B.roi){
    clearResults('Kết quả A và B dùng cấu hình AI khác nhau. Hãy quét lại hai camera.');
    return;
   }
   el('aiStride').value=String(restoredJobs.A.stride);
   el('aiConf').value=String(restoredJobs.A.confidence);
   el('aiRoi').checked=Boolean(results.A.roi);
   matchAllCrossings();
   el('aiProgress').value=100;
   status(`Đã nạp kết quả đúng phiên cho A và B: ${live.matches.length} cặp gợi ý cần đối chiếu.`);
  }else if(co.length){
   status('Chỉ có kết quả AI cho Camera '+co[0]+'. Hãy chạy AI cho cả hai camera để tạo cặp gợi ý.');
  }else{
   status(staleFound?'Kết quả AI cũ không còn khớp phiên, video hoặc vạch đo hiện tại. Hãy quét lại hai camera.':'Chưa có kết quả AI cho phiên và hai video hiện tại.');
  }
 }
 async function waitJob(id,token){for(;;){if(token!==runToken)throw Error('Đã hủy tác vụ AI cũ');const job=await api('/api/yolo/job/'+id);el('aiProgress').value=100*job.processed/Math.max(1,job.total);const phase=job.status==='queued'?'đang xếp hàng':job.status==='loading_model'||(job.status==='running'&&!job.processed)?'đang nạp model và chuẩn bị video':job.status==='done'?'đã hoàn tất':`${job.processed}/${job.total} frame`;status(`Camera ${job.camera}: ${phase}${job.status==='running'&&job.processed?` · ${Math.round(100*job.processed/Math.max(1,job.total))}%`:''}`);if(job.status==='done')return job;if(job.status==='failed')throw Error(job.error||'AI nhận diện lỗi');await wait(350)}}
 async function runCamera(camera,token){status('Bắt đầu AI nhận diện Camera '+camera+'…');let job;for(let attempt=0;attempt<40;attempt++){if(token!==runToken)throw Error('Đã hủy tác vụ AI cũ');try{job=await api('/api/yolo/'+s.id,{camera,start:0,duration:0,full:true,stride:Number(el('aiStride').value||1),roi:el('aiRoi')?.checked!==false,confidence:Number(el('aiConf').value)});break}catch(e){if(!e.message.includes('Đang có tác vụ YOLO chạy')||attempt===39)throw e;status('Đang chuyển sang Camera '+camera+'; chờ GPU sẵn sàng…');await wait(250)}}const done=await waitJob(job.id,token);saveJob(camera,job.id);const data=prepareData(await api('/api/yolo/job/'+job.id+'/result'));results[camera]=data;const crossingCount=data.crossings?.size||0;status(`Hoàn tất Camera ${camera}: ${done.total} hình đã chọn, ${done.detections} lượt phát hiện, ${crossingCount} xe qua vạch.`);return {job:done,data}}
 el('aiRun').onclick=async()=>{if(!s)return status('Chọn phiên trước.');if(!meta.A||!meta.B)return status('Hãy nhập đủ video Camera A và Camera B trước.');if(!s.lines?.A||!s.lines?.B||!s.line_locked?.A||!s.line_locked?.B)return status('Hãy vẽ và khóa vạch A, B trước khi chạy AI.');if(!s.observer||!(s.L>0)||!s.sync?.verified||!s.sync?.references?.length)return status('Hãy nhập người thao tác, khoảng cách L và căn cứ đồng bộ trước khi quét AI.');const token=++runToken;resetLive();delete results.A;delete results.B;el('aiRun').disabled=true;el('aiShow').hidden=true;for(const c of ['A','B'])el('aiDownload'+c).hidden=true;try{const a=await runCamera('A',token);const b=await runCamera('B',token);if(token!==runToken)return;el('aiRun').disabled=false;el('aiShow').hidden=false;for(const [c,job] of [['A',a.job],['B',b.job]]){el('aiDownload'+c).href='/api/yolo/job/'+job.id+'/result';el('aiDownload'+c).hidden=false}matchAllCrossings();status(`Đã quét A (${a.data.crossings?.size||0} lượt) và B (${b.data.crossings?.size||0} lượt): ${live.matches.length} cặp gợi ý. Mở bảng bên dưới và đối chiếu hai frame trước khi nhập.`)}catch(e){if(token===runToken){el('aiRun').disabled=false;status(e.message)}}};
 el('aiShow').onclick=safe(async()=>{const moved=[];for(const camera of ['A','B']){const data=results[camera];if(!data||data.session_id!==s.id||meta[camera]?.id!==data.media_id)continue;const firstCross=[...(data.crossings?.values()||[])].sort((a,b)=>a.frame-b.frame)[0];await show(camera,firstCross?.frame??data.frames[0].frame);moved.push(camera)}if(!moved.length)return status('Chưa có kết quả đúng phiên và video này. Hãy chạy AI nhận diện trước.');el('camera'+moved[0]).scrollIntoView({block:'center'});status('Đã nhảy tới xe qua vạch đầu tiên của camera '+moved.join(' và ')+'.')});
 function exportDemo(){if(!live.reports.length)return status('Chưa có tốc độ AI đề xuất để xuất báo cáo. Hãy phát video tới khi có dòng tốc độ.');const cols=['direction','type','speed','travel_seconds','time_A','time_B','frame_A','frame_B','track_A','track_B','confidence','note'];const csv='\ufeff'+[cols.join(','),...live.reports.map(r=>cols.map(k=>'"'+String(r[k]??'').replaceAll('"','""')+'"').join(','))].join('\n');const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download=`bao-cao-demo-ai-${new Date().toISOString().slice(0,19).replace(/[:T]/g,'-')}.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);status('Đã tạo báo cáo demo nhanh dạng CSV. Đây là kết quả AI đề xuất để rà soát.')}
 el('aiVisible').onchange=safe(async()=>{for(const c of ['A','B'])if(meta[c]&&!playing[c])await show(c,frames[c])});
 el('aiClearLog').onclick=resetLive;el('aiExportDemo').onclick=exportDemo;el('aiLogType').onchange=renderLog;el('aiLogKind').onchange=renderLog;
 el('aiExportMatched')?.addEventListener('click',exportMatchedCsv);
 function clearResults(message){runToken++;delete results.A;delete results.B;resetLive();el('aiShow').hidden=true;for(const c of ['A','B'])el('aiDownload'+c).hidden=true;el('aiProgress').value=0;status(message)}
 window.addEventListener('ab:session-loaded',()=>{clearResults('Đang kiểm tra kết quả AI của phiên hiện tại…');restore()});
 window.addEventListener('ab:measurement-settings-changed',()=>clearResults('Thiết lập đo đã đổi. Hãy chạy lại AI để tạo cặp gợi ý mới.'));
 el('aiRun').disabled=false;renderLog();
})();
