/* Deterministic table operations; input is never mutated. Shared with Node tests. */
(function(root){
  'use strict';
  const empty=v=>v==null||String(v).trim()==='';
  const number=v=>!empty(v)&&Number.isFinite(Number(v));
  function checkSize(rows,cols){if(rows>20000||cols>256||rows*cols>500000)throw Error('结果超出容量：最多 20000 行、256 列、500000 格。');}
  function unique(headers){const seen=new Set();return headers.map(v=>{const name=String(v),base=name||'未命名';let h=base,i=2;while(seen.has(h))h=base+' ('+(i++)+')';seen.add(h);return h;});}
  function compute(table,op){
    const headers=table.headers.map(String),rows=table.rows.map(r=>headers.map((_,i)=>r[i]??''));
    const col=c=>{if(!Number.isInteger(c)||c<0||c>=headers.length)throw Error('请选择有效的数据列。');return c;};
    const numeric=v=>{if(!number(v))throw Error('参与计算的数值包含空白或非数字，请先处理。');return Number(v);};
    let out,structural=false;
    if(op.kind==='sort'){
      const c=col(op.column),values=rows.map(r=>r[c]).filter(v=>!empty(v)),isNumber=values.length>0&&values.every(number);
      rows.sort((a,b)=>{if(empty(a[c]))return empty(b[c])?0:1;if(empty(b[c]))return -1;const diff=isNumber?Number(a[c])-Number(b[c]):String(a[c]).localeCompare(String(b[c]),'zh-CN',{numeric:true});return op.descending?-diff:diff;});
      out={headers,rows};
    }else if(op.kind==='filter'){
      const c=col(op.column),q=String(op.value??'');
      if(['gt','gte','lt','lte'].includes(op.operator)&&!number(q))throw Error('数值筛选需要填写一个有效数字。');
      const tests={eq:v=>String(v)===q,ne:v=>String(v)!==q,contains:v=>String(v).includes(q),nonempty:v=>!empty(v),empty,
        gt:v=>number(v)&&Number(v)>Number(q),gte:v=>number(v)&&Number(v)>=Number(q),lt:v=>number(v)&&Number(v)<Number(q),lte:v=>number(v)&&Number(v)<=Number(q)};
      if(!tests[op.operator])throw Error('请选择筛选条件。');out={headers,rows:rows.filter(r=>tests[op.operator](r[c]))};
    }else if(op.kind==='transpose'){
      if(headers.length<2||!rows.length)throw Error('转置至少需要一行数据、两列。');checkSize(headers.length-1,rows.length+1);
      const labels=rows.map(r=>String(r[0]));if(labels.some(empty)||new Set(labels).size!==labels.length||labels.includes(headers[0]))throw Error('转置时首列将成为表头，请先确保首列非空且不重复，也不与首列表头同名。');
      out={headers:[headers[0],...labels],rows:headers.slice(1).map((h,c)=>[h,...rows.map(r=>r[c+1])])};structural=true;
    }else if(op.kind==='melt'){
      const id=col(op.id),values=[...new Set(op.values||[])];if(!values.length)throw Error('至少选择一个数值列。');values.forEach(c=>{col(c);if(c===id)throw Error('标识列不能同时作为数值列。');});if(new Set(values.map(c=>headers[c])).size!==values.length)throw Error('数值列名称重复，请先重命名再转成长表。');checkSize(rows.length*values.length,3);
      out={headers:unique([headers[id],'系列','数值']),rows:rows.flatMap(r=>values.map(c=>[r[id],headers[c],r[c]]))};structural=true;
    }else if(op.kind==='pivot'){
      const id=col(op.id),group=col(op.group),value=col(op.value);if(new Set([id,group,value]).size!==3)throw Error('行标识、系列和数值必须选择不同的列。');
      const groups=[],byRow=new Map();
      for(const r of rows){if(empty(r[id])||empty(r[group]))throw Error('行标识与系列名称不能留空。');const k=String(r[id]),g=String(r[group]);
        if(!groups.includes(g))groups.push(g);if(!byRow.has(k))byRow.set(k,new Map());const bucket=byRow.get(k);
        if(bucket.has(g))throw Error('同一行标识与系列有多条记录，请先明确汇总方式，不能直接转宽表。');bucket.set(g,r[value]);checkSize(byRow.size,groups.length+1);
      }
      if(groups.includes(headers[id]))throw Error('系列名称与标识列表头相同，请先重命名。');
      out={headers:[headers[id],...groups],rows:[...byRow].map(([k,b])=>[k,...groups.map(g=>b.get(g)??'')])};structural=true;
    }else if(op.kind==='aggregate'){
      const group=col(op.group),value=col(op.value);if(group===value)throw Error('分组列与数值列必须不同。');
      const buckets=new Map();for(const r of rows){if(empty(r[group]))throw Error('分组列不能留空。');const g=String(r[group]);if(!buckets.has(g))buckets.set(g,[]);buckets.get(g).push(numeric(r[value]));}
      const names={mean:'均值',sum:'合计',std:'样本标准差',count:'有效数值个数'};if(!names[op.method])throw Error('请选择汇总方式。');
      out={headers:unique([headers[group],headers[value]+'_'+names[op.method]]),rows:[...buckets].map(([g,vs])=>{const mean=vs.reduce((a,b)=>a+b,0)/vs.length;let v;
        if(op.method==='std'){if(vs.length<2)throw Error('计算样本标准差时每组至少需要两个数值。');v=Math.sqrt(vs.reduce((a,b)=>a+(b-mean)**2,0)/(vs.length-1));}
        else v=op.method==='mean'?mean:op.method==='sum'?vs.reduce((a,b)=>a+b,0):vs.length;
        if(!Number.isFinite(v))throw Error('汇总结果超出数值范围。');return [g,v];})};structural=true;
    }else throw Error('未知整理操作。');
    checkSize(out.rows.length,out.headers.length);if(!out.rows.length)throw Error('处理结果没有数据行，请调整条件。');
    return {table:out,structural};
  }
  const api={compute,number,empty};root.VividTransform=api;if(typeof module!=='undefined')module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
