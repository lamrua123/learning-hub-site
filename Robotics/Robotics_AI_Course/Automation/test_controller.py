"""Kiểm thử guard/transition và lỗi process, không gọi model hay sửa vault thật."""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import controller as c

SOURCE = Path(__file__).resolve().parents[1]

def usage(five=80,weekly=70):
    return dict(mode='AVAILABLE',five_hour_remaining=five,weekly_remaining=weekly,
                five_hour_resets_at=None,weekly_resets_at=None,reached=False,
                source='TEST_FIXTURE',checked_at=c.utcnow(),reason=None)

def review():
    return dict(repair_attempts=0,test_level='SYNTHETIC_TEST_FIXTURE_ONLY',
                checks={k:dict(passed=True,evidence='Synthetic test fixture; not a real technical review.') for k in c.SEMANTIC},
                gate='PASS',pending_repairs=[])

class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='robotics-controller-test-')
        self.root = Path(self.temp.name)/'course'
        self.root.mkdir()
        for relative in ('Reference/ROADMAP_INDEX.json','01_COURSE_ROADMAP.md','02_COURSE_STATE.md','00_HOME.md'):
            destination = self.root/relative
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(SOURCE/relative,destination)
        (self.root/'Automation/Logs').mkdir(parents=True,exist_ok=True)
        (self.root/'Automation/Receipts').mkdir(parents=True,exist_ok=True)
        self.index = c.read_index(self.root)
        self.state = c.read_state(self.root)
        lesson = self.index['lessons'][0]['path']
        (self.root/lesson).parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(SOURCE/lesson,self.root/lesson)
        # Fixture luôn bắt đầu ở Bài 001, độc lập tiến độ vault khi chạy SelfTest về sau.
        self.state.update(course_status='IN_PROGRESS',automation_state='PAUSED',completed_lessons=1,
                          last_checkpoint_lesson=0,last_checkpoint_number=0,last_checkpoint=None,
                          major_checkpoints_completed=[],pending_repairs=[],completed_projects=[],
                          pause_reason='INITIALIZATION_COMPLETE',usage=usage(),
                          last_unit=dict(id='fixture-001',kind='lesson',target=1,path=lesson,
                                         receipt='Automation/Receipts/fixture-001.json'))
        self.state['usage_unavailable_since_checkpoint'] = False
        c.atomic_text(self.root/'Automation/Receipts/fixture-001.json',
                      c.json_text(dict(id='fixture-001',sha256=c.digest(self.root/lesson),review=review())))
        c.write_state(self.root,self.state,self.index)
        self.base_lesson = (self.root/self.index['lessons'][0]['path']).read_text(encoding='utf-8')

    def tearDown(self):
        self.temp.cleanup()

    def args(self,**kwargs):
        value = dict(dry_run=False,validate_only=False,resume=True,max_units=20,codex=None,timeout=60)
        value.update(kwargs)
        return SimpleNamespace(**value)

    def fake_author(self,root,command,features,active,timeout):
        path = root/active['path']
        path.parent.mkdir(parents=True,exist_ok=True)
        if active['kind']=='lesson':
            row = self.index['lessons'][active['target']-1]
            text = self.base_lesson.replace('# Bài 001 - Điện là gì và mạch kín đầu tiên',f"# Bài {row['number']:03d} - {row['title']}",1)
        elif active['kind'] in ('checkpoint','major_checkpoint'):
            text = (f"# Checkpoint {active['target']:03d} - Review Bài {active['start']:03d} đến {active['end']:03d}\n"
                    if active['kind']=='checkpoint' else f"# Major Checkpoint {active['target']:02d} - Part {active['target']:02d}\n")
            for h in ('Phạm vi và bằng chứng','Đánh giá 16 tiêu chí','Lỗi và sửa đổi','Quyết định gate','Cập nhật state','Major checkpoint bổ sung'):
                text += f'\n## {h}\nSynthetic isolated fixture. PASS\n'
                if h=='Đánh giá 16 tiêu chí':
                    text += '\n'.join(f'| {n} | Synthetic | PASS | Isolated test evidence |' for n in range(1,17))+'\n'
        else:
            text = path.read_text(encoding='utf-8')+'\nSynthetic repair.\n'
        path.write_text(text,encoding='utf-8')
        rp = root/'Automation/test-review.json'
        rp.write_text(c.json_text(review()),encoding='utf-8')
        c.prepare_commit(root,rp)

    def run_mock(self,u=None,author=None,args=None):
        with patch.object(c,'resolve_codex',return_value=['mock']),patch.object(c,'detect_features',return_value={'version':'mock'}),patch.object(c,'probe_usage',return_value=u or usage()),patch.object(c,'execute_unit',side_effect=author or self.fake_author) as dispatch:
            c.run_controller(self.root,args or self.args())
            return dispatch.call_count

    def test_real_course_structural(self):
        self.assertEqual(c.validate_course(self.root,self.state,self.index),[])
        self.assertEqual(len(self.index['lessons']),160)
        self.assertEqual(len(self.index['modules']),24)

    def test_paused_without_resume_does_not_dispatch(self):
        with patch.object(c,'resolve_codex') as command:
            c.run_controller(self.root,self.args(resume=False))
            command.assert_not_called()

    def test_dry_run_is_read_only(self):
        before = c.digest(self.root/'02_COURSE_STATE.md')
        c.run_controller(self.root,self.args(dry_run=True))
        self.assertEqual(before,c.digest(self.root/'02_COURSE_STATE.md'))

    def test_ten_percent_each_window_stops(self):
        for u in (usage(10,80),usage(80,10),usage(0,0)):
            with self.subTest(u=u):
                self.assertEqual(self.run_mock(u),0)
                s = c.read_state(self.root)
                self.assertEqual(s['pause_reason'],'USAGE_GUARD')
                self.assertEqual(s['completed_lessons'],1)

    def test_incomplete_usage_with_low_known_window_stops(self):
        u = c.unavailable('TEST')
        u['five_hour_remaining'] = 10
        self.assertEqual(self.run_mock(u),0)

    def test_normalize_prefers_map_and_checks_duration(self):
        r = {'rateLimits':{'primary':{'usedPercent':1,'windowDurationMins':300}},
             'rateLimitsByLimitId':{'codex':{'primary':{'usedPercent':31,'windowDurationMins':10080},
                                            'secondary':{'usedPercent':42,'windowDurationMins':300}}}}
        u = c.normalize_usage(r)
        self.assertEqual((u['five_hour_remaining'],u['weekly_remaining']),(58,69))
        self.assertEqual(u['mode'],'AVAILABLE')
        r['rateLimitsByLimitId'] = {}
        self.assertEqual(c.normalize_usage(r)['mode'],'UNAVAILABLE')

    def test_missing_null_nan_and_expired_are_unavailable(self):
        for used,reset in [(None,None),(float('nan'),None),(False,None),(1,time.time()-10)]:
            bucket = {'primary':{'usedPercent':used,'windowDurationMins':300,'resetsAt':reset},'secondary':None}
            self.assertEqual(c.normalize_usage({'rateLimits':bucket})['mode'],'UNAVAILABLE')

    def test_guard_reached_without_percentages(self):
        u = c.normalize_usage({'rateLimits':{'rateLimitReachedType':'weekly'}})
        self.assertTrue(c.usage_low(u))

    def test_next_checkpoint_then_major(self):
        s = copy.deepcopy(self.state)
        s.update(completed_lessons=10,last_checkpoint_lesson=5,last_checkpoint_number=1)
        self.assertEqual(c.next_unit(s,self.index)['kind'],'checkpoint')
        s.update(last_checkpoint_lesson=10,last_checkpoint_number=2)
        self.assertEqual(c.next_unit(s,self.index),dict(kind='major_checkpoint',target=1,path='Checkpoints/Major Checkpoint 01 - Part 01.md'))
        s['major_checkpoints_completed'] = [1]
        self.assertEqual(c.next_unit(s,self.index)['target'],11)

    def test_repairs_take_priority(self):
        s = copy.deepcopy(self.state)
        s['pending_repairs'] = [dict(id='fix-1',path=self.index['lessons'][0]['path'],reason='Unsafe example',required_changes='Fix')]
        self.assertEqual(c.next_unit(s,self.index)['kind'],'repair')

    def test_unavailable_four_lessons_then_checkpoint_and_pause(self):
        calls = self.run_mock(c.unavailable('TEST_UNAVAILABLE'))
        s = c.read_state(self.root)
        self.assertEqual(calls,5)  # Từ Bài 001: 002,003,004,005,checkpoint.
        self.assertEqual(s['completed_lessons'],5)
        self.assertEqual(s['last_checkpoint_lesson'],5)
        self.assertEqual(s['pause_reason'],'USAGE_DATA_UNAVAILABLE_SAFE_PAUSE')
        self.assertFalse(s['checkpoint_pending'])

    def test_max_units_resume_does_not_reset_checkpoint_counter(self):
        for _ in range(4):
            self.assertEqual(self.run_mock(c.unavailable('TEST'),args=self.args(max_units=1)),1)
        s = c.read_state(self.root)
        self.assertEqual((s['completed_lessons'],s['checkpoint_pending']),(5,True))
        self.assertEqual(self.run_mock(usage(10,60)),0)
        self.assertTrue(c.read_state(self.root)['checkpoint_pending'])
        self.assertEqual(self.run_mock(c.unavailable('TEST'),args=self.args(max_units=1)),1)
        self.assertEqual(c.read_state(self.root)['last_unit']['kind'],'checkpoint')

    def test_codex_no_state_update_blocks_without_retry(self):
        with self.assertRaises(ValueError):
            self.run_mock(author=lambda *a: None)
        s = c.read_state(self.root)
        self.assertEqual(s['course_status'],'BLOCKED')
        self.assertEqual(s['completed_lessons'],1)
        self.assertTrue((self.root/'Automation/ACTIVE_UNIT.json').exists())

    def test_rate_limit_stops_without_retry(self):
        calls=[]
        def fail(*args):
            calls.append(1)
            raise RuntimeError('RATE_LIMIT_ERROR')
        with self.assertRaises(RuntimeError):
            self.run_mock(author=fail)
        self.assertEqual(len(calls),1)
        self.assertEqual(c.read_state(self.root)['pause_reason'],'RATE_LIMIT_ERROR')

    def test_more_than_one_lesson_is_rejected(self):
        def bad(root,command,features,active,timeout):
            row = self.index['lessons'][active['target']]
            p = root/row['path']
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text('Unexpected extra lesson',encoding='utf-8')
            self.fake_author(root,command,features,active,timeout)
        with self.assertRaisesRegex(ValueError,'ngoài phạm vi'):
            self.run_mock(author=bad)
        self.assertEqual(c.read_state(self.root)['completed_lessons'],1)

    def test_hash_tamper_is_rejected(self):
        path = self.root/self.state['last_unit']['path']
        path.write_text(path.read_text(encoding='utf-8')+'\nTamper\n',encoding='utf-8')
        self.assertTrue(any('Receipt/hash' in e for e in c.validate_course(self.root,self.state,self.index)))

    def test_two_repairs_maximum(self):
        r = review()
        r['repair_attempts'] = 3
        self.assertTrue(c.semantic_errors(r))

    def test_current_project_is_authored_not_learner_completion(self):
        s = copy.deepcopy(self.state)
        s.update(completed_lessons=31,last_checkpoint_lesson=30,major_checkpoints_completed=[1,2,3,4])
        c.refresh_derived(s,self.index)
        self.assertEqual(s['current_project'],'PROJECT 01 (bài 031)')
        self.assertEqual(s['completed_projects'],[])

    def test_completed_major_with_repairs_must_be_reviewed_again(self):
        self.assertEqual(self.run_mock(args=self.args(max_units=11)),11)
        # 002..005, checkpoint, 006..010, checkpoint = 11 units.
        s = c.read_state(self.root)
        self.assertEqual(c.next_unit(s,self.index)['kind'],'major_checkpoint')
        active = dict(c.next_unit(s,self.index),id='major-needs-repair',start_revision=s['revision'],
                      lesson_hashes=c.inventory(self.root))
        c.atomic_text(self.root/'Automation/ACTIVE_UNIT.json',c.json_text(active))
        r = review()
        r['gate'] = 'NEEDS_REPAIR'
        r['pending_repairs'] = [dict(id='fix-1',path=self.index['lessons'][0]['path'],reason='Synthetic issue',required_changes='Synthetic fix')]
        original = c.prepare_commit
        def commit_changed(root,path):
            path.write_text(c.json_text(r),encoding='utf-8')
            return original(root,path)
        with patch.object(c,'prepare_commit',side_effect=commit_changed):
            self.fake_author(self.root,[],{},active,60)
        s = c.read_state(self.root)
        self.assertNotIn(1,s['major_checkpoints_completed'])
        self.assertEqual(c.next_unit(s,self.index)['kind'],'repair')
        s['pending_repairs'] = []
        self.assertEqual(c.next_unit(s,self.index)['kind'],'major_checkpoint')

    def test_complete_waits_for_final_checkpoint_and_major(self):
        s = copy.deepcopy(self.state)
        s.update(completed_lessons=160,last_checkpoint_lesson=155,last_checkpoint_number=31,major_checkpoints_completed=list(range(1,24)))
        self.assertEqual(c.next_unit(s,self.index)['kind'],'checkpoint')
        s.update(last_checkpoint_lesson=160,last_checkpoint_number=32)
        self.assertEqual(c.next_unit(s,self.index)['kind'],'major_checkpoint')
        s['major_checkpoints_completed'].append(24)
        c.refresh_derived(s,self.index)
        self.assertEqual(s['course_status'],'COMPLETE')

    def test_lock_prevents_second_controller(self):
        path = self.root/'Automation/controller.lock'
        path.write_text('{"pid": 999999}',encoding='utf-8')
        with patch.object(c,'execute_unit') as dispatch:
            self.assertEqual(c.main(['--root',str(self.root),'--resume']),1)
            dispatch.assert_not_called()
        self.assertTrue(path.exists())

    def test_process_error_event_is_killed_promptly(self):
        fake = self.root/'Automation/fake_cli.py'
        fake.write_text('import sys,json,time\nsys.stdin.read()\nprint(json.dumps({"type":"error","message":"usage limit reached"}),flush=True)\ntime.sleep(30)\n',encoding='utf-8')
        began = time.monotonic()
        with self.assertRaisesRegex(RuntimeError,'RATE_LIMIT_ERROR'):
            c.execute_unit(self.root,[sys.executable,str(fake)],{},dict(id='fake-error'),60)
        self.assertLess(time.monotonic()-began,10)

if __name__ == '__main__':
    unittest.main()
