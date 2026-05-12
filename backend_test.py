#!/usr/bin/env python3
"""
Backend API tests for SMIFS Discovery Module
Tests all 17 backend features specified in the review request.
"""
import requests
import sys
import time
from datetime import datetime

BASE_URL = "https://data-centre-hub.preview.emergentagent.com/api"

class DiscoveryTester:
    def __init__(self):
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []
        self.credential_id = None
        self.job_id = None
        self.discovered_device_id = None

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

    # Test 1: GET /api/discovery/stats
    def test_stats(self):
        resp = requests.get(f"{BASE_URL}/discovery/stats", headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        self.log(f"Stats response: {data}")
        assert 'credentials' in data, "Missing 'credentials' in stats"
        assert 'jobs' in data, "Missing 'jobs' in stats"
        assert 'discovered_devices' in data, "Missing 'discovered_devices' in stats"
        assert 'imported_devices' in data, "Missing 'imported_devices' in stats"
        self.log(f"✓ Stats: {data}")

    # Test 2-4: Credentials CRUD
    def test_create_credential(self):
        payload = {
            "name": "test-snmp-cred",
            "snmp_version": "v2c",
            "community": "public",
            "port": 161,
            "description": "Test credential"
        }
        resp = requests.post(f"{BASE_URL}/discovery/credentials", json=payload, headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        self.log(f"Created credential: {data}")
        assert 'id' in data, "No id in response"
        assert data['name'] == "test-snmp-cred", f"Name mismatch: {data['name']}"
        assert data['snmp_version'] == "v2c", f"Version mismatch: {data['snmp_version']}"
        assert data['community'] == "public", f"Community mismatch: {data['community']}"
        self.credential_id = data['id']
        self.log(f"✓ Credential created with id: {self.credential_id}")

    def test_list_credentials(self):
        resp = requests.get(f"{BASE_URL}/discovery/credentials", headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        self.log(f"Credentials list: {data}")
        assert 'results' in data, "Missing 'results' in response"
        assert 'total' in data, "Missing 'total' in response"
        assert data['total'] >= 1, f"Expected at least 1 credential, got {data['total']}"
        found = any(c['id'] == self.credential_id for c in data['results'])
        assert found, f"Created credential {self.credential_id} not found in list"
        self.log(f"✓ Found {data['total']} credentials")

    def test_delete_credential(self):
        # Create a temp credential to delete
        payload = {"name": "temp-delete", "snmp_version": "v2c", "community": "public"}
        resp = requests.post(f"{BASE_URL}/discovery/credentials", json=payload, headers=self.headers())
        assert resp.status_code == 200, f"Failed to create temp credential: {resp.status_code}"
        temp_id = resp.json()['id']
        
        # Delete it
        resp = requests.delete(f"{BASE_URL}/discovery/credentials/{temp_id}", headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert data.get('deleted') == temp_id, f"Delete response mismatch: {data}"
        self.log(f"✓ Deleted credential {temp_id}")

    # Test 5: POST /api/discovery/scan (ad-hoc)
    def test_adhoc_scan(self):
        payload = {"target": "192.168.1.1", "timeout": 3}
        resp = requests.post(f"{BASE_URL}/discovery/scan", json=payload, headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        self.log(f"Scan result: {data}")
        assert 'target' in data, "Missing 'target' in response"
        assert data['target'] == "192.168.1.1", f"Target mismatch: {data['target']}"
        assert 'vendor' in data, "Missing 'vendor' in response"
        assert 'model' in data, "Missing 'model' in response"
        assert 'interfaces' in data, "Missing 'interfaces' in response"
        assert 'ip_addresses' in data, "Missing 'ip_addresses' in response"
        assert 'neighbors' in data, "Missing 'neighbors' in response"
        assert isinstance(data['interfaces'], list), "interfaces should be a list"
        assert isinstance(data['ip_addresses'], list), "ip_addresses should be a list"
        assert isinstance(data['neighbors'], list), "neighbors should be a list"
        # Should be simulated in sandbox
        assert data.get('simulated') or data.get('reachable'), "Device should be simulated or reachable"
        self.log(f"✓ Scan returned: vendor={data['vendor']}, model={data['model']}, interfaces={len(data['interfaces'])}")

    # Test 6-8: Jobs
    def test_create_job(self):
        payload = {
            "name": "Test Job",
            "target_spec": "10.0.0.1-3",
            "auto_import": True,
            "description": "Test discovery job"
        }
        resp = requests.post(f"{BASE_URL}/discovery/jobs", json=payload, headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        self.log(f"Created job: {data}")
        assert 'id' in data, "No id in response"
        assert data['name'] == "Test Job", f"Name mismatch: {data['name']}"
        assert data['target_spec'] == "10.0.0.1-3", f"Target spec mismatch: {data['target_spec']}"
        assert data['status'] == 'pending', f"Expected status 'pending', got {data['status']}"
        assert data['auto_import'] == True, f"auto_import should be True"
        self.job_id = data['id']
        self.log(f"✓ Job created with id: {self.job_id}")

    def test_run_job(self):
        assert self.job_id, "No job_id available"
        resp = requests.post(f"{BASE_URL}/discovery/jobs/{self.job_id}/run", headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        self.log(f"Run job response: {data}")
        assert data.get('status') == 'queued', f"Expected status 'queued', got {data.get('status')}"
        self.log(f"✓ Job {self.job_id} queued")

    def test_job_completion(self):
        """Wait for job to complete and verify stats"""
        assert self.job_id, "No job_id available"
        self.log("Waiting for job to complete (max 15 seconds)...")
        
        for i in range(15):
            time.sleep(1)
            resp = requests.get(f"{BASE_URL}/discovery/jobs/{self.job_id}", headers=self.headers())
            assert resp.status_code == 200, f"Failed to get job: {resp.status_code}"
            data = resp.json()
            self.log(f"  [{i+1}s] Job status: {data['status']}, stats: {data.get('stats', {})}")
            
            if data['status'] == 'completed':
                stats = data.get('stats', {})
                assert stats.get('scanned', 0) >= 1, f"Expected scanned >= 1, got {stats.get('scanned')}"
                assert stats.get('discovered', 0) >= 1, f"Expected discovered >= 1, got {stats.get('discovered')}"
                # Because auto_import=true, should have imported at least 1
                assert stats.get('imported', 0) >= 1, f"Expected imported >= 1, got {stats.get('imported')}"
                self.log(f"✓ Job completed: scanned={stats['scanned']}, discovered={stats['discovered']}, imported={stats['imported']}")
                return
        
        raise AssertionError(f"Job did not complete within 15 seconds")

    # Test 9-10: Discovered devices
    def test_list_discovered_devices(self):
        resp = requests.get(f"{BASE_URL}/discovery/devices", headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        self.log(f"Discovered devices: total={data.get('total')}")
        assert 'results' in data, "Missing 'results' in response"
        assert 'total' in data, "Missing 'total' in response"
        assert data['total'] >= 1, f"Expected at least 1 discovered device, got {data['total']}"
        # Save first device id for import test
        if data['results']:
            self.discovered_device_id = data['results'][0]['id']
            self.log(f"✓ Found {data['total']} discovered devices, first id: {self.discovered_device_id}")

    def test_import_device(self):
        assert self.discovered_device_id, "No discovered_device_id available"
        resp = requests.post(f"{BASE_URL}/discovery/devices/{self.discovered_device_id}/import", 
                           json={}, headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        self.log(f"Import result: {data}")
        assert 'device_id' in data, "Missing 'device_id' in response"
        assert 'interfaces_created' in data, "Missing 'interfaces_created' in response"
        assert 'ips_created' in data, "Missing 'ips_created' in response"
        assert 'cables_created' in data, "Missing 'cables_created' in response"
        self.log(f"✓ Imported device: device_id={data['device_id']}, interfaces={data['interfaces_created']}, ips={data['ips_created']}, cables={data['cables_created']}")

    # Test 11: Check auto-discovered tag
    def test_auto_discovered_tag(self):
        resp = requests.get(f"{BASE_URL}/devices?q=auto", headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        self.log(f"Auto-discovered devices: {data}")
        assert 'results' in data, "Missing 'results' in response"
        # Should have at least one device with auto-discovered tag
        found = False
        for device in data.get('results', []):
            if 'auto-discovered' in device.get('tags', []):
                found = True
                self.log(f"✓ Found auto-discovered device: {device.get('name')} with tags: {device.get('tags')}")
                break
        assert found, "No devices found with 'auto-discovered' tag"

    # Test 12: Topology
    def test_topology(self):
        resp = requests.get(f"{BASE_URL}/discovery/topology", headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        self.log(f"Topology: {data}")
        assert 'nodes' in data, "Missing 'nodes' in response"
        assert 'edges' in data, "Missing 'edges' in response"
        assert isinstance(data['nodes'], list), "nodes should be a list"
        assert isinstance(data['edges'], list), "edges should be a list"
        self.log(f"✓ Topology: {len(data['nodes'])} nodes, {len(data['edges'])} edges")

    # Test 13-16: Netdisco integration
    def test_netdisco_test_bogus(self):
        """Test with bogus URL - should return reachable=false, not 500"""
        payload = {
            "base_url": "https://bogus-netdisco-url-that-does-not-exist.example.com",
            "username": "test",
            "password": "test",
            "verify_ssl": False
        }
        resp = requests.post(f"{BASE_URL}/discovery/netdisco/test", json=payload, headers=self.headers())
        # Should NOT return 500
        assert resp.status_code != 500, f"Should not return 500 for bogus URL, got {resp.status_code}: {resp.text}"
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        self.log(f"Netdisco test result: {data}")
        assert 'reachable' in data, "Missing 'reachable' in response"
        assert data['reachable'] == False, f"Expected reachable=false for bogus URL, got {data['reachable']}"
        self.log(f"✓ Netdisco test with bogus URL returned reachable=false (graceful)")

    def test_netdisco_sync_bogus(self):
        """Sync with bogus URL - should return devices_pulled=0, not 500"""
        payload = {
            "base_url": "https://bogus-netdisco-url-that-does-not-exist.example.com",
            "username": "test",
            "password": "test",
            "verify_ssl": False
        }
        resp = requests.post(f"{BASE_URL}/discovery/netdisco/sync", json=payload, headers=self.headers())
        # Should NOT return 500
        assert resp.status_code != 500, f"Should not return 500 for bogus URL, got {resp.status_code}: {resp.text}"
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        self.log(f"Netdisco sync result: {data}")
        assert 'devices_pulled' in data, "Missing 'devices_pulled' in response"
        assert data['devices_pulled'] == 0, f"Expected devices_pulled=0 for bogus URL, got {data['devices_pulled']}"
        self.log(f"✓ Netdisco sync with bogus URL returned devices_pulled=0 (graceful)")

    def test_netdisco_settings_get(self):
        resp = requests.get(f"{BASE_URL}/discovery/netdisco/settings", headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        self.log(f"Netdisco settings: {data}")
        # Should return a dict (may be empty or have defaults)
        assert isinstance(data, dict), "Settings should be a dict"
        # If password exists, it should be masked
        if 'password' in data and data['password']:
            assert data['password'] == '***', f"Password should be masked, got {data['password']}"
        self.log(f"✓ Netdisco settings retrieved")

    def test_netdisco_settings_save(self):
        payload = {
            "base_url": "https://test-netdisco.example.com",
            "username": "testuser",
            "password": "testpass",
            "verify_ssl": True
        }
        resp = requests.post(f"{BASE_URL}/discovery/netdisco/settings", json=payload, headers=self.headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        self.log(f"Save settings result: {data}")
        assert data.get('saved') == True, f"Expected saved=true, got {data}"
        self.log(f"✓ Netdisco settings saved")

    # Test 17: Auth enforcement
    def test_auth_required(self):
        """Test that endpoints require authentication"""
        resp = requests.post(f"{BASE_URL}/discovery/jobs", json={"name": "test", "target_spec": "10.0.0.1"})
        assert resp.status_code == 401, f"Expected 401 without auth, got {resp.status_code}"
        self.log(f"✓ Auth required: got 401 as expected")

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("\n" + "="*80)
        print("SMIFS DISCOVERY MODULE - BACKEND API TESTS")
        print("="*80)
        
        # Login first
        try:
            self.login()
        except Exception as e:
            self.log(f"FATAL: Login failed - {e}", "ERROR")
            return 1

        # Run all tests
        self.test("1. GET /api/discovery/stats", self.test_stats)
        self.test("2. POST /api/discovery/credentials (create)", self.test_create_credential)
        self.test("3. GET /api/discovery/credentials (list)", self.test_list_credentials)
        self.test("4. DELETE /api/discovery/credentials/{id}", self.test_delete_credential)
        self.test("5. POST /api/discovery/scan (ad-hoc scan)", self.test_adhoc_scan)
        self.test("6. POST /api/discovery/jobs (create job)", self.test_create_job)
        self.test("7. POST /api/discovery/jobs/{id}/run", self.test_run_job)
        self.test("8. GET /api/discovery/jobs/{id} (completion check)", self.test_job_completion)
        self.test("9. GET /api/discovery/devices (list)", self.test_list_discovered_devices)
        self.test("10. POST /api/discovery/devices/{id}/import", self.test_import_device)
        self.test("11. GET /api/devices?q=auto (check auto-discovered tag)", self.test_auto_discovered_tag)
        self.test("12. GET /api/discovery/topology", self.test_topology)
        self.test("13. POST /api/discovery/netdisco/test (bogus URL)", self.test_netdisco_test_bogus)
        self.test("14. POST /api/discovery/netdisco/sync (bogus URL)", self.test_netdisco_sync_bogus)
        self.test("15. GET /api/discovery/netdisco/settings", self.test_netdisco_settings_get)
        self.test("16. POST /api/discovery/netdisco/settings", self.test_netdisco_settings_save)
        self.test("17. Auth enforcement (401 without token)", self.test_auth_required)

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
    tester = DiscoveryTester()
    sys.exit(tester.run_all_tests())
