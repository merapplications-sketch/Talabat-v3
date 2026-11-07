import copy
import json
import tempfile
import unittest
from pathlib import Path
from offline_checks import *


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'db.dump').write_bytes(b'SYNTHETIC_NOT_A_POSTGRES_BACKUP')
        (self.root / 'proof.bin').write_bytes(b'SYNTHETIC_OBJECT_BYTES')
        self.manifest = {'format': 1, 'source_project': PILOT,
            'export_started_utc': '2026-11-07T00:00:00Z', 'export_finished_utc': '2026-11-07T00:00:01Z',
            'storage_inventory': [{'bucket': 'fixture', 'object': 'proof.bin'}],
            'files': [{'path': p, 'kind': kind, 'size': (self.root/p).stat().st_size,
                       'sha256': digest(self.root/p), **extra} for p, kind, extra in [
                           ('db.dump', 'database', {}),
                           ('proof.bin', 'storage', {'bucket':'fixture', 'object':'proof.bin'})]]}
        self.event = {'event_id':'00000000-0000-4000-8000-000000000033',
                      'project':PILOT, 'synthetic':True, 'kind':'authorization_denied', 'count':1}

    def test_bundle_positive_and_no_restore_claim(self):
        result = verify_bundle(self.root, self.manifest)
        self.assertEqual(result['verified_objects'], 1)
        self.assertFalse(result['database_restored'])

    def test_storage_tamper_rejected(self):
        (self.root/'proof.bin').write_bytes(b'TAMPERED_OBJECT_BYTES')
        with self.assertRaises(ValueError): verify_bundle(self.root, self.manifest)

    def test_database_tamper_rejected(self):
        (self.root/'db.dump').write_bytes(b'bad')
        with self.assertRaises(ValueError): verify_bundle(self.root, self.manifest)

    def test_missing_object_rejected(self):
        (self.root/'proof.bin').unlink()
        with self.assertRaises(FileNotFoundError): verify_bundle(self.root, self.manifest)

    def test_missing_inventory_entry_rejected(self):
        self.manifest['files'].pop()
        with self.assertRaises(ValueError): verify_bundle(self.root, self.manifest)

    def test_duplicate_rejected(self):
        self.manifest['files'].append(self.manifest['files'][0])
        with self.assertRaises(ValueError): verify_bundle(self.root, self.manifest)

    def test_traversal_and_absolute_rejected(self):
        for path in ('../db.dump', '/etc/passwd', '..\\db.dump'):
            self.manifest['files'][0]['path'] = path
            with self.assertRaises(ValueError): verify_bundle(self.root, self.manifest)

    def test_symlink_rejected(self):
        (self.root/'link').symlink_to(self.root/'db.dump')
        self.manifest['files'][0]['path'] = 'link'
        with self.assertRaises(ValueError): verify_bundle(self.root, self.manifest)

    def test_protected_targets_refused_even_when_allowlisted(self):
        for project in (PILOT, PRODUCTION, 'unknown'):
            with self.assertRaises(ValueError): restore_target(project, [PILOT, PRODUCTION, 'disposable'])
        self.assertEqual(restore_target('disposable', ['disposable']), 'disposable')

    def test_wrong_source_refused(self):
        self.manifest['source_project'] = PRODUCTION
        with self.assertRaises(ValueError): verify_bundle(self.root, self.manifest)

    def test_alert_arbitrary_secrets_dropped(self):
        self.event.update(message='SECRET_MARKER\nFORGED', token='SECRET_MARKER', url='https://x/?token=SECRET_MARKER', gps='SECRET_MARKER')
        self.assertNotIn('SECRET_MARKER', json.dumps(incident_event(self.event)))
        self.assertEqual(incident_event(self.event)['kind'], 'authorization_denied')

    def test_alert_injection_in_allowed_field_rejected(self):
        self.event['kind'] = 'authorization_denied\nFORGED'
        with self.assertRaises(ValueError): incident_event(self.event)

    def test_alert_requires_synthetic_test_project(self):
        self.event['project'] = PRODUCTION
        with self.assertRaises(ValueError): incident_event(self.event)

    def test_retry_bounded_and_stable_event_id(self):
        failed = delivery_drill(self.event, [503]*10)
        self.assertEqual(failed['attempts'], [503]*3)
        success = delivery_drill(self.event, [503, 204, 503])
        self.assertTrue(success['transport_ack'])
        self.assertFalse(success['human_receipt'])
        self.assertFalse(success['external_delivery'])
        self.assertEqual(success['event']['event_id'], self.event['event_id'])

    def test_alert_no_retry_on_429_or_permanent_error(self):
        for status in (429, 400, 401, 403):
            self.assertEqual(delivery_drill(self.event, [status,204])['attempts'], [status])

    def test_rate_stops_on_lockout_timeout_failure(self):
        for status in (429, None, 503):
            self.assertEqual(rate_drill([200,status,200])['observed'], [200,status])

    def test_rate_success_and_budget(self):
        self.assertEqual(rate_drill([200]*100)['observed'], [200]*8)
        self.assertFalse(rate_drill([200])['provider_tested'])
        for budget in (0, 17, True):
            with self.assertRaises(ValueError): rate_drill([],budget)

    def test_recovery_fixture_cannot_target_real_mail(self):
        with self.assertRaises(ValueError): recovery_case('owner@example.com','customer')
        self.assertFalse(recovery_case('recover@talabot-test.invalid','customer')['send_enabled'])

    def test_customer_admin_recovery_requirements_separate(self):
        self.assertIn('no_new_mfa_requirement', recovery_case('c@talabot-test.invalid','customer')['steps'])
        self.assertIn('mfa_still_required', recovery_case('a@talabot-test.invalid','admin')['steps'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
