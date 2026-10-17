'use strict';
window.VividModelSettings={bind({api,toast,onChange=()=>{}}){
 const el=id=>document.getElementById(id);
 function fields(){const useAPI=el('provider').value==='api';el('api-fields').hidden=!useAPI;el('cli-hint').hidden=useAPI;}
 function paint(c){el('provider').value=c.provider;el('api-url').value=c.base_url;el('model-name').value=c.model;el('api-key').value='';el('api-key').placeholder=c.has_key?'已保存密钥；留空保持':'请输入 API Key';el('visual-review').checked=c.review;el('model-badge').textContent=c.provider==='codex'?(c.codex_available?'● Codex CLI 已找到':'○ Codex CLI 待安装'):'● '+(c.model||'API 待配置');fields();onChange(c);}
 async function save(){const data={provider:el('provider').value,base_url:el('api-url').value,model:el('model-name').value,review:el('visual-review').checked};if(el('api-key').value)data.api_key=el('api-key').value;const c=await api('/api/agent/config',data);paint(c);return c;}
 el('provider').onchange=fields;
 el('model-open').onclick=async()=>{try{paint(await api('/api/agent/config'));el('model-result').textContent='';el('model-dialog').showModal();}catch(e){toast(e.message);}};
 el('model-form').onsubmit=async e=>{e.preventDefault();try{await save();el('model-dialog').close();toast('模型设置已保存。');}catch(err){el('model-result').textContent=err.message;}};
 el('model-test').onclick=async()=>{el('model-test').disabled=true;el('model-result').textContent='正在实际调用所选模型…';try{await save();const r=await api('/api/agent/config/test',{});el('model-result').textContent=r.message+' · '+r.usage.seconds+' 秒';}catch(e){el('model-result').textContent=e.message;}finally{el('model-test').disabled=false;}};
 return {paint,save};
}};
