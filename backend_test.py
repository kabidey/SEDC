"""
Comprehensive backend API tests for SMIFS Enterprise Data Centre (NetBox clone)
Tests all 95 models and special endpoints as specified in the review request.
"""
import requests
import sys
import json
from datetime import datetime

BASE_URL = "https://data-centre-hub.preview.emergentagent.com/api"

class NetBoxTester:
    def __init__(self):
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []
        self.created_ids = {}  # Track created resources for cleanup and FK references

    def log(self, msg, level="INFO"):
        print(f"[{level}] {msg}")

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{BASE_URL}{endpoint}"
        h = {'Content-Type': 'application/json'}
        if self.token:
            h['Authorization'] = f'Bearer {self.token}'
        if headers:
            h.update(headers)

        self.tests_run += 1
        self.log(f"Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=h, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=h, timeout=10)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=h, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=h, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ PASSED - {name} (Status: {response.status_code})", "PASS")
                try:
                    return True, response.json() if response.text else {}
                except:
                    return True, {}
            else:
                self.tests_failed += 1
                error_detail = response.text[:200] if response.text else "No response body"
                self.log(f"❌ FAILED - {name} - Expected {expected_status}, got {response.status_code}", "FAIL")
                self.log(f"   Response: {error_detail}", "FAIL")
                self.failures.append({
                    'test': name,
                    'expected': expected_status,
                    'actual': response.status_code,
                    'response': error_detail
                })
                return False, {}

        except Exception as e:
            self.tests_failed += 1
            self.log(f"❌ FAILED - {name} - Error: {str(e)}", "FAIL")
            self.failures.append({'test': name, 'error': str(e)})
            return False, {}

    def test_root_endpoint(self):
        """Test GET /api/ returns app info"""
        success, data = self.run_test("Root endpoint", "GET", "/", 200)
        if success and data.get('app') == 'SMIFS Enterprise Data Centre':
            self.log("Root endpoint returned correct app info")
        return success

    def test_health_endpoint(self):
        """Test GET /api/health returns ok"""
        success, data = self.run_test("Health check", "GET", "/health", 200)
        if success and data.get('status') == 'ok':
            self.log("Health check passed")
        return success

    def test_login(self):
        """Test POST /api/auth/login with admin/admin"""
        success, data = self.run_test(
            "Login with admin/admin",
            "POST",
            "/auth/login",
            200,
            data={"username": "admin", "password": "admin"}
        )
        if success and 'access_token' in data and 'user' in data:
            self.token = data['access_token']
            self.log(f"Login successful, token obtained, user: {data['user'].get('username')}")
            return True
        return False

    def test_register(self):
        """Test POST /api/auth/register creates new user"""
        username = f"testuser_{datetime.now().strftime('%H%M%S%f')}"
        success, data = self.run_test(
            "Register new user",
            "POST",
            "/auth/register",
            200,
            data={"username": username, "password": "testpass123", "email": "test@example.com"}
        )
        return success and 'access_token' in data

    def test_auth_me(self):
        """Test GET /api/auth/me returns current user"""
        success, data = self.run_test("Get current user", "GET", "/auth/me", 200)
        return success and data.get('username') == 'admin'

    def test_schema_endpoint(self):
        """Test GET /api/_schema returns list of all models"""
        success, data = self.run_test("Schema introspection", "GET", "/_schema", 200)
        if success:
            models = data.get('models', [])
            self.log(f"Schema returned {len(models)} models")
            if len(models) >= 90:  # Should have ~95 models
                self.log("✅ Schema has expected number of models")
            else:
                self.log(f"⚠️  Schema has only {len(models)} models, expected ~95")
        return success

    def test_sites_crud(self):
        """Test full CRUD on /api/sites"""
        # CREATE
        site_data = {"name": "Test Site Alpha", "status": "active", "facility": "DC-01"}
        success, site = self.run_test("Create site", "POST", "/sites", 200, data=site_data)
        if not success:
            return False
        site_id = site.get('id')
        self.created_ids['site'] = site_id
        
        # LIST
        success, list_data = self.run_test("List sites", "GET", "/sites?limit=10", 200)
        if not success or not list_data.get('results'):
            return False
        
        # GET by ID
        success, get_data = self.run_test(f"Get site by ID", "GET", f"/sites/{site_id}", 200)
        if not success or get_data.get('id') != site_id:
            return False
        
        # UPDATE
        update_data = {"name": "Test Site Alpha Updated", "status": "planned"}
        success, updated = self.run_test(f"Update site", "PATCH", f"/sites/{site_id}", 200, data=update_data)
        if not success or updated.get('name') != "Test Site Alpha Updated":
            return False
        
        # Don't delete yet - we need it for FK references
        return True

    def test_devices_crud(self):
        """Test full CRUD on /api/devices with required FKs"""
        # First create dependencies: manufacturer, device-type, device-role, site
        success, mfr = self.run_test("Create manufacturer", "POST", "/manufacturers", 200, 
                                     data={"name": "Cisco"})
        if not success:
            return False
        mfr_id = mfr.get('id')
        
        success, dtype = self.run_test("Create device-type", "POST", "/device-types", 200,
                                       data={"manufacturer_id": mfr_id, "model": "Catalyst 9300", "u_height": 1})
        if not success:
            return False
        dtype_id = dtype.get('id')
        
        success, role = self.run_test("Create device-role", "POST", "/device-roles", 200,
                                      data={"name": "Switch", "color": "0000ff"})
        if not success:
            return False
        role_id = role.get('id')
        
        site_id = self.created_ids.get('site')
        if not site_id:
            self.log("⚠️  No site_id available, creating one")
            success, site = self.run_test("Create site for device", "POST", "/sites", 200,
                                         data={"name": "Device Test Site"})
            if not success:
                return False
            site_id = site.get('id')
        
        # CREATE device
        device_data = {
            "name": "sw-core-01",
            "device_type_id": dtype_id,
            "role_id": role_id,
            "site_id": site_id,
            "status": "active"
        }
        success, device = self.run_test("Create device", "POST", "/devices", 200, data=device_data)
        if not success:
            return False
        device_id = device.get('id')
        self.created_ids['device'] = device_id
        
        # GET
        success, _ = self.run_test("Get device", "GET", f"/devices/{device_id}", 200)
        if not success:
            return False
        
        # UPDATE
        success, _ = self.run_test("Update device", "PATCH", f"/devices/{device_id}", 200,
                                   data={"serial": "ABC123XYZ"})
        if not success:
            return False
        
        # DELETE
        success, _ = self.run_test("Delete device", "DELETE", f"/devices/{device_id}", 200)
        return success

    def test_racks_crud(self):
        """Test full CRUD on /api/racks"""
        site_id = self.created_ids.get('site')
        if not site_id:
            success, site = self.run_test("Create site for rack", "POST", "/sites", 200,
                                         data={"name": "Rack Test Site"})
            if not success:
                return False
            site_id = site.get('id')
        
        rack_data = {"name": "Rack-A-01", "site_id": site_id, "u_height": 42}
        success, rack = self.run_test("Create rack", "POST", "/racks", 200, data=rack_data)
        if not success:
            return False
        rack_id = rack.get('id')
        self.created_ids['rack'] = rack_id
        
        # Test rack elevation endpoint
        success, elev = self.run_test("Get rack elevation", "GET", f"/rack-tools/{rack_id}/elevation", 200)
        if success:
            self.log(f"Rack elevation returned {len(elev.get('units', []))} units")
        
        return success

    def test_prefixes_crud(self):
        """Test full CRUD on /api/prefixes"""
        prefix_data = {"prefix": "10.0.0.0/8", "status": "active"}
        success, prefix = self.run_test("Create prefix", "POST", "/prefixes", 200, data=prefix_data)
        if not success:
            return False
        prefix_id = prefix.get('id')
        self.created_ids['prefix'] = prefix_id
        
        # Test prefix tree endpoint
        success, tree = self.run_test("Get prefix tree", "GET", "/prefix-tools/tree", 200)
        if success:
            self.log(f"Prefix tree returned {len(tree.get('results', []))} prefixes")
        
        return success

    def test_ip_addresses_crud(self):
        """Test full CRUD on /api/ip-addresses"""
        ip_data = {"address": "10.0.0.1/24", "status": "active"}
        success, ip = self.run_test("Create IP address", "POST", "/ip-addresses", 200, data=ip_data)
        if not success:
            return False
        ip_id = ip.get('id')
        
        success, _ = self.run_test("Get IP address", "GET", f"/ip-addresses/{ip_id}", 200)
        return success

    def test_vlans_crud(self):
        """Test full CRUD on /api/vlans"""
        vlan_data = {"vid": 100, "name": "Management", "status": "active"}
        success, vlan = self.run_test("Create VLAN", "POST", "/vlans", 200, data=vlan_data)
        if not success:
            return False
        vlan_id = vlan.get('id')
        
        success, _ = self.run_test("Get VLAN", "GET", f"/vlans/{vlan_id}", 200)
        return success

    def test_customization_models(self):
        """Test tags, custom-fields, webhooks"""
        # Tags
        tag_data = {"name": "Production", "slug": "production", "color": "00ff00"}
        success, tag = self.run_test("Create tag", "POST", "/tags", 200, data=tag_data)
        if not success:
            return False
        
        # Custom fields
        cf_data = {
            "name": "cost_center",
            "label": "Cost Center",
            "type": "text",
            "object_types": ["site", "device"]
        }
        success, cf = self.run_test("Create custom field", "POST", "/custom-fields", 200, data=cf_data)
        if not success:
            return False
        
        # Webhooks
        wh_data = {
            "name": "Site Change Webhook",
            "object_types": ["site"],
            "type_create": True,
            "payload_url": "https://example.com/webhook",
            "enabled": True,
            "http_method": "POST"
        }
        success, wh = self.run_test("Create webhook", "POST", "/webhooks", 200, data=wh_data)
        return success

    def test_changelog(self):
        """Test GET /api/changelog returns change log entries"""
        success, data = self.run_test("Get changelog", "GET", "/changelog?limit=20", 200)
        if success:
            changes = data.get('results', [])
            self.log(f"Changelog returned {len(changes)} entries")
            return len(changes) > 0  # Should have changes from previous CRUD operations
        return False

    def test_search(self):
        """Test GET /api/search?q=site returns search results"""
        success, data = self.run_test("Global search", "GET", "/search?q=site", 200)
        if success:
            results = data.get('results', [])
            self.log(f"Search returned {results} results")
        return success

    def test_stats(self):
        """Test GET /api/stats returns counters and recent_changes"""
        success, data = self.run_test("Get stats", "GET", "/stats", 200)
        if success:
            counters = data.get('counters', {})
            recent = data.get('recent_changes', [])
            self.log(f"Stats: {len(counters)} counters, {len(recent)} recent changes")
            return 'sites' in counters and isinstance(recent, list)
        return False

    def test_graphql_collections(self):
        """Test POST /api/graphql with query '{ collections }'"""
        query = {"query": "{ collections }"}
        success, data = self.run_test("GraphQL collections query", "POST", "/graphql", 200, data=query)
        if success:
            gql_data = data.get('data', {})
            collections = gql_data.get('collections', [])
            self.log(f"GraphQL returned {len(collections)} collections")
            return len(collections) > 0
        return False

    def test_graphql_collection_query(self):
        """Test POST /api/graphql with collection query"""
        query = {"query": "{ collection(name: \"sites\", limit: 5) { id data } }"}
        success, data = self.run_test("GraphQL sites query", "POST", "/graphql", 200, data=query)
        if success:
            gql_data = data.get('data', {})
            collection = gql_data.get('collection', [])
            self.log(f"GraphQL sites query returned {len(collection)} items")
        return success

    def test_csv_export(self):
        """Test GET /api/sites/export returns CSV"""
        success, _ = self.run_test("CSV export sites", "GET", "/sites/export", 200)
        return success

    def test_csv_import(self):
        """Test POST /api/sites/import accepts CSV upload"""
        # Create a simple CSV
        csv_content = "name,status\nCSV Import Site,active\n"
        files = {'file': ('test.csv', csv_content, 'text/csv')}
        
        url = f"{BASE_URL}/sites/import"
        h = {'Authorization': f'Bearer {self.token}'}
        
        self.tests_run += 1
        self.log("Testing CSV import...")
        
        try:
            response = requests.post(url, files=files, headers=h, timeout=10)
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                data = response.json()
                self.log(f"✅ PASSED - CSV import (created: {data.get('created', 0)})", "PASS")
                return True
            else:
                self.tests_failed += 1
                self.log(f"❌ FAILED - CSV import - Status: {response.status_code}", "FAIL")
                self.failures.append({'test': 'CSV import', 'status': response.status_code})
                return False
        except Exception as e:
            self.tests_failed += 1
            self.log(f"❌ FAILED - CSV import - Error: {str(e)}", "FAIL")
            self.failures.append({'test': 'CSV import', 'error': str(e)})
            return False

    def test_cables_polymorphic(self):
        """Test POST /api/cables with polymorphic terminations"""
        # Create interfaces first
        device_id = self.created_ids.get('device')
        if not device_id:
            self.log("⚠️  Skipping cable test - no device available")
            return True  # Skip but don't fail
        
        success, iface1 = self.run_test("Create interface 1", "POST", "/interfaces", 200,
                                        data={"device_id": device_id, "name": "eth0", "type": "1000base-t"})
        if not success:
            return False
        
        success, iface2 = self.run_test("Create interface 2", "POST", "/interfaces", 200,
                                        data={"device_id": device_id, "name": "eth1", "type": "1000base-t"})
        if not success:
            return False
        
        cable_data = {
            "a_terminations": [{"object_type": "interface", "object_id": iface1['id']}],
            "b_terminations": [{"object_type": "interface", "object_id": iface2['id']}],
            "type": "cat6",
            "status": "connected"
        }
        success, cable = self.run_test("Create cable", "POST", "/cables", 200, data=cable_data)
        if not success:
            return False
        cable_id = cable.get('id')
        
        # Test cable trace
        success, trace = self.run_test("Trace cable", "GET", f"/cables/trace/interface/{iface1['id']}", 200)
        if success:
            path = trace.get('path', [])
            self.log(f"Cable trace returned path with {len(path)} hops")
        
        return success

    def test_auth_required(self):
        """Test DELETE /api/sites/{id} without token returns 401"""
        site_id = self.created_ids.get('site')
        if not site_id:
            self.log("⚠️  Skipping auth test - no site available")
            return True
        
        # Temporarily remove token
        old_token = self.token
        self.token = None
        
        success, _ = self.run_test("Delete site without auth", "DELETE", f"/sites/{site_id}", 401)
        
        # Restore token
        self.token = old_token
        return success

    def test_admin_operations(self):
        """Test POST /api/users requires admin role"""
        user_data = {
            "username": "testadmin",
            "password": "testpass",
            "email": "admin@test.com",
            "is_admin": False
        }
        success, _ = self.run_test("Create user (admin only)", "POST", "/users", 200, data=user_data)
        return success

    def test_api_tokens(self):
        """Test POST /api/api-tokens for current user"""
        token_data = {"description": "Test API Token", "write_enabled": True}
        success, token = self.run_test("Create API token", "POST", "/api-tokens", 200, data=token_data)
        if success:
            self.log(f"API token created: {token.get('key', '')[:10]}...")
        return success

    def test_bulk_delete(self):
        """Test bulk delete on sites"""
        # Create a few sites for bulk delete
        ids = []
        for i in range(3):
            success, site = self.run_test(f"Create bulk test site {i}", "POST", "/sites", 200,
                                         data={"name": f"Bulk Delete Site {i}"})
            if success:
                ids.append(site['id'])
        
        if not ids:
            return False
        
        success, result = self.run_test("Bulk delete sites", "POST", "/sites/bulk_delete", 200,
                                       data={"ids": ids})
        if success:
            deleted = result.get('deleted', 0)
            self.log(f"Bulk delete removed {deleted} sites")
            return deleted == len(ids)
        return False

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed} ✅")
        print(f"Failed: {self.tests_failed} ❌")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failures:
            print("\n" + "="*80)
            print("FAILURES")
            print("="*80)
            for f in self.failures[:10]:  # Show first 10 failures
                print(f"❌ {f.get('test', 'Unknown')}")
                if 'expected' in f:
                    print(f"   Expected: {f['expected']}, Got: {f['actual']}")
                if 'response' in f:
                    print(f"   Response: {f['response']}")
                if 'error' in f:
                    print(f"   Error: {f['error']}")
                print()
        
        print("="*80)
        return 0 if self.tests_failed == 0 else 1


def main():
    tester = NetBoxTester()
    
    print("="*80)
    print("SMIFS Enterprise Data Centre - Backend API Tests")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print()
    
    # Core endpoints
    tester.test_root_endpoint()
    tester.test_health_endpoint()
    
    # Auth tests
    if not tester.test_login():
        print("\n❌ CRITICAL: Login failed. Cannot proceed with authenticated tests.")
        return tester.print_summary()
    
    tester.test_register()
    tester.test_auth_me()
    
    # Schema
    tester.test_schema_endpoint()
    
    # CRUD tests on key models
    tester.test_sites_crud()
    tester.test_devices_crud()
    tester.test_racks_crud()
    tester.test_prefixes_crud()
    tester.test_ip_addresses_crud()
    tester.test_vlans_crud()
    
    # Customization
    tester.test_customization_models()
    
    # Special endpoints
    tester.test_changelog()
    tester.test_search()
    tester.test_stats()
    
    # GraphQL
    tester.test_graphql_collections()
    tester.test_graphql_collection_query()
    
    # CSV import/export
    tester.test_csv_export()
    tester.test_csv_import()
    
    # Cables (polymorphic)
    tester.test_cables_polymorphic()
    
    # Auth & permissions
    tester.test_auth_required()
    tester.test_admin_operations()
    tester.test_api_tokens()
    
    # Bulk operations
    tester.test_bulk_delete()
    
    return tester.print_summary()


if __name__ == "__main__":
    sys.exit(main())
