#!/usr/bin/env python3
"""
Comprehensive test suite for abuse protection features.
Run this script to verify all protection systems are working correctly.
"""
from recipe_parser import app, db
from models import ApiUsage, RateLimit
from protection import record_api_usage, check_daily_budget
from datetime import date
from decimal import Decimal
import time


def test_rate_limiting():
    """Test that rate limiting works after 20 requests"""
    print("\n" + "=" * 70)
    print("TEST 1: RATE LIMITING (20 requests/hour per IP)")
    print("=" * 70)

    with app.test_client() as client:
        # Make 22 requests to test the limit
        for i in range(1, 23):
            response = client.post('/parse', data={
                'recipe_url': 'https://example.com/fake-recipe'
            }, headers={
                'X-Forwarded-For': '192.0.2.100'  # Test IP
            })

            if response.status_code == 429:
                print(f"✅ Rate limit kicked in at request {i} (after {i-1} successful)")
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    print(f"   Retry-After header: {retry_after} seconds")
                return True
            elif i <= 20 and response.status_code != 200:
                print(f"❌ Unexpected status {response.status_code} at request {i}")
                return False

            if i % 5 == 0:
                print(f"   Requests 1-{i}: OK")

            time.sleep(0.05)  # Small delay

    print("❌ Did not hit rate limit after 22 requests")
    return False


def test_ssrf_protection():
    """Test that SSRF protection blocks dangerous URLs"""
    print("\n" + "=" * 70)
    print("TEST 2: SSRF PROTECTION")
    print("=" * 70)

    # URLs that should be blocked
    blocked_urls = [
        ('http://localhost/admin', 'localhost'),
        ('http://127.0.0.1/secrets', '127.0.0.1'),
        ('http://192.168.1.1/router', 'private IP 192.168.x.x'),
        ('http://10.0.0.1/internal', 'private IP 10.x.x.x'),
        ('http://172.16.0.1/private', 'private IP 172.16.x.x'),
        ('http://169.254.169.254/metadata', 'metadata endpoint'),
    ]

    # URLs that should be allowed
    allowed_urls = [
        'https://www.allrecipes.com/recipe/123',
        'https://www.foodnetwork.com/recipes',
    ]

    with app.test_client() as client:
        print("\nBlocking dangerous URLs:")
        blocked_count = 0
        for url, description in blocked_urls:
            response = client.post('/parse', data={'recipe_url': url}, headers={
                'X-Forwarded-For': '203.0.113.100'  # Different test IP
            })

            is_blocked = b'security' in response.data.lower() or b'not allowed' in response.data.lower()
            status = "✅" if is_blocked else "❌"
            print(f"  {status} {description:25s} - {'BLOCKED' if is_blocked else 'ALLOWED (FAIL)'}")

            if is_blocked:
                blocked_count += 1

        print(f"\nAllowing legitimate URLs:")
        allowed_count = 0
        for url in allowed_urls:
            response = client.post('/parse', data={'recipe_url': url}, headers={
                'X-Forwarded-For': '203.0.113.101'
            })

            is_ssrf_error = b'Private IP' in response.data or b'Localhost' in response.data
            status = "✅" if not is_ssrf_error else "❌"
            domain = url.split('/')[2]
            print(f"  {status} {domain:25s} - {'ALLOWED' if not is_ssrf_error else 'BLOCKED (FAIL)'}")

            if not is_ssrf_error:
                allowed_count += 1

        success = (blocked_count == len(blocked_urls) and allowed_count == len(allowed_urls))
        if success:
            print(f"\n✅ SSRF test passed: {blocked_count}/{len(blocked_urls)} blocked, {allowed_count}/{len(allowed_urls)} allowed")
        else:
            print(f"\n❌ SSRF test failed")

        return success


def test_budget_controls():
    """Test that budget controls work correctly"""
    print("\n" + "=" * 70)
    print("TEST 3: BUDGET CONTROLS")
    print("=" * 70)

    with app.app_context():
        daily_budget = app.config.get('DAILY_BUDGET_USD', 5.00)
        cost_per_request = app.config.get('COST_PER_REQUEST', 0.0015)

        print(f"Configuration: ${daily_budget:.2f}/day, ${cost_per_request:.4f}/request\n")

        # Get current usage
        today = date.today()
        today_usage = ApiUsage.query.filter_by(date=today).first()

        if today_usage:
            current_cost = float(today_usage.estimated_cost)
            current_count = today_usage.request_count
            print(f"Current usage: {current_count} requests, ${current_cost:.4f}")
        else:
            print("No usage recorded yet today")
            current_cost = 0
            current_count = 0

        # Test recording API usage
        print("\nRecording 3 test API calls...")
        for i in range(3):
            record_api_usage()

        # Check updated usage
        today_usage = ApiUsage.query.filter_by(date=today).first()
        new_cost = float(today_usage.estimated_cost)
        new_count = today_usage.request_count

        print(f"Updated usage: {new_count} requests (+{new_count - current_count}), ${new_cost:.4f} (+${new_cost - current_cost:.4f})")

        # Test budget limit detection
        original_cost = today_usage.estimated_cost
        today_usage.estimated_cost = Decimal(str(daily_budget + 1.0))
        db.session.commit()

        budget_ok, budget_msg = check_daily_budget()

        if not budget_ok:
            print(f"✅ Budget limit correctly detected when exceeded")
        else:
            print(f"❌ Budget limit not detected (should be exceeded)")
            return False

        # Restore original cost
        today_usage.estimated_cost = original_cost
        db.session.commit()

        # Calculate remaining budget
        remaining = daily_budget - float(original_cost)
        requests_left = int(remaining / cost_per_request)
        print(f"\nBudget status: ${float(original_cost):.4f} / ${daily_budget:.2f} ({requests_left} requests remaining)")

        return True


def test_admin_dashboard():
    """Test that admin dashboard renders correctly"""
    print("\n" + "=" * 70)
    print("TEST 4: ADMIN DASHBOARD")
    print("=" * 70)

    with app.test_client() as client:
        response = client.get('/admin/usage')

        if response.status_code != 200:
            print(f"❌ Dashboard failed to load: {response.status_code}")
            return False

        # Check for key elements
        checks = [
            (b'API Usage Dashboard', 'Dashboard title'),
            (b'Daily Budget', 'Budget section'),
            (b'Requests Today', 'Request count'),
            (b'Active Users', 'Active users'),
            (b'Last 7 Days', 'History table'),
            (b'SSRF Protection', 'Security status'),
        ]

        all_found = True
        for check_bytes, description in checks:
            found = check_bytes in response.data
            status = "✅" if found else "❌"
            print(f"  {status} {description}")
            if not found:
                all_found = False

        return all_found


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("ABUSE PROTECTION TEST SUITE")
    print("=" * 70)
    print("Testing all protection features...")

    results = {
        'Rate Limiting': test_rate_limiting(),
        'SSRF Protection': test_ssrf_protection(),
        'Budget Controls': test_budget_controls(),
        'Admin Dashboard': test_admin_dashboard(),
    }

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:20s} {status}")
        if not passed:
            all_passed = False

    print("=" * 70)

    if all_passed:
        print("✅ ALL TESTS PASSED - Protection systems working correctly!")
        return 0
    else:
        print("❌ SOME TESTS FAILED - Please review output above")
        return 1


if __name__ == '__main__':
    exit(main())
