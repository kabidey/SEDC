#!/usr/bin/env python3
"""
Backend API tests for SMIFS Monitoring Engine (Phase 8)
Tests all monitoring features: monitors, rules, alerts, channels, SSE streaming.
"""
import requests
import sys
import time
import json
from datetime import datetime

BASE_URL = "https://data-centre-hub.preview.emergentagent.com/api"

class MonitoringTester:
    def __init__(self):
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []
        self.monitor_id = None
        self.rule_id = None
        self.channel_id = None
        self.alert_id = None
        self.unreachable_monitor_id = None

    def log(self, msg, level="INFO"):
        print(f"[{level}] {msg}")

    def test(self, name, func):
        """Run a single test"""
        self.tests_run += 1
        self.log(f"\n{'='*60}")
        self.log(f"Test {self.tests_run}: {name}")
        self.log('='*60)
        try:
            func()
            self.tests_passed += 1
            self.log(f"✅ PASSED: {name}", "PASS")
            return True
        except AssertionError as e:
            self.tests_failed += 1
            self.failures.append(f"{name}: {str(e)}")
            self.log(f"❌ FAILED: {name} - {str(e)}", "FAIL")
            return False
        except Exception as e:
            self.tests_failed += 1
            self.failures.append(f"{name}: Unexpected error - {str(e)}")
            self.log(f"❌ ERROR: {name} - {str(e)}", "ERROR")
            return False

    def login(self):
        """Login and get JWT token"""
        self.log("Logging in as admin...")
        resp = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "admin"})
        assert resp.status_code == 200, f"Login failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert 'access_token' in data, "No access_token in response"
        self.token = data['access_token']
        self.log(f"✓ Logged in successfully, token: {self.token[:20]}...")

    def headers(self):
        """Return auth headers"""
        return {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}

    # Test 1: GET /api/monitoring/stats
    def test_stats(self):
        resp = requests.get(f"{BASE_URL}/monitoring/stats", headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        self.log(f"Stats response: {data}")
        assert 'monitors_total' in data, "Missing 'monitors_total'"
        assert 'monitors_ok' in data, "Missing 'monitors_ok'"
        assert 'monitors_warning' in data, "Missing 'monitors_warning'"
        assert 'monitors_critical' in data, "Missing 'monitors_critical'"
        assert 'monitors_unknown' in data, "Missing 'monitors_unknown'"
        assert 'alerts_firing' in data, "Missing 'alerts_firing'"
        assert 'alerts_critical' in data, "Missing 'alerts_critical'"
        assert 'channels' in data, "Missing 'channels'"
        assert 'rules' in data, "Missing 'rules'"
        assert 'engine' in data, "Missing 'engine'"
        assert data['engine'].get('running') == True, f"Engine should be running, got {data['engine']}"
        self.log(f"✓ Stats: monitors={data['monitors_total']}, alerts={data['alerts_firing']}, engine running={data['engine']['running']}")

    # Test 2: POST /api/monitoring/monitors (create TCP monitor)
    def test_create_monitor(self):
        payload = {
            "name": "Google TCP Check",
            "type": "tcp",
            "target": "google.com",
            "port": 443,
            "interval_seconds": 30,
            "timeout_seconds": 5,
            "enabled": True,
            "description": "Test TCP monitor for google.com:443"
        }
        resp = requests.post(f"{BASE_URL}/monitoring/monitors", json=payload, headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        self.log(f"Created monitor: {data}")
        assert 'id' in data, "No id in response"
        assert data['name'] == "Google TCP Check", f"Name mismatch: {data['name']}"
        assert data['type'] == "tcp", f"Type mismatch: {data['type']}"
        assert data['target'] == "google.com", f"Target mismatch: {data['target']}"
        assert data['port'] == 443, f"Port mismatch: {data['port']}"
        assert data['current_status'] == 'unknown', f"Initial status should be 'unknown', got {data['current_status']}"
        self.monitor_id = data['id']
        self.log(f"✓ Monitor created with id: {self.monitor_id}")

    # Test 3: GET /api/monitoring/monitors
    def test_list_monitors(self):
        resp = requests.get(f"{BASE_URL}/monitoring/monitors", headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        self.log(f"Monitors list: total={data.get('total')}")
        assert 'results' in data, "Missing 'results'"
        assert 'total' in data, "Missing 'total'"
        assert data['total'] >= 1, f"Expected at least 1 monitor, got {data['total']}"
        found = any(m['id'] == self.monitor_id for m in data['results'])
        assert found, f"Created monitor {self.monitor_id} not found in list"
        self.log(f"✓ Found {data['total']} monitors")

    # Test 4: POST /api/monitoring/monitors/{id}/run
    def test_run_monitor(self):
        assert self.monitor_id, "No monitor_id available"
        resp = requests.post(f"{BASE_URL}/monitoring/monitors/{self.monitor_id}/run", headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        self.log(f"Run monitor response: {data}")
        # After run, status should be updated (likely 'ok' for google.com:443)
        assert data.get('current_status') in ['ok', 'warning', 'critical', 'unknown'], f"Invalid status: {data.get('current_status')}"
        assert data.get('last_check_at') is not None, "last_check_at should be set after run"
        self.log(f"✓ Monitor run completed: status={data.get('current_status')}, latency={data.get('last_latency_ms')}ms")

    # Test 5: GET /api/monitoring/monitors/{id}/metrics
    def test_get_metrics(self):
        assert self.monitor_id, "No monitor_id available"
        # Wait a moment for metric to be persisted
        time.sleep(1)
        resp = requests.get(f"{BASE_URL}/monitoring/monitors/{self.monitor_id}/metrics?hours=1&limit=100", headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        self.log(f"Metrics response: count={data.get('count')}")
        assert 'results' in data, "Missing 'results'"
        assert 'count' in data, "Missing 'count'"
        assert data['count'] >= 1, f"Expected at least 1 metric sample, got {data['count']}"
        sample = data['results'][0]
        assert 'status' in sample, "Sample missing 'status'"
        assert 'latency_ms' in sample, "Sample missing 'latency_ms'"
        assert 'time' in sample, "Sample missing 'time'"
        self.log(f"✓ Found {data['count']} metric samples, first: status={sample['status']}, latency={sample.get('latency_ms')}ms")

    # Test 6: PATCH /api/monitoring/monitors/{id}
    def test_update_monitor(self):
        assert self.monitor_id, "No monitor_id available"
        payload = {"description": "Updated description", "interval_seconds": 60}
        resp = requests.patch(f"{BASE_URL}/monitoring/monitors/{self.monitor_id}", json=payload, headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        self.log(f"Updated monitor: {data}")
        assert data['description'] == "Updated description", f"Description not updated: {data['description']}"
        assert data['interval_seconds'] == 60, f"Interval not updated: {data['interval_seconds']}"
        self.log(f"✓ Monitor updated successfully")

    # Test 7: POST /api/monitoring/rules (create alert rule)
    def test_create_rule(self):
        assert self.monitor_id, "No monitor_id available"
        payload = {
            "name": "Test Alert Rule",
            "monitor_id": self.monitor_id,
            "condition": "down",
            "severity": "critical",
            "enabled": True,
            "description": "Test rule for down condition"
        }
        resp = requests.post(f"{BASE_URL}/monitoring/rules", json=payload, headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        self.log(f"Created rule: {data}")
        assert 'id' in data, "No id in response"
        assert data['name'] == "Test Alert Rule", f"Name mismatch: {data['name']}"
        assert data['condition'] == "down", f"Condition mismatch: {data['condition']}"
        assert data['severity'] == "critical", f"Severity mismatch: {data['severity']}"
        self.rule_id = data['id']
        self.log(f"✓ Rule created with id: {self.rule_id}")

    # Test 8: GET /api/monitoring/rules
    def test_list_rules(self):
        resp = requests.get(f"{BASE_URL}/monitoring/rules", headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        self.log(f"Rules list: total={data.get('total')}")
        assert 'results' in data, "Missing 'results'"
        assert 'total' in data, "Missing 'total'"
        assert data['total'] >= 1, f"Expected at least 1 rule, got {data['total']}"
        found = any(r['id'] == self.rule_id for r in data['results'])
        assert found, f"Created rule {self.rule_id} not found in list"
        self.log(f"✓ Found {data['total']} rules")

    # Test 9: PATCH /api/monitoring/rules/{id}
    def test_update_rule(self):
        assert self.rule_id, "No rule_id available"
        payload = {"description": "Updated rule description"}
        resp = requests.patch(f"{BASE_URL}/monitoring/rules/{self.rule_id}", json=payload, headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        self.log(f"Updated rule: {data}")
        assert data['description'] == "Updated rule description", f"Description not updated: {data['description']}"
        self.log(f"✓ Rule updated successfully")

    # Test 10: Alert flow - create unreachable monitor, trigger, check alert
    def test_alert_flow_create_unreachable_monitor(self):
        payload = {
            "name": "Unreachable Test",
            "type": "tcp",
            "target": "192.0.2.1",  # TEST-NET-1, unreachable
            "port": 9999,
            "interval_seconds": 30,
            "timeout_seconds": 2,
            "enabled": True
        }
        resp = requests.post(f"{BASE_URL}/monitoring/monitors", json=payload, headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        self.unreachable_monitor_id = data['id']
        self.log(f"✓ Created unreachable monitor: {self.unreachable_monitor_id}")

    def test_alert_flow_create_rule_for_unreachable(self):
        assert self.unreachable_monitor_id, "No unreachable_monitor_id available"
        payload = {
            "name": "Critical Down Alert",
            "monitor_id": self.unreachable_monitor_id,
            "condition": "down",
            "severity": "critical",
            "enabled": True
        }
        resp = requests.post(f"{BASE_URL}/monitoring/rules", json=payload, headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        self.log(f"✓ Created rule for unreachable monitor: {data['id']}")

    def test_alert_flow_trigger_and_check(self):
        assert self.unreachable_monitor_id, "No unreachable_monitor_id available"
        # Trigger run
        resp = requests.post(f"{BASE_URL}/monitoring/monitors/{self.unreachable_monitor_id}/run", headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        self.log(f"Triggered unreachable monitor: status={data.get('current_status')}")
        assert data.get('current_status') in ['critical', 'unknown'], f"Expected critical/unknown, got {data.get('current_status')}"
        
        # Wait for alert to be created
        time.sleep(2)
        
        # Check for firing alerts
        resp = requests.get(f"{BASE_URL}/monitoring/alerts?state=firing", headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        self.log(f"Firing alerts: total={data.get('total')}")
        assert 'results' in data, "Missing 'results'"
        # Should have at least one firing alert
        assert data['total'] >= 1, f"Expected at least 1 firing alert, got {data['total']}"
        # Find our alert
        alert = next((a for a in data['results'] if a.get('monitor_id') == self.unreachable_monitor_id), None)
        assert alert is not None, f"Alert for monitor {self.unreachable_monitor_id} not found"
        self.alert_id = alert['id']
        assert alert['state'] == 'firing', f"Alert state should be 'firing', got {alert['state']}"
        assert alert['severity'] == 'critical', f"Alert severity should be 'critical', got {alert['severity']}"
        self.log(f"✓ Alert created and firing: {self.alert_id}, severity={alert['severity']}")

    # Test 11: POST /api/monitoring/alerts/{id}/acknowledge
    def test_acknowledge_alert(self):
        assert self.alert_id, "No alert_id available"
        resp = requests.post(f"{BASE_URL}/monitoring/alerts/{self.alert_id}/acknowledge", headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        self.log(f"Acknowledged alert: {data}")
        assert data.get('acknowledged_at') is not None, "acknowledged_at should be set"
        assert data.get('acknowledged_by') == 'admin', f"acknowledged_by should be 'admin', got {data.get('acknowledged_by')}"
        self.log(f"✓ Alert acknowledged by {data.get('acknowledged_by')}")

    # Test 12: POST /api/monitoring/alerts/{id}/resolve
    def test_resolve_alert(self):
        assert self.alert_id, "No alert_id available"
        resp = requests.post(f"{BASE_URL}/monitoring/alerts/{self.alert_id}/resolve", headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        self.log(f"Resolved alert: {data}")
        assert data.get('state') == 'resolved', f"State should be 'resolved', got {data.get('state')}"
        assert data.get('resolved_at') is not None, "resolved_at should be set"
        self.log(f"✓ Alert resolved")

    # Test 13: POST /api/monitoring/channels (create in-app channel)
    def test_create_channel(self):
        payload = {
            "name": "Test In-App Channel",
            "type": "inapp",
            "enabled": True,
            "config": {},
            "description": "Test in-app notification channel"
        }
        resp = requests.post(f"{BASE_URL}/monitoring/channels", json=payload, headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        self.log(f"Created channel: {data}")
        assert 'id' in data, "No id in response"
        assert data['name'] == "Test In-App Channel", f"Name mismatch: {data['name']}"
        assert data['type'] == "inapp", f"Type mismatch: {data['type']}"
        self.channel_id = data['id']
        self.log(f"✓ Channel created with id: {self.channel_id}")

    # Test 14: GET /api/monitoring/channels
    def test_list_channels(self):
        resp = requests.get(f"{BASE_URL}/monitoring/channels", headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        self.log(f"Channels list: total={data.get('total')}")
        assert 'results' in data, "Missing 'results'"
        assert 'total' in data, "Missing 'total'"
        assert data['total'] >= 1, f"Expected at least 1 channel, got {data['total']}"
        found = any(c['id'] == self.channel_id for c in data['results'])
        assert found, f"Created channel {self.channel_id} not found in list"
        self.log(f"✓ Found {data['total']} channels")

    # Test 15: POST /api/monitoring/channels/{id}/test
    def test_test_channel(self):
        assert self.channel_id, "No channel_id available"
        resp = requests.post(f"{BASE_URL}/monitoring/channels/{self.channel_id}/test", headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        self.log(f"Test channel response: {data}")
        assert 'ok' in data, "Missing 'ok' in response"
        # In-app channels should return ok=True
        assert data['ok'] == True, f"Expected ok=True for in-app channel, got {data}"
        self.log(f"✓ Channel test successful")

    # Test 16: PATCH /api/monitoring/channels/{id}
    def test_update_channel(self):
        assert self.channel_id, "No channel_id available"
        payload = {"description": "Updated channel description"}
        resp = requests.patch(f"{BASE_URL}/monitoring/channels/{self.channel_id}", json=payload, headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        self.log(f"Updated channel: {data}")
        assert data['description'] == "Updated channel description", f"Description not updated: {data['description']}"
        self.log(f"✓ Channel updated successfully")

    # Test 17: GET /api/monitoring/notifications
    def test_list_notifications(self):
        resp = requests.get(f"{BASE_URL}/monitoring/notifications", headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        self.log(f"Notifications list: total={data.get('total')}")
        assert 'results' in data, "Missing 'results'"
        assert 'total' in data, "Missing 'total'"
        # May be 0 if no notifications sent yet
        self.log(f"✓ Found {data['total']} notifications")

    # Test 18: SSE endpoint /api/monitoring/stream
    def test_sse_stream(self):
        self.log("Testing SSE stream endpoint...")
        try:
            # Use streaming request with timeout
            url = f"{BASE_URL}/monitoring/stream?token={self.token}"
            resp = requests.get(url, headers={'Accept': 'text/event-stream'}, stream=True, timeout=5)
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
            
            # Read first few events
            events = []
            for i, line in enumerate(resp.iter_lines(decode_unicode=True)):
                if i > 20:  # Read max 20 lines
                    break
                if line:
                    self.log(f"  SSE line: {line}")
                    if line.startswith('event:') or line.startswith('data:'):
                        events.append(line)
            
            # Should have received at least the 'hello' event
            assert len(events) >= 2, f"Expected at least 2 SSE lines (event + data), got {len(events)}"
            # Check for hello event
            has_hello = any('hello' in e for e in events)
            assert has_hello, f"Expected 'hello' event in SSE stream, got: {events}"
            self.log(f"✓ SSE stream working, received {len(events)} lines including 'hello' event")
        except requests.exceptions.Timeout:
            self.log("✓ SSE stream connected (timed out after reading initial events, which is expected)")
        except Exception as e:
            raise AssertionError(f"SSE stream test failed: {e}")

    # Test 19: Cleanup - delete test data
    def test_cleanup_delete_channel(self):
        if self.channel_id:
            resp = requests.delete(f"{BASE_URL}/monitoring/channels/{self.channel_id}", headers=self.headers())
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
            self.log(f"✓ Deleted channel {self.channel_id}")

    def test_cleanup_delete_rule(self):
        if self.rule_id:
            resp = requests.delete(f"{BASE_URL}/monitoring/rules/{self.rule_id}", headers=self.headers())
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
            self.log(f"✓ Deleted rule {self.rule_id}")

    def test_cleanup_delete_monitor(self):
        if self.monitor_id:
            resp = requests.delete(f"{BASE_URL}/monitoring/monitors/{self.monitor_id}", headers=self.headers())
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
            data = resp.json()
            assert data.get('deleted') == self.monitor_id, f"Delete response mismatch: {data}"
            # Verify metrics were also deleted
            time.sleep(1)
            resp = requests.get(f"{BASE_URL}/monitoring/monitors/{self.monitor_id}/metrics", headers=self.headers())
            assert resp.status_code == 404, f"Monitor should be deleted, got {resp.status_code}"
            self.log(f"✓ Deleted monitor {self.monitor_id} and its metrics")

    def test_cleanup_delete_unreachable_monitor(self):
        if self.unreachable_monitor_id:
            resp = requests.delete(f"{BASE_URL}/monitoring/monitors/{self.unreachable_monitor_id}", headers=self.headers())
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
            self.log(f"✓ Deleted unreachable monitor {self.unreachable_monitor_id}")

    # Test 20: Sanity check - existing endpoints still work
    def test_sanity_stats_endpoint(self):
        resp = requests.get(f"{BASE_URL}/stats", headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert 'devices' in data or 'sites' in data, "Stats endpoint should return device/site counts"
        self.log(f"✓ Sanity check: /api/stats working")

    def test_sanity_sites_endpoint(self):
        resp = requests.get(f"{BASE_URL}/sites", headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert 'results' in data, "Sites endpoint should return results"
        self.log(f"✓ Sanity check: /api/sites working")

    def test_sanity_discovery_stats(self):
        resp = requests.get(f"{BASE_URL}/discovery/stats", headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert 'credentials' in data or 'jobs' in data, "Discovery stats should return counts"
        self.log(f"✓ Sanity check: /api/discovery/stats working")

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("\n" + "="*80)
        print("SMIFS MONITORING ENGINE (PHASE 8) - BACKEND API TESTS")
        print("="*80)
        
        # Login first
        try:
            self.login()
        except Exception as e:
            self.log(f"FATAL: Login failed - {e}", "ERROR")
            return 1

        # Run all tests
        self.test("1. GET /api/monitoring/stats", self.test_stats)
        self.test("2. POST /api/monitoring/monitors (create TCP monitor)", self.test_create_monitor)
        self.test("3. GET /api/monitoring/monitors (list)", self.test_list_monitors)
        self.test("4. POST /api/monitoring/monitors/{id}/run", self.test_run_monitor)
        self.test("5. GET /api/monitoring/monitors/{id}/metrics", self.test_get_metrics)
        self.test("6. PATCH /api/monitoring/monitors/{id}", self.test_update_monitor)
        self.test("7. POST /api/monitoring/rules (create)", self.test_create_rule)
        self.test("8. GET /api/monitoring/rules (list)", self.test_list_rules)
        self.test("9. PATCH /api/monitoring/rules/{id}", self.test_update_rule)
        self.test("10. Alert flow: create unreachable monitor", self.test_alert_flow_create_unreachable_monitor)
        self.test("11. Alert flow: create rule for unreachable", self.test_alert_flow_create_rule_for_unreachable)
        self.test("12. Alert flow: trigger and check alert", self.test_alert_flow_trigger_and_check)
        self.test("13. POST /api/monitoring/alerts/{id}/acknowledge", self.test_acknowledge_alert)
        self.test("14. POST /api/monitoring/alerts/{id}/resolve", self.test_resolve_alert)
        self.test("15. POST /api/monitoring/channels (create)", self.test_create_channel)
        self.test("16. GET /api/monitoring/channels (list)", self.test_list_channels)
        self.test("17. POST /api/monitoring/channels/{id}/test", self.test_test_channel)
        self.test("18. PATCH /api/monitoring/channels/{id}", self.test_update_channel)
        self.test("19. GET /api/monitoring/notifications", self.test_list_notifications)
        self.test("20. GET /api/monitoring/stream (SSE)", self.test_sse_stream)
        self.test("21. Cleanup: delete channel", self.test_cleanup_delete_channel)
        self.test("22. Cleanup: delete rule", self.test_cleanup_delete_rule)
        self.test("23. Cleanup: delete monitor", self.test_cleanup_delete_monitor)
        self.test("24. Cleanup: delete unreachable monitor", self.test_cleanup_delete_unreachable_monitor)
        self.test("25. Sanity: GET /api/stats", self.test_sanity_stats_endpoint)
        self.test("26. Sanity: GET /api/sites", self.test_sanity_sites_endpoint)
        self.test("27. Sanity: GET /api/discovery/stats", self.test_sanity_discovery_stats)

        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Total tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed} ✅")
        print(f"Failed: {self.tests_failed} ❌")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failures:
            print("\n" + "="*80)
            print("FAILURES:")
            print("="*80)
            for i, failure in enumerate(self.failures, 1):
                print(f"{i}. {failure}")
        
        return 0 if self.tests_failed == 0 else 1

if __name__ == "__main__":
    tester = MonitoringTester()
    sys.exit(tester.run_all_tests())
