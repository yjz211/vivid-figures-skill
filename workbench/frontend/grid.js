'use strict';
let dataGrid=null,gridReady=false;
function gridRender(){
  gridReady=false;
  if(dataGrid)dataGrid.destroy();
  const table=project.table;
  dataGrid=new Tabulator('#data-table',{
    height:'100%',layout:'fitData',index:'_row',headerSort:false,
    selectableRange:1,selectableRangeColumns:true,selectableRangeRows:true,
    selectableRangeClearCells:false,editTriggerEvent:'dblclick',clipboard:false,
    rowHeader:{title:'#',editableTitle:false,formatter:'rownum',headerSort:false,hozAlign:'center',resizable:false,frozen:true,width:45,editor:false},
    columnDefaults:{headerSort:false,width:112,editor:'input',editableTitle:false,formatter:'plaintext',titleFormatter:col=>{const el=document.createElement('span');el.textContent=col.getColumn().getDefinition().title;return el;},headerDblClick:(e,col)=>renameGridColumn(col),headerContextMenu:[{label:'修改列名',action:(e,col)=>renameGridColumn(col)},{label:'删除此列',action:(e,col)=>deleteDataColumn(Number(col.getField().slice(1)))}]},
    columns:table.headers.map((h,c)=>({title:String(h),field:'c'+c})),
    data:table.rows.map((r,i)=>Object.assign({_row:i},Object.fromEntries(r.map((v,c)=>['c'+c,v])))),
    rowContextMenu:[{label:'删除此行',action:(e,row)=>{remember();project.table.rows.splice(row.getData()._row,1);tableRender();changed();}}],
  });
  const currentGrid=dataGrid;dataGrid.on('tableBuilt',()=>{if(dataGrid===currentGrid)gridReady=true;});
  dataGrid.on('cellEdited',cell=>{remember();project.table.rows[cell.getRow().getData()._row][Number(cell.getField().slice(1))]=cell.getValue();changed();});
  $('table-count').textContent=`${table.rows.length} 行 × ${table.headers.length} 列`;
  $('rows-page').textContent='连续滚动';$('rows-prev').hidden=true;$('rows-next').hidden=true;updateUndo();
}
function renameGridColumn(col){
  const c=Number(col.getField()?.slice(1));if(!Number.isInteger(c))return;
  const holder=col.getElement().querySelector('.tabulator-col-title');if(holder.querySelector('input'))return;
  const input=document.createElement('input');input.className='vivid-header-editor';input.value=project.table.headers[c];holder.replaceChildren(input);
  let cancelled=false;input.onmousedown=e=>e.stopPropagation();input.onclick=e=>e.stopPropagation();
  input.onkeydown=e=>{e.stopPropagation();if(e.key==='Enter')input.blur();if(e.key==='Escape'){cancelled=true;input.blur();}};
  input.onblur=()=>{if(!cancelled&&input.value!==project.table.headers[c]){remember();project.table.headers[c]=input.value;mappingRender();changed();}tableRender();};
  input.focus();input.select();
}
function gridSelection(){
  const range=dataGrid?.getRanges()[0];
  if(!range)return null;
  const rows=range.getRows().map(r=>r.getData()._row).filter(Number.isInteger);
  const cols=range.getColumns().map(c=>Number(c.getField()?.slice(1))).filter(Number.isInteger);
  return rows.length&&cols.length?{rows,cols,r:Math.min(...rows),c:Math.min(...cols)}:null;
}
function gridPaste(text){
  const selection=gridSelection();if(!selection)return toast('先选择粘贴起点');
  let block=parsePaste(text);if(!block.length)return;
  const withHeaders=$('paste-headers').checked;
  const headers=withHeaders?block.shift():null;if(!block.length)return toast('粘贴内容需要包含数据行');
  const width=Math.max(...block.map(r=>r.length),headers?.length||0),r0=selection.r,c0=selection.c;
  const nr=Math.max(project.table.rows.length,r0+block.length),nc=Math.max(project.table.headers.length,c0+width);
  if(nr>20000||nc>256||nr*nc>500000)return toast('粘贴超出容量：最多 20000 行、256 列、500000 格');
  if($('paste-mode').value==='selection'&&(block.length!==selection.rows.length||width!==selection.cols.length))return toast('选区模式要求粘贴尺寸与选区一致；可切换“从起点扩展”');
  remember();while(project.table.headers.length<nc)addColumn();while(project.table.rows.length<nr)project.table.rows.push(Array(nc).fill(''));
  if(headers)headers.forEach((v,j)=>project.table.headers[c0+j]=v);
  block.forEach((row,i)=>{for(let j=0;j<width;j++)project.table.rows[r0+i][c0+j]=row[j]??'';});
  tableRender();mappingRender();changed();toast(`已粘贴 ${block.length} × ${width} 格，可撤销`);
}
function clearGridSelection(){
  const sel=gridSelection();if(!sel)return;remember();
  sel.rows.forEach(r=>sel.cols.forEach(c=>project.table.rows[r][c]=''));tableRender();changed();
}
function installGridEvents(){
  const el=$('data-table');
  el.addEventListener('paste',e=>{if(e.target.matches('input,textarea'))return;e.preventDefault();gridPaste(e.clipboardData.getData('text/plain'));},true);
  el.addEventListener('copy',e=>{if(e.target.matches('input,textarea'))return;const sel=gridSelection();if(!sel)return;e.preventDefault();e.clipboardData.setData('text/plain',sel.rows.map(r=>sel.cols.map(c=>{const v=String(project.table.rows[r][c]??'');return /[\t\n\r"]/.test(v)?'"'+v.replaceAll('"','""')+'"':v;}).join('\t')).join('\n'));});
  el.addEventListener('keydown',e=>{if(e.target.matches('input,textarea'))return;if(['Delete','Backspace'].includes(e.key)){e.preventDefault();e.stopImmediatePropagation();clearGridSelection();}},true);
  $('clear-cells').onclick=clearGridSelection;
  $('delete-rows').onclick=()=>{const sel=gridSelection();if(!sel)return;remember();sel.rows.sort((a,b)=>b-a).forEach(r=>project.table.rows.splice(r,1));tableRender();changed();};
}
function fieldChips(){
  $('field-chips').innerHTML=project.table.headers.map((h,i)=>`<button draggable="true" data-field="${i}" title="拖到下方对应字段">${project.table.rows.slice(0,50).filter(r=>r[i]!==''&&r[i]!=null).every(r=>Number.isFinite(Number(r[i])))?'#':'文'} ${esc(h)}</button>`).join('');
  $('field-chips').querySelectorAll('button').forEach(b=>b.ondragstart=e=>e.dataTransfer.setData('text/vivid-column',b.dataset.field));
  $('mapping-fields').querySelectorAll('select').forEach(select=>{
    select.ondragover=e=>{e.preventDefault();select.classList.add('drop-field');};select.ondragleave=()=>select.classList.remove('drop-field');
    select.ondrop=e=>{e.preventDefault();select.classList.remove('drop-field');const value=e.dataTransfer.getData('text/vivid-column');if(![...select.options].some(o=>o.value===value))return;select.value=value;select.dispatchEvent(new Event('change',{bubbles:true}));};
  });
}
function matchFields(){
  const normalize=s=>String(s).toLowerCase().replace(/[\s_\-（）()]/g,'');
  const selects=[...$('mapping-fields').querySelectorAll('select[data-column-role]')];
  const fields=spec.tables?.find(t=>t.key===project.active_table)?.headers;
  if(!fields)return toast('当前模板使用通用字段，请直接拖动或选择对应列');
  const bindings=fields.map((field,i)=>{const matches=project.table.headers.map((h,j)=>normalize(h)===normalize(field)?j:-1).filter(j=>j>=0);return matches.length===1?matches[0]:-1;});
  remember();project.column_mappings??={};project.column_mappings[project.active_table]=bindings;mappingRender();changed();toast(`已匹配 ${bindings.filter(i=>i>=0).length}/${bindings.length} 个字段，其余请手动指定`);
}
