"""No-GPU checks for Headroom Bench under Windows PowerShell 5.1 or PS 7."""
import copy
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'tools' / 'bench-app'
CATALOG = APP / 'catalog' / 'sessiond-3070ti.json'
PS = (shutil.which(os.environ['HEADROOM_TEST_PS']) if os.environ.get('HEADROOM_TEST_PS')
      else (shutil.which('powershell.exe') or shutil.which('pwsh')))


@unittest.skipUnless(PS, 'PowerShell is unavailable')
class BenchAppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)
        self.catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
        self.mock = {
            'telemetry': [290, 290, 320, '610.88'],
            'quietUtil': 0, 'profileHash': '1B08C2D0854460FF0123',
            'witnesses': {
                '1': {'core': 1763, 'memory': 9501},
                '2': {'core': 1395, 'memory': 9501},
                '3': {'core': 1500, 'memory': 9501},
            },
            'voltage': 0.850,
        }

    def write(self, name, value):
        path = self.dir / name
        path.write_text(json.dumps(value), encoding='utf-8')
        return path

    def ps(self, script, *args):
        cmd = [PS, '-NoProfile']
        if os.name == 'nt':
            cmd += ['-ExecutionPolicy', 'Bypass']
        cmd += ['-File', str(APP / script), *map(str, args)]
        return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=40)

    def ps_command(self, command):
        cmd = [PS, '-NoProfile']
        if os.name == 'nt':
            cmd += ['-ExecutionPolicy', 'Bypass']
        return subprocess.run(cmd + ['-Command', command], cwd=ROOT,
                              capture_output=True, text=True, timeout=40)

    def display(self, expression, plan=None, record=None):
        helper = str(APP / 'Bench-Display.ps1').replace("'", "''")
        prefix = f". '{helper}'; "
        if plan is not None:
            path = str(self.write('display-plan.json', plan)).replace("'", "''")
            prefix += f"$plan=Get-Content '{path}' -Raw | ConvertFrom-Json; "
        if record is not None:
            path = str(self.write('display-record.json', record)).replace("'", "''")
            prefix += f"$record=Get-Content '{path}' -Raw | ConvertFrom-Json; "
        proc = self.ps_command(prefix + expression + ' | ConvertTo-Json -Depth 12 -Compress')
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        return json.loads(proc.stdout)

    def engine(self, plan=None, session=None, resume=False):
        plan = plan or self.catalog
        session = session or self.dir / 'session.json'
        plan_path = self.write('plan.json', plan)
        mock_path = self.write('mock.json', self.mock)
        args = ['-PlanPath', plan_path, '-SessionPath', session,
                '-MockPath', mock_path, '-DryRun']
        if resume:
            args.append('-Resume')
        proc = self.ps('Run-Plan.ps1', *args)
        record = json.loads(session.read_text(encoding='utf-8')) if session.exists() else None
        return proc, record

    def validate(self, plan):
        path = self.write('invalid.json', plan)
        return self.ps('Test-Plan.ps1', '-PlanPath', path)

    def test_full_passing_preselected_catalog(self):
        proc, record = self.engine()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(record['status'], 'PASS')
        self.assertEqual(len(record['steps']), 63)
        self.assertEqual(record['selectedRuns'], [r['id'] for r in self.catalog['runs']])
        self.assertEqual(record['revert']['coreMhz'], 1763)
        self.assertTrue(record['afterRevertHumanCompleted'])
        self.assertTrue(record['finalState']['logging']['stoppedVerified'])
        self.assertTrue(record['finalState']['clocks']['verified'])
        self.assertEqual(record['finalState']['clocks']['readbackSmClockMhz'], 1763)
        self.assertTrue(record['finalState']['processes']['verified'])

    def test_sensors_step_passes_itself_when_sensors_window_detected(self):
        # Suggested by Raymond 2026-09-23: with HWiNFO's Sensors window up, run start to finish
        # untouched. Default (not detected) records the operator; detected records auto.
        proc, record = self.engine()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        sensors = [s for s in record['steps'] if s['key'] == 'preflight/sensors'][0]
        self.assertEqual(sensors['witness'], {'acknowledged': True, 'confirmedBy': 'operator'})
        self.mock['sensorsReady'] = True
        proc, record = self.engine(session=self.dir / 'auto.json')
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        sensors = [s for s in record['steps'] if s['key'] == 'preflight/sensors'][0]
        self.assertEqual(sensors['witness'], {'acknowledged': True, 'confirmedBy': 'auto'})
        # Wait-Human now returns a value; no other step may pick it up as stray output.
        for step in record['steps']:
            self.assertNotIn('operator', json.dumps(step['witness']) if step['key'] != 'preflight/sensors' else '')

    def test_section8_runs_follow_the_registered_bracket(self):
        # REGISTERED-PREDICTIONS section 8 (2026-09-23): the extras must run only after stock-4
        # closes 4a/4b, so they cannot change how the registered suites are scored.
        ids = [r['id'] for r in self.catalog['runs']]
        extras = ['finefloor-pair', 'edit1-finefloor', 'edit1-5', 'stock-6']
        self.assertEqual(ids[:5], ['preflight', 'stock-1', 'edit1-2', 'edit2-3', 'stock-4'])
        self.assertEqual([i for i in ids if i in extras], extras)
        self.assertTrue(all(ids.index(e) > ids.index('stock-4') for e in extras))
        self.assertEqual(ids[-1], 'cleanup')
        runs = {r['id']: r for r in self.catalog['runs']}
        self.assertEqual(runs['finefloor-pair']['requires'], ['stock-4'])
        gate = [s for s in runs['stock-6']['steps'] if s['type'] == 'gate-drift'][0]
        self.assertEqual((gate['firstRun'], gate['lastRun']), ('stock-4', 'stock-6'))
        labels = [s.get('label') for r in self.catalog['runs'] for s in r['steps'] if s.get('label')]
        self.assertEqual(len(labels), len(set(labels)))

    def test_edited_preselected_run_is_flagged_and_recorded(self):
        queue = copy.deepcopy(self.catalog['runs'])
        queue[1]['steps'][3]['settings'] += ' operator edit'
        queue_path = self.write('queue.json', {'runs': queue})
        plan_path = self.dir / 'edited-plan.json'
        made = self.ps('New-Plan.ps1', '-CatalogPath', CATALOG,
                       '-QueuePath', queue_path, '-OutputPath', plan_path)
        self.assertEqual(made.returncode, 0, made.stdout + made.stderr)
        plan = json.loads(plan_path.read_text(encoding='utf-8'))
        self.assertEqual(plan['customizations'][0]['kind'], 'edited')
        self.assertEqual(plan['customizations'][0]['run'], 'stock-1')
        proc, record = self.engine(plan)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(record['customizations'][0]['actual']['steps'][3]['settings'],
                         queue[1]['steps'][3]['settings'])

    def test_unselected_cleanup_does_not_request_uninstall(self):
        queue = {'runs': self.catalog['runs'][:-1]}
        queue_path = self.write('queue.json', queue)
        plan_path = self.dir / 'subset-plan.json'
        made = self.ps('New-Plan.ps1', '-CatalogPath', CATALOG,
                       '-QueuePath', queue_path, '-OutputPath', plan_path)
        self.assertEqual(made.returncode, 0, made.stdout + made.stderr)
        plan = json.loads(plan_path.read_text(encoding='utf-8'))
        self.assertIsNone(plan['afterRevertHuman'])
        self.assertEqual(plan['customizations'][0]['kind'], 'selection-or-order')

    def test_failed_gate_stops_and_reverts(self):
        self.mock['telemetry'][0] = 310
        proc, record = self.engine()
        self.assertNotEqual(proc.returncode, 0)
        # Preflight checks the store, applies stock, then gates power, so a tuned
        # profile left live is replaced before the gate rather than failing it.
        self.assertEqual([s['type'] for s in record['steps']],
                         ['gate-hash', 'apply-profile', 'gate-power'])
        self.assertEqual(record['steps'][2]['verdict'], 'FAIL')
        self.assertEqual(record['revert']['coreMhz'], 1763)
        self.assertTrue(record['finalState']['logging']['stoppedVerified'])

    def test_final_check_stops_mocked_running_hwinfo_log(self):
        self.mock['finalLoggingStillRunning'] = True
        proc, record = self.engine()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(record['status'], 'PASS')
        self.assertEqual(record['finalState']['logging']['status'], 'stopped')
        self.assertTrue(record['finalState']['logging']['stopAttempted'])
        self.assertTrue(record['finalState']['logging']['stoppedVerified'])

    def test_final_check_fails_if_mocked_log_cannot_stop(self):
        self.mock['finalLoggingStillRunning'] = True
        self.mock['finalLoggingStopFails'] = True
        proc, record = self.engine()
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(record['status'], 'FAIL')
        self.assertEqual(record['finalState']['logging']['status'], 'running')
        self.assertFalse(record['finalState']['logging']['stoppedVerified'])

    def test_estimate_fresh_mid_resume_overrun_and_skipped_steps(self):
        plan = {'runs': [
            {'id': 'a', 'minutes': 2, 'steps': [{'id': 'one', 'estimatedMinutes': 2}]},
            {'id': 'b', 'minutes': 7, 'steps': [
                {'id': 'one', 'estimatedMinutes': 3}, {'id': 'two', 'estimatedMinutes': 4}]},
        ]}
        now = '2026-09-23T19:00:00'
        old = '2026-09-23T18:00:00'
        passed_a = {'key': 'a/one', 'verdict': 'PASS', 'start': '2026-09-23T18:40:00'}
        passed_b = {'key': 'b/one', 'verdict': 'PASS', 'start': '2026-09-23T18:45:00'}
        running = {'key': 'b/one', 'verdict': 'RUNNING', 'start': '2026-09-23T18:59:00'}
        cases = [
            ({'start': now, 'attemptStart': now, 'resumeRunId': '', 'steps': []}, 9, False),
            ({'start': '2026-09-23T18:40:00', 'attemptStart': '2026-09-23T18:40:00', 'resumeRunId': '',
              'steps': [passed_a, running]}, 6, False),
            ({'start': old, 'attemptStart': '2026-09-23T18:59:00', 'resumeRunId': 'b',
              'steps': [passed_a, passed_b,
                        {'key': 'b/one', 'verdict': 'RUNNING', 'start': '2026-09-23T18:30:00'},
                        running]}, 6, False),
            ({'start': old, 'attemptStart': '2026-09-23T18:45:00', 'resumeRunId': 'b',
              'steps': [passed_a, {**running, 'start': '2026-09-23T18:50:00'}]}, 4, True),
            ({'start': now, 'attemptStart': now, 'resumeRunId': '',
              'steps': [passed_a, passed_b]}, 4, False),
        ]
        for record, expected, overrun in cases:
            with self.subTest(record=record):
                value = self.display(f"Get-BenchEstimate $plan $record ([datetime]'{now}')",
                                     plan=plan, record=record)
                self.assertAlmostEqual(value['remainingMinutes'], expected)
                self.assertEqual(value['stepOverrun'], overrun)
                self.assertEqual(value['stepFinish'] is None, overrun or not any(
                    step['verdict'] == 'RUNNING' for step in record['steps']))

    def test_reading_formatter_labels_units_and_missing_fields(self):
        full = self.display("Format-BenchReadings '2572, 13801, 176.86, 62, 99' '0.720' $true")
        self.assertEqual(full, 'Core 2572 MHz   Memory 13801 MHz   Power 176.9 W   Temp 62 C   Util 99%   Voltage 0.720 V')
        missing = self.display("Format-BenchReadings '2572,,bad,62' '0.720' $false")
        self.assertEqual(missing, 'Core 2572 MHz   Memory -- MHz   Power -- W   Temp 62 C   Util --%')
        self.assertNotIn('Voltage', missing)

    def test_status_caption_value_and_color_for_each_state(self):
        names = ['Ready', 'Running', 'Pause requested', 'Paused', 'Stop requested',
                 'Stopping and reverting', 'PASS', 'FAIL']
        expression = "@('Ready','Running','Pause requested','Paused','Stop requested','Stopping and reverting','PASS','FAIL') | ForEach-Object { Get-BenchStatus $_ }"
        values = self.display(expression)
        self.assertEqual([item['value'] for item in values], names)
        self.assertTrue(all(item['caption'] == 'Status:' for item in values))
        self.assertEqual(values[-2]['color'], 'Green')
        self.assertEqual(values[-1]['color'], 'Red')

    def test_stock_drift_gate_fails_and_reverts(self):
        self.mock['driftPct'] = 1.6
        proc, record = self.engine()
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('stock-4/stock-return', [s['key'] for s in record['steps'] if s['verdict'] == 'FAIL'])
        self.assertEqual(record['revert']['coreMhz'], 1763)

    def test_stock_clocks_after_applied_profile_fail_witness(self):
        self.mock['witnesses']['3']['core'] = 1763
        proc, record = self.engine()
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn('edit2-3/witness', [s['key'] for s in record['steps'] if s['verdict'] == 'FAIL'])
        failed = [s for s in record['steps'] if s['key'] == 'edit2-3/witness'][0]
        self.assertEqual(failed['witness']['coreMhz'], 1763)
        self.assertEqual(record['revert']['coreMhz'], 1763)

    def test_hwinfo_fallback_records_manual_path(self):
        self.mock['hwinfoStartFail'] = True
        proc, record = self.engine()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        starts = [s for s in record['steps'] if s['type'] == 'hwinfo-start']
        self.assertTrue(starts)
        self.assertTrue(all(s['witness']['mode'] == 'manual' for s in starts))
        self.assertIn('hwinfo-rtx3070ti-sessiond-stock-1', starts[0]['witness']['path'])

    def test_resume_after_interrupted_suite_keeps_old_attempt(self):
        self.mock['failSuite'] = True
        first, old = self.engine()
        self.assertNotEqual(first.returncode, 0)
        self.assertEqual(old['status'], 'FAIL')
        self.mock['failSuite'] = False
        second, record = self.engine(resume=True)
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertEqual(record['status'], 'PASS')
        self.assertTrue(any(s['verdict'] == 'FAIL' for s in record['steps']))
        paths = [s['witness']['path'] for s in record['steps']
                 if s['type'] == 'hwinfo-start' and s['verdict'] == 'PASS']
        self.assertTrue(any('-resume-' in p for p in paths))
        self.assertEqual(len(paths), len(set(paths)))

    def test_refuses_session_overwrite(self):
        first, _ = self.engine()
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        second, record = self.engine()
        self.assertNotEqual(second.returncode, 0)
        self.assertIn('Refusing to overwrite session', second.stdout)
        self.assertEqual(record['status'], 'PASS')

    def test_validator_rejects_malformed_plans(self):
        mutations = []
        def altered(change):
            p = copy.deepcopy(self.catalog)
            change(p)
            mutations.append(p)
        altered(lambda p: p['runs'][0]['steps'][0].update(type='unknown'))
        altered(lambda p: p.pop('volumeLabel'))
        altered(lambda p: p['revert']['witness'].pop('memoryMax'))
        altered(lambda p: p['runs'][0]['steps'][2].pop('limit'))
        altered(lambda p: p['runs'][0]['steps'][0].update(path='Profiles/VEN.cfg'))
        altered(lambda p: p['runs'][1]['steps'].pop(2))  # suite with no start
        altered(lambda p: p['runs'][2]['steps'][1].update(path=p['runs'][1]['steps'][2]['path']))
        altered(lambda p: p['runs'][5]['steps'][1].update(minMhz=50))
        altered(lambda p: p['runs'][5]['steps'][1].update(maxMhz=3000))
        altered(lambda p: p['runs'][5]['steps'][1].update(iterations=[120, 200]))
        altered(lambda p: p['runs'][5]['steps'][1].update(workload='gemm;calc'))
        altered(lambda p: p['runs'][2]['steps'][0].update(type='hwinfo-start', path='relative.csv'))
        altered(lambda p: p['runs'][0]['steps'][3].update(maxUtil=0))
        altered(lambda p: p['runs'][1]['steps'][0].update(slot=0))
        altered(lambda p: p['runs'][1]['steps'][1].pop('memoryMax'))
        altered(lambda p: p['runs'][1]['steps'][1].update(coreMax=3000))
        altered(lambda p: p['runs'][1]['steps'].pop(1))  # applied profile without a witness
        altered(lambda p: p['runs'][1]['steps'][2].update(path='relative.csv'))
        altered(lambda p: p['runs'][1]['steps'][2].update(path='C:/Temp/hwinfo.csv'))
        altered(lambda p: p['runs'][1]['steps'][4].update(type='hwinfo-start', path='kit:/results/extra.csv'))
        altered(lambda p: p['runs'][1]['steps'][3].pop('settings'))
        altered(lambda p: p['runs'][5]['steps'][1].pop('output'))
        altered(lambda p: p['runs'][5]['steps'][1].update(output='C:/Temp/sweep'))
        altered(lambda p: p['runs'][0]['steps'][5].update(instruction=''))
        altered(lambda p: p['runs'][1]['steps'].insert(3, {'id':'bad-profile','type':'apply-profile','name':'Bad','slot':1}))
        altered(lambda p: p['runs'].insert(2, p['runs'].pop(5)))
        altered(lambda p: p['runs'].insert(1, p['runs'].pop(-1)))
        altered(lambda p: p['runs'].pop(0))
        for i, plan in enumerate(mutations):
            with self.subTest(mutation=i):
                proc = self.validate(plan)
                self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_all_scripts_parse_and_are_ascii(self):
        scripts = sorted(APP.glob('*.ps1'))
        for script in scripts:
            with self.subTest(script=script.name):
                self.assertTrue(script.read_bytes().isascii())
                quoted = str(script).replace("'", "''")
                command = f"$e=$null; [void][System.Management.Automation.Language.Parser]::ParseFile('{quoted}',[ref]$null,[ref]$e); if($e.Count){{exit 1}}"
                proc = subprocess.run([PS, '-NoProfile', '-Command', command], capture_output=True, text=True, timeout=10)
                self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_hwinfo_voltage_reader_handles_duplicate_headers_and_footer(self):
        source = ROOT / 'data' / 'frequency-sweeps' / 'rtx3070ti-20260825' / 'hwinfo-oc' / 'hwinfo-oc-membw-matched2130.csv'
        if not source.exists():
            self.skipTest('HWiNFO fixture is unavailable')
        with source.open(encoding='cp1252', newline='') as f:
            rows = list(csv.reader(f))
        column = [i for i, name in enumerate(rows[0]) if name.startswith('GPU Core Voltage')]
        self.assertEqual(len(column), 1)
        actual_rows = [r for r in rows[1:] if len(r) == len(rows[0]) and r[0] != 'Date' and r[0]]
        expected = float(actual_rows[-1][column[0]])
        helper = str(APP / 'Hwinfo-Csv.ps1').replace("'", "''")
        data = str(source).replace("'", "''")
        command = f". '{helper}'; Get-HwinfoCoreVoltage '{data}'"
        args = [PS, '-NoProfile']
        if os.name == 'nt':
            args += ['-ExecutionPolicy', 'Bypass']
        proc = subprocess.run(args + ['-Command', command], capture_output=True, text=True, timeout=20)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertAlmostEqual(float(proc.stdout.strip()), expected)

    def read_voltage(self, header, rows):
        path = self.dir / 'igpu.csv'
        with path.open('w', encoding='cp1252', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
        helper = str(APP / 'Hwinfo-Csv.ps1').replace("'", "''")
        data = str(path).replace("'", "''")
        args = [PS, '-NoProfile']
        if os.name == 'nt':
            args += ['-ExecutionPolicy', 'Bypass']
        return subprocess.run(args + ['-Command', f". '{helper}'; Get-HwinfoCoreVoltage '{data}'"],
                              capture_output=True, text=True, timeout=20)

    def test_hwinfo_voltage_reader_ignores_integrated_gpu_column(self):
        # The first live run, 2026-09-23, on a Ryzen 9700X: its Radeon iGPU adds
        # "GPU Core Voltage (VDDCR_GFX) [V]" beside the NVIDIA "GPU Core Voltage [V]". The reader
        # demanded exactly one prefix match and failed every sample. Worse, the iGPU read 0.725 V,
        # inside the 5060 Ti witness window, so picking it would have passed on the wrong GPU.
        header = ['Date', 'Time', 'GPU Core Voltage (VDDCR_GFX) [V]', 'GPU Clock [MHz]',
                  'GPU Core Voltage [V]', 'GPU Clock [MHz]']
        rows = [['23.9.2026', '18:51:0%d' % i, '0.725', '600.0', '0.720', '1537.0'] for i in range(5)]
        proc = self.read_voltage(header, rows)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertAlmostEqual(float(proc.stdout.strip()), 0.720)

    def test_hwinfo_voltage_reader_picks_the_loaded_gpu_among_same_named_columns(self):
        header = ['Date', 'Time', 'GPU Core Voltage [V]', 'GPU Clock [MHz]',
                  'GPU Core Voltage [V]', 'GPU Clock [MHz]']
        rows = [['23.9.2026', '18:51:0%d' % i, '0.900', '350.0', '0.720', '1537.0'] for i in range(5)]
        proc = self.read_voltage(header, rows)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertAlmostEqual(float(proc.stdout.strip()), 0.720)

    def test_hwinfo_manual_fallback_requires_file_growth(self):
        path = self.dir / 'log.csv'
        path.write_text('Date,Voltage\n', encoding='ascii')
        helper = str(APP / 'Hwinfo-Csv.ps1').replace("'", "''")
        data = str(path).replace("'", "''")
        command = f". '{helper}'; Assert-HwinfoLogGrowth '{data}' -FirstDelayMs 150 -SecondDelayMs 150"
        args = [PS, '-NoProfile']
        if os.name == 'nt':
            args += ['-ExecutionPolicy', 'Bypass']
        frozen = subprocess.run(args + ['-Command', command], capture_output=True, text=True, timeout=10)
        self.assertNotEqual(frozen.returncode, 0)
        self.assertIn('not growing', frozen.stderr + frozen.stdout)
        # A real HWiNFO log grows continuously. A single append at a fixed delay raced PowerShell 7's
        # slower start on Linux CI (the append landed before the first size read), so append
        # every 100 ms for as long as the check runs.
        done = threading.Event()
        def append():
            while not done.is_set():
                with path.open('a', encoding='ascii') as f:
                    f.write('2026-09-23,0.85\n')
                time.sleep(0.1)
        thread = threading.Thread(target=append)
        thread.start()
        try:
            growing_command = f". '{helper}'; Assert-HwinfoLogGrowth '{data}' -FirstDelayMs 200 -SecondDelayMs 1200"
            growing = subprocess.run(args + ['-Command', growing_command], capture_output=True, text=True, timeout=10)
        finally:
            done.set()
            thread.join()
        self.assertEqual(growing.returncode, 0, growing.stdout + growing.stderr)

    def test_stock_drift_uses_median_absolute_matched_target_change(self):
        first = self.dir / 'first'
        last = self.dir / 'last'
        first.mkdir(); last.mkdir()
        names = ['target_frequency_mhz', 'achieved_frequency_avg', 'bench_throughput']
        for directory, factor in [(first, lambda i: 1.0),
                                  (last, lambda i: 1.01 if i < 6 else 1.016)]:
            with (directory / 'run-gemm_sweep.csv').open('w', newline='', encoding='ascii') as file:
                writer = csv.DictWriter(file, fieldnames=names)
                writer.writeheader()
                for i in range(13):
                    target = 855 + i * 105
                    writer.writerow({'target_frequency_mhz': target,
                                     'achieved_frequency_avg': target + (3 if directory == first else -3),
                                     'bench_throughput': 100 * factor(i)})
        helper = str(APP / 'Stock-Drift.ps1').replace("'", "''")
        a = str(first).replace("'", "''")
        b = str(last).replace("'", "''")
        command = f". '{helper}'; Measure-StockDrift '{a}' '{b}' @('gemm') | ConvertTo-Json -Compress"
        args = [PS, '-NoProfile']
        if os.name == 'nt':
            args += ['-ExecutionPolicy', 'Bypass']
        proc = subprocess.run(args + ['-Command', command], capture_output=True, text=True, timeout=10)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        measured = json.loads(proc.stdout)
        self.assertAlmostEqual(measured['worstMedianAbsPct'], 1.6, places=6)
        self.assertAlmostEqual(measured['perWorkload']['gemm'], 1.6, places=6)

    def test_pmon_gate_sums_processes_and_checks_video_engines(self):
        helper = str(APP / 'Pmon-Gate.ps1').replace("'", "''")
        command = (f". '{helper}'; "
                   "$rows=@('0 101 C 3 0 0 0 - - a','0 202 C 3 0 0 0 - - b',"
                   "'0 101 C 2 0 1 0 - - a','0 202 C 1 0 0 0 - - b'); "
                   "Measure-PmonQuiet $rows | ConvertTo-Json -Compress")
        args = [PS, '-NoProfile']
        if os.name == 'nt':
            args += ['-ExecutionPolicy', 'Bypass']
        proc = subprocess.run(args + ['-Command', command], capture_output=True, text=True, timeout=10)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        measured = json.loads(proc.stdout)
        self.assertEqual(measured['maxSm'], 6)
        self.assertEqual(measured['maxEncoder'], 1)
        self.assertEqual(measured['maxDecoder'], 0)
        self.assertEqual(measured['samples'], 2)

    def test_sync_kit_lists_every_runtime_file(self):
        kit = self.dir / 'headroom-kit'
        (kit / 'python').mkdir(parents=True)
        (kit / 'python' / 'python.exe').write_bytes(b'fixture')
        cmd = [PS, '-NoProfile']
        if os.name == 'nt':
            cmd += ['-ExecutionPolicy', 'Bypass']
        cmd += ['-File', str(ROOT / 'tools' / 'collection-kit' / 'Sync-Kit.ps1'),
                '-KitPath', str(kit), '-WhatIfOnly']
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=20)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        for file in ['RUN-BENCH.bat', 'Run-Plan.ps1', 'Bench-Window.ps1', 'Bench-Display.ps1',
                     'Run-Child.ps1', 'Test-Plan.ps1', 'New-Plan.ps1',
                     'Hwinfo-Csv.ps1', 'Stock-Drift.ps1', 'Pmon-Gate.ps1', 'sessiond-3070ti.json',
                     'Invoke-HwinfoLogging.ps1']:
            self.assertIn(file, proc.stdout)

    @unittest.skipUnless(os.name == 'nt', 'WinForms needs Windows desktop')
    def test_window_opens_in_dry_run(self):
        mock = self.write('mock.json', self.mock)
        proc = self.ps('Bench-Window.ps1', '-DryRun', '-MockPath', mock, '-AutoCloseSeconds', '1')
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        # 6 of 7 since 2026-09-23: C8 runs the evening before in shakedown-3070ti.json, so the
        # Session D catalog no longer preselects it.
        self.assertIn('CATALOG LOADED: 11 runs, 10 preselected.', proc.stdout)


if __name__ == '__main__':
    class ReportingResult(unittest.TextTestResult):
        def addSuccess(self, test):
            super().addSuccess(test)
            print('[PASS] ' + test.id())

        def addSkip(self, test, reason):
            super().addSkip(test, reason)
            print('[SKIP] ' + test.id() + ': ' + reason)

    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    outcome = unittest.TextTestRunner(resultclass=ReportingResult).run(suite)
    raise SystemExit(0 if outcome.wasSuccessful() else 1)
