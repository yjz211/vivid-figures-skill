"""Archived render links remain usable without exposing adjacent archive files."""
from pathlib import Path
import json, sys, tempfile, threading, unittest, urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'editor_backend'))
import server

class ArchivedJobs(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name); web = base/'workbench'; web.mkdir()
        self.live = web/'workspace/jobs'; self.live.mkdir(parents=True)
        self.archive = base/'归档/snapshot/jobs'; self.archive.mkdir(parents=True)
        registry = web/'workspace/archive-jobs.json'
        registry.write_text(json.dumps({'roots':['../归档/snapshot/jobs']}), encoding='utf8')
        self.job = 'a'*32
        folder = self.archive/self.job; folder.mkdir()
        (folder/'status.json').write_text('{"state":"done"}', encoding='utf8')
        (folder/'figure.png').write_bytes(b'archived image')
        (self.archive/'private.txt').write_text('not a job file', encoding='utf8')
        self.patches = [patch.object(server,'WEB',web), patch.object(server,'JOBS',self.live), patch.object(server,'ARCHIVE_REGISTRY',registry)]
        for item in self.patches: item.start()
        self.http = server.LocalHTTPServer(('127.0.0.1',0), server.Handler)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True); self.thread.start()
        self.url = 'http://127.0.0.1:'+str(self.http.server_port)
        self.client = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def tearDown(self):
        self.http.shutdown(); self.http.server_close(); self.thread.join()
        for item in reversed(self.patches): item.stop()
        self.temp.cleanup()

    def get(self, path, method='GET'):
        return self.client.open(urllib.request.Request(self.url+path, method=method), timeout=3)

    def test_old_status_and_exports(self):
        with self.get('/api/jobs/'+self.job) as response: data=json.load(response)
        self.assertEqual(data['base'], '/workspace/jobs/'+self.job+'/')
        with self.get(data['base']+'figure.png') as response: self.assertEqual(response.read(), b'archived image')
        with self.get(data['base']+'figure.png', 'HEAD') as response: self.assertEqual(response.status, 200)

    def test_current_job_takes_priority(self):
        folder=self.live/self.job; folder.mkdir(); (folder/'figure.png').write_bytes(b'new image')
        with self.get('/workspace/jobs/'+self.job+'/figure.png') as response: self.assertEqual(response.read(), b'new image')

    def test_archive_path_escape_is_unavailable(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.get('/workspace/jobs/'+self.job+'/%2e%2e/private.txt')
        self.assertEqual(error.exception.code, 404)

    def test_unknown_and_invalid_job_ids(self):
        for job, status in [('b'*32,404), ('invalid',400)]:
            with self.assertRaises(urllib.error.HTTPError) as error: self.get('/api/jobs/'+job)
            self.assertEqual(error.exception.code, status)

    def test_registry_cannot_expose_other_folders(self):
        outside=self.archive.parents[2]/'outside'; (outside/self.job).mkdir(parents=True)
        (outside/self.job/'figure.png').write_bytes(b'outside')
        server.ARCHIVE_REGISTRY.write_text(json.dumps({'roots':['../outside']}), encoding='utf8')
        with self.assertRaises(urllib.error.HTTPError) as error: self.get('/workspace/jobs/'+self.job+'/figure.png')
        self.assertEqual(error.exception.code,404)

    def test_second_server_cannot_share_the_port(self):
        with self.assertRaises(OSError):
            server.LocalHTTPServer(self.http.server_address, server.Handler)

if __name__=='__main__': unittest.main()
