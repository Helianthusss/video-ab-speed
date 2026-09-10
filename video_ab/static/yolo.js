(() => {
 const el=id=>document.getElementById(id), results={};
 let active,timer,last;
 const status=t=>el('aiStatus').textContent=t;
 window.drawYolo=(camera,index,ctx,canvas)=>{
  const data=results[camera];
  if(!el('aiVisible').checked||!data||data.session_id!==s.id||data.media_id!==meta[camera]?.id)return;
  const row=data.byFrame.get(index);if(!row)return;
  ctx.save();ctx.lineWidth=Math.max(2,canvas.width/500);ctx.font=`${Math.max(15,canvas.width/65)}px sans-serif`;
  for(const b of row.boxes){let [x,y,r,t]=b.xyxyn;x*=canvas.width;r*=canvas.width;y*=canvas.height;t*=canvas.height;ctx.strokeStyle='#41ff84';ctx.strokeRect(x,y,r-x,t-y);const label=b.label+' '+Math.round(b.confidence*100)+'%';ctx.fillStyle='#102c20';ctx.fillRect(x,Math.max(0,y-24),ctx.measureText(label).width+8,24);ctx.fillStyle='#fff';ctx.fillText(label,x+4,Math.max(18,y-5));}
  ctx.restore();
 };
 async function poll(id){try{
  const job=await api('/api/yolo/job/'+id);if(active!==id)return;
  el('aiProgress').value=100*job.processed/Math.max(1,job.total);
  status(`Camera ${job.camera}: ${job.processed}/${job.total} frame · ${job.status}`);
  if(job.status==='done'){
   const data=await api('/api/yolo/job/'+id+'/result');data.byFrame=new Map(data.frames.map(r=>[r.frame,r]));results[data.camera]=data;last=data;
   el('aiRun').disabled=false;el('aiShow').hidden=false;el('aiDownload').hidden=false;el('aiDownload').href='/api/yolo/job/'+id+'/result';
   status(`Hoàn tất Camera ${job.camera}: ${job.total} frame trong ${job.elapsed_seconds} giây, thiết bị ${job.device==='0'?'GPU':job.device}. ${job.detections} lượt phát hiện trên các frame, không phải số xe duy nhất. Bấm Xem đoạn đã nhận diện.`);
  }else if(job.status==='failed'){el('aiRun').disabled=false;status('YOLO: '+job.error)}else timer=setTimeout(()=>poll(id),1500);
 }catch(e){el('aiRun').disabled=false;status('Không đọc được tác vụ: '+e.message)}}
 el('aiRun').onclick=async()=>{if(!s)return status('Chọn phiên trước.');el('aiRun').disabled=true;el('aiShow').hidden=true;el('aiDownload').hidden=true;clearTimeout(timer);status('Khởi tạo YOLO…');try{const job=await api('/api/yolo/'+s.id,{camera:el('aiCamera').value,start:Number(el('aiStart').value),duration:Number(el('aiDuration').value),confidence:Number(el('aiConf').value)});active=job.id;localStorage.setItem('video-ab-yolo',active);poll(active)}catch(e){el('aiRun').disabled=false;status(e.message)}};
 el('aiShow').onclick=safe(async()=>{if(!last||s.id!==last.session_id||meta[last.camera]?.id!==last.media_id)return status('Chọn lại đúng phiên và video của tác vụ này.');await show(last.camera,last.frames[0].frame);el('camera'+last.camera).scrollIntoView({block:'center'});});
 el('aiVisible').onchange=safe(async()=>{for(const c of ['A','B'])if(meta[c]&&!playing[c])await show(c,frames[c]);});
 active=localStorage.getItem('video-ab-yolo');if(active)poll(active);
})();
