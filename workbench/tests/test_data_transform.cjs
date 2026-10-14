const assert=require('node:assert/strict');
const {compute}=require('../frontend/data-transform.js');
let count=0;
function test(name,fn){fn();count++;console.log('PASS '+name);}
const wide={headers:['时间','甲','乙'],rows:[['二月',2,4],['一月',1,3]]};
test('Numeric sort, blanks last, input unchanged',()=>{
 const t={headers:['组','值'],rows:[['a','10'],['b','2'],['c',''],['d','2']]},copy=JSON.stringify(t);
 assert.deepEqual(compute(t,{kind:'sort',column:1}).table.rows.map(r=>r[0]),['b','d','a','c']);
 assert.deepEqual(compute(t,{kind:'sort',column:1,descending:true}).table.rows.map(r=>r[0]),['a','b','d','c']);assert.equal(JSON.stringify(t),copy);
});
test('Filtering does not coerce blank or text to zero',()=>assert.deepEqual(compute({headers:['v'],rows:[[''],['0'],['-2'],['x']]},{kind:'filter',column:0,operator:'gte',value:0}).table.rows,[['0']]));
test('Empty filter results are rejected',()=>assert.throws(()=>compute(wide,{kind:'filter',column:0,operator:'eq',value:'三月'}),/没有数据/));
test('Wide-long-wide round trip preserves data and order',()=>{
 const long=compute(wide,{kind:'melt',id:0,values:[1,2]}).table;
 assert.deepEqual(compute(long,{kind:'pivot',id:0,group:1,value:2}).table,wide);
});
test('Transpose twice preserves labels and values',()=>assert.deepEqual(compute(compute(wide,{kind:'transpose'}).table,{kind:'transpose'}).table,wide));
test('Repeated pivot keys never silently aggregate',()=>assert.throws(()=>compute({headers:['时间','组','值'],rows:[['a','b',1],['a','b',2]]},{kind:'pivot',id:0,group:1,value:2}),/多条记录/));
test('Missing pivot cells remain empty, not fabricated zeros',()=>assert.deepEqual(compute({headers:['t','g','v'],rows:[['1','A',4],['2','B',9]]},{kind:'pivot',id:0,group:1,value:2}).table.rows,[['1',4,''],['2','',9]]));
test('Standard deviation uses sample denominator',()=>{
 const t={headers:['g','v'],rows:[['A',1],['A',3]]};assert.equal(compute(t,{kind:'aggregate',group:0,value:1,method:'std'}).table.rows[0][1],Math.sqrt(2));
 assert.equal(compute(t,{kind:'aggregate',group:0,value:1,method:'mean'}).table.rows[0][1],2);
});
test('Invalid inputs cannot silently enter statistics',()=>{
 for(const v of ['',null,'oops'])assert.throws(()=>compute({headers:['g','v'],rows:[['A',v]]},{kind:'aggregate',group:0,value:1,method:'mean'}),/非数字/);
 assert.throws(()=>compute({headers:['g','v'],rows:[['A',1]]},{kind:'aggregate',group:0,value:1,method:'std'}),/两个数值/);
});
test('Oversized reshape rejected before materialization',()=>assert.throws(()=>compute({headers:['id','a','b'],rows:Array.from({length:11000},(_,i)=>[i,1,2])},{kind:'melt',id:0,values:[1,2]}),/容量/));
test('Duplicate transpose labels rejected',()=>assert.throws(()=>compute({headers:['g','v'],rows:[['A',1],['A',2]]},{kind:'transpose'}),/不重复/));
test('Unknown columns and operators rejected',()=>{assert.throws(()=>compute(wide,{kind:'sort',column:40}));assert.throws(()=>compute(wide,{kind:'filter',column:0,operator:'eval'}));});
console.log(`${count} checks passed`);
