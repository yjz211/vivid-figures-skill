"""Agent boundaries: durable replay, conflicts, clarification, cancellation, private paths."""
from pathlib import Path
import copy, json, os, sys, tempfile, threading, time, unittest
from unittest.mock import patch
WEB=Path(__file__).resolve().parents[1]
TEMP=tempfile.TemporaryDirectory(prefix='vivid-agent-tests-')
os.environ['VIVID_AGENT_HOME']=TEMP.name
sys.path.insert(0,str(WEB/'editor_backend'))
from fastapi.testclient import TestClient
from agent import store, tools, provider, runtime
from schema import sample
from agent_server import app

def settled(rid):
    for _ in range(150):
        r=store.run(rid)
        if r['status'] in ['done','waiting','error','cancelled'] and rid not in runtime.THREADS:return r
        time.sleep(.03)
    raise AssertionError('test run did not settle')

class Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client=TestClient(app,base_url='http://127.0.0.1:8766');cls.client.__enter__()
        cls.token=cls.client.get('/api/bootstrap').json()['token']
        cls.client.headers['x-vivid-token']=cls.token
    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None,None,None)
        runtime.CHECKPOINT_CONNECTION.close();TEMP.cleanup()
    def test_private_paths_and_origin(self):
        for path in ['/workspace/agent/settings.json','/.venv/pyvenv.cfg','/editor_backend/agent/provider.py','/assets/%2e%2e/workspace/agent/settings.json','/frontend/%2e%2e/editor_backend/agent/provider.py']:
            self.assertEqual(self.client.get(path).status_code,404,path)
        self.assertEqual(self.client.get('/api/bootstrap',headers={'Host':'evil.example'}).status_code,403)
        self.assertEqual(self.client.post('/api/agent/sessions',json={},headers={'Origin':'https://example.org'}).status_code,403)
        self.assertEqual(self.client.post('/api/agent/sessions',json={},headers={'x-vivid-token':'wrong'}).status_code,403)
        expected={card['id'] for card in json.loads((WEB.parent/'catalog/cards.json').read_text(encoding='utf8'))['cards']}
        actual={template['id'] for template in self.client.get('/api/templates').json()['templates']}
        self.assertIn('advanced.grouped_radial_bar',actual)
        self.assertEqual(actual,expected)
    def test_version_conflict_and_idempotence(self):
        s=store.create_session('CAS test');p=sample('basic.grouped_bar')
        c=store.create_chart(s['id'],p,operation='create-once');again=store.create_chart(s['id'],p,operation='create-once')
        self.assertEqual(c['id'],again['id']);self.assertEqual(len(store.session(s['id'])['charts']),1)
        manual=copy.deepcopy(p);manual['settings']['title']='手动标题'
        latest=store.save_revision(c['id'],1,manual,operation='save-once')
        replay=store.save_revision(c['id'],1,manual,operation='save-once');self.assertEqual(replay['revision'],2)
        with self.assertRaises(store.Conflict):store.save_revision(c['id'],1,p)
        run=store.create_run(s['id'],c['id'],{'prompt':'换配色'})
        proposed=copy.deepcopy(p);proposed['settings']['palette']='blue-sky'
        st={'run_id':run['id'],'session_id':s['id'],'chart_id':c['id'],'base_revision':1,'project':proposed,'prompt':'换配色','dirty':True,'decision':{'message':'修改完成'}}
        first=runtime.finalize(st);replay=runtime.finalize(st)
        self.assertTrue(first['result']['conflict']);self.assertEqual(first,replay)
        self.assertEqual(store.chart(c['id'])['project']['settings']['title'],'手动标题')
        self.assertEqual(len(store.session(s['id'])['messages']),1)
        restored=store.save_revision(c['id'],2,p,'restore');self.assertEqual(restored['revision'],3)
        self.assertEqual(store.chart(c['id'],2)['project'],manual)
    def test_transform_and_bind(self):
        t={'headers':['组别','值'],'rows':[['甲',1],['甲',3],['乙',2],['乙',4]]}
        out=tools.transform_table(t,{'kind':'aggregate','group':0,'value':1,'method':'mean'})
        self.assertEqual(out['rows'],[['甲',2],['乙',3]]);self.assertEqual(len(t['rows']),4)
        p=tools.bind_template('basic.grouped_bar',[{'id':'d','table':out}],[{'table_key':'data','dataset_id':'d'}])
        self.assertEqual(p['table'],out)
        with self.assertRaises(ValueError):tools.bind_template('basic.grouped_bar',[],[{'table_key':'data','dataset_id':'missing'}])
        with self.assertRaises(ValueError):tools.transform_table(t,{'kind':'pivot','id':0,'group':0,'value':1})
    def test_manual_binding_and_matrix_columns(self):
        s=store.create_session('manual binding')
        table={'headers':['备注','二月','地区','一月'],'rows':[['保留',7,'北区',5],['保留',8,'南区',6]]}
        d=store.dataset(s['id'],'reordered matrix',table)
        args={'template_id':'competition.spatiotemporal_heatmap','bindings':[{'table_key':'data','dataset_id':d['id'],'columns':[2,3,1]}]}
        r=self.client.post('/api/agent/sessions/'+s['id']+'/bind',json=args)
        self.assertEqual(r.status_code,200,r.text)
        p=r.json()['project'];self.assertEqual(p['tables']['data'],{'headers':['地区','一月','二月'],'rows':[['北区',5,7],['南区',6,8]]})
        self.assertEqual(store.session(s['id'])['datasets'][0]['table'],table)
        args['bindings'][0]['columns']=[2,2]
        self.assertEqual(self.client.post('/api/agent/sessions/'+s['id']+'/bind',json=args).status_code,400)
    def test_excel_cover_sheet_does_not_block_data_selection(self):
        import openpyxl,io,base64
        book=openpyxl.Workbook();book.active.title='说明';book.active.append(['封面，不是数据'])
        sheet=book.create_sheet('实际数据');sheet.append(['地区',0]);sheet.append(['园区甲',12])
        stream=io.BytesIO();book.save(stream)
        data={'name':'多表.xlsx','content':base64.b64encode(stream.getvalue()).decode()}
        listing=self.client.post('/api/import',json={**data,'list_sheets':True})
        self.assertEqual(listing.status_code,200);self.assertEqual(listing.json()['sheets'],['说明','实际数据'])
        selected=self.client.post('/api/import',json={**data,'sheet':'实际数据'})
        self.assertEqual(selected.status_code,200);self.assertEqual(selected.json()['table'],{'headers':['地区','0'],'rows':[['园区甲',12]]})
    def test_new_chart_target_and_scoped_data(self):
        s=store.create_session('new target');old=store.create_chart(s['id'],sample('basic.line'))
        good=store.dataset(s['id'],'selected',{'headers':['类别','数值'],'rows':[['甲',5],['乙',9]]})
        other=store.dataset(s['id'],'not selected',{'headers':['类别','数值'],'rows':[['甲',99],['乙',98]]})
        with patch.object(runtime,'launch'):
            r=runtime.start(s['id'],'用选中数据另画一张',old['id'],target='new',dataset_ids=[good['id']])
        st={**r['body']['initial'],'run_id':r['id']};self.assertFalse(st['chart_id']);self.assertIsNone(st['project'])
        self.assertEqual([d['id'] for d in runtime.context(st)['datasets']],[good['id']])
        st.update(round=1,decision={'status':'complete','actions':[{'tool':'inspect_template','arguments_json':json.dumps({'template_id':'basic.grouped_bar'})},{'tool':'bind_template','arguments_json':json.dumps({'template_id':'basic.grouped_bar','target':'new','bindings':[{'table_key':'data','dataset_id':good['id']}]})}]})
        bound=runtime.execute(st);result=runtime.finalize(bound)['result']
        self.assertNotEqual(result['chart_id'],old['id']);self.assertEqual(store.chart(old['id'])['revision'],1)
        self.assertEqual(len(store.session(s['id'])['charts']),2)
        # Natural-language "new" can also be expressed by the validated tool target.
        st.update(chart_id=old['id'],project=old['project'],base_revision=1,target='current')
        bound=runtime.execute(st);self.assertFalse(bound['chart_id'])
        with self.assertRaises(ValueError):runtime.start(s['id'],'无效数据',dataset_ids=['foreign-dataset'])
    def test_clarify_reconnect_resume(self):
        s=store.create_session('clarification');calls=[]
        def model(*a,**kw):
            calls.append(1)
            return ({'message':'需要确认','status':'question','question':'请说明误差的含义。','actions':[]} if len(calls)==1 else {'message':'已收到标准差定义。','status':'complete','question':'','actions':[]}),{}
        with patch.object(provider,'call',model):
            r=runtime.start(s['id'],'误差含义不明');self.assertEqual(settled(r['id'])['status'],'waiting')
            stream=self.client.get('/api/agent/runs/'+r['id']+'/events')
            self.assertIn('RUN_STARTED',stream.text);self.assertIn('event: settled',stream.text)
            runtime.CHECKPOINT_CONNECTION.close();runtime.init() # actual SQLite reopen
            runtime.resume(r['id'],'误差是样本标准差')
            self.assertEqual(settled(r['id'])['status'],'done');self.assertEqual(len(calls),2)
    def test_cancel_and_retry_after_failure(self):
        s=store.create_session('cancel')
        def blocking(prompt,schema,path,cancelled,*a,**kw):
            while not cancelled():time.sleep(.01)
            raise InterruptedError()
        with patch.object(provider,'call',blocking):
            r=runtime.start(s['id'],'测试停止');time.sleep(.1);runtime.stop(r['id'])
            self.assertEqual(settled(r['id'])['status'],'cancelled')
        with patch.object(provider,'call',side_effect=RuntimeError('连接失败')):
            r=runtime.start(s['id'],'测试重试');self.assertEqual(settled(r['id'])['status'],'error')
        with patch.object(provider,'call',return_value=({'message':'已恢复','status':'complete','question':'','actions':[]},{})):
            runtime.CHECKPOINT_CONNECTION.close();runtime.init();runtime.resume(r['id'])
            self.assertEqual(settled(r['id'])['status'],'done')
    def test_credentials_not_returned(self):
        provider.save_config({'provider':'api','model':'test','api_key':'test-secret-marker'})
        public=provider.config(public=True);self.assertTrue(public['has_key']);self.assertNotIn('test-secret-marker',json.dumps(public))
        self.assertNotIn('test-secret-marker',provider.SETTINGS.read_text())
        self.assertEqual(provider.config()['api_key'],'test-secret-marker')

    def test_review_preserves_manual_properties(self):
        from jsonschema import validate,ValidationError
        bad={'summary':'','preserve':[],'issues':['color'],'edits':[{'object_id':'title','property':'color','value_json':'"red"'}]}
        with self.assertRaises(ValidationError):validate(bad,provider.REVIEW_SCHEMA)
        s=store.create_session('review protection');p=sample('basic.line')
        p['object_edits']={'title':{'guard':'g','props':{'offset_x':18}}}
        f=Path(TEMP.name)/'review-fixture';f.mkdir();(f/'project.json').write_text(json.dumps(p),encoding='utf8')
        (f/'objects.json').write_text(json.dumps({'guard':'g','objects':[{'id':'title','props':{'offset_x':18}}]}),encoding='utf8')
        r=store.create_run(s['id'],None,{'prompt':'review'})
        response={'summary':'标题靠近边缘','preserve':['手动位置'],'issues':['标题靠近边缘'],'edits':[{'object_id':'title','property':'offset_x','value_json':'0'}]}
        with patch.object(runtime.jobs,'folder',return_value=f),patch.object(provider,'call',return_value=(response,{})),patch.object(runtime,'render') as rendering:
            result=runtime.review({'run_id':r['id'],'project':p,'job':'test','prompt':'保持手动位置'})
            self.assertEqual(result['project']['object_edits']['title']['props']['offset_x'],18)
            self.assertTrue(result['review']['visual']);rendering.assert_not_called()

if __name__=='__main__':unittest.main(verbosity=2)
