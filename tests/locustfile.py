"""
=============================================================================
LOCUST STRESS TEST — Web1 Activity Management System
=============================================================================
INSTALL:
    pip install locust

RUN (Web UI — open http://localhost:8089 in browser):
    locust -f tests/locustfile.py --host=http://localhost:5000

RUN (Headless / command-line only):
    locust -f tests/locustfile.py --host=http://localhost:5000 ^
           --headless -u 100 -r 10 --run-time 2m

FLAGS:
  -u  : total number of simulated users (e.g. -u 200)
  -r  : users spawned per second (e.g. -r 20)
  --run-time : how long to run  (e.g. 1m, 2m30s, 1h)

WHAT THIS TESTS:
  - StudentUser  : student roll-number login + profile fetch + view activities
  - StaffUser    : email/password login (HOD / Coordinator / Creator) + dashboard
  - GuestUser    : unauthenticated browsing (homepage, static assets, event list)

RESULTS:
  - Web UI shows real-time RPS, P50/P95/P99 latency, failures, charts
  - Press CTRL-C to stop; a final summary CSV is printed
=============================================================================
"""

import random
import string
from locust import HttpUser, task, between, events
from locust.exception import StopUser


# ---------------------------------------------------------------------------
# Shared sample data  (edit to match real data in your DB)
# ---------------------------------------------------------------------------

# Real roll numbers from your students table
STUDENT_ROLL_NUMBERS = [
    "241101p",
    "241102p",
    "241103p",
    "241104p",
    "241105p",
    "241106p",
    "241107p",
    "241108p",
    "241109p",
    "241110p",
    "241111p",
    "241112p",
    "241113p",
    "241114p",
    "241115p",
]

# Real staff accounts from your database
STAFF_ACCOUNTS = [
    {"email": "admin@pbsiddhartha.ac.in",  "password": "admin123"},   # CREATOR
    {"email": "hod@pbsiddhartha.ac.in",    "password": "hod123"},     # HOD
    {"email": "ruhi@pbsiddhartha.ac.in",   "password": "ruhi123"},    # COORDINATOR
]

# Activity names to browse
ACTIVITY_NAMES = ["NCC", "NSS", "SPORTS", "CULTURALS"]


def random_roll():
    """Return a random roll number from the sample list."""
    return random.choice(STUDENT_ROLL_NUMBERS)


def random_staff():
    """Return a random staff credential dict."""
    return random.choice(STAFF_ACCOUNTS)


# ===========================================================================
# USER TYPE 1 — STUDENT
# Simulates a student: look up roll number → view profile → browse activities
# ===========================================================================
class StudentUser(HttpUser):
    """Represents a student logging in and browsing."""
    weight = 6          # 60% of simulated users will be students
    wait_time = between(1, 4)   # think time between requests (seconds)

    def on_start(self):
        """Called once when a simulated user starts. Perform login."""
        self.roll = random_roll()
        self.logged_in = False
        self._student_login()

    def _student_login(self):
        with self.client.post(
            "/api/auth/student",
            json={"rollNumber": self.roll},
            name="/api/auth/student  [LOGIN]",
            catch_response=True
        ) as resp:
            if resp.status_code == 200:
                self.logged_in = True
                resp.success()
            elif resp.status_code == 404:
                # Roll number not in DB — mark as failure but keep running
                resp.failure(f"Roll {self.roll} not found — update STUDENT_ROLL_NUMBERS in locustfile.py")
                self.logged_in = False  # will skip auth-required tasks
            else:
                resp.failure(f"Login failed: {resp.status_code} {resp.text[:120]}")
                self.logged_in = False

    # ---- Tasks (weighted) --------------------------------------------------

    @task(3)
    def view_my_profile(self):
        """Fetch student profile — most common action."""
        if not self.logged_in:
            self.load_student_login_page()
            return
        self.client.get(
            f"/api/student/profile/{self.roll}",
            name="/api/student/profile/[roll]"
        )

    @task(2)
    def view_my_events(self):
        """Check which events I'm registered in."""
        if not self.logged_in:
            return
        self.client.get(
            f"/api/student/{self.roll}/application-status",
            name="/api/student/[roll]/application-status"
        )

    @task(2)
    def browse_activity_list(self):
        """Browse the full activity listing."""
        self.client.get(
            "/api/activity-summary",
            name="/api/activity-summary  [LIST]"
        )

    @task(1)
    def view_activity_details(self):
        """View a specific activity's details."""
        activity = random.choice(ACTIVITY_NAMES)
        self.client.get(
            f"/api/activity-lead/{activity}",
            name="/api/activity-lead/[name]"
        )

    @task(1)
    def check_attendance(self):
        """Check personal attendance records."""
        if not self.logged_in:
            return
        self.client.get(
            f"/api/attendance/student/{self.roll}",
            name="/api/attendance/student/[roll]"
        )

    @task(1)
    def check_can_apply(self):
        """Check eligibility to apply for an activity."""
        if not self.logged_in:
            return
        self.client.get(
            f"/api/student/{self.roll}/can-apply",
            name="/api/student/[roll]/can-apply"
        )

    @task(1)
    def load_student_login_page(self):
        """Load the student login page (works without auth)."""
        self.client.get(
            "/pages/login/student-login.html",
            name="/pages/login/student-login.html"
        )


# ===========================================================================
# USER TYPE 2 — STAFF  (HOD / Coordinator / Creator)
# Simulates a staff member logging in and using the dashboard
# ===========================================================================
class StaffUser(HttpUser):
    """Represents HOD / Coordinator / Creator."""
    weight = 2          # 20% of simulated users are staff
    wait_time = between(2, 6)

    def on_start(self):
        self.credentials = random_staff()
        self.logged_in = False
        self.role = None
        self._staff_login()

    def _staff_login(self):
        with self.client.post(
            "/api/auth/login",
            json=self.credentials,
            name="/api/auth/login  [STAFF LOGIN]",
            catch_response=True
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                self.role = data.get("user", {}).get("role", "UNKNOWN")
                self.logged_in = True
                resp.success()
            else:
                resp.failure(f"Staff login failed — update STAFF_ACCOUNTS in locustfile.py: {resp.status_code} {resp.text[:120]}")
                self.logged_in = False  # keep running with public-only tasks

    # ---- Tasks -------------------------------------------------------------

    @task(3)
    def view_student_list(self):
        """List all students (common HOD task)."""
        if not self.logged_in:
            self.load_login_page()
            return
        self.client.get(
            "/api/student-profiles",
            name="/api/student-profiles  [LIST]"
        )

    @task(2)
    def view_activity_summary(self):
        """View activity summary for dashboard."""
        self.client.get(
            "/api/activity-summary",
            name="/api/activity-summary  [STAFF]"
        )

    @task(2)
    def view_activity_members(self):
        """Check activity member enrollment."""
        if not self.logged_in:
            return
        self.client.get(
            "/api/activity-members",
            name="/api/activity-members"
        )

    @task(1)
    def view_students_by_activity(self):
        """Filter students by activity."""
        if not self.logged_in:
            return
        activity = random.choice(ACTIVITY_NAMES)
        self.client.get(
            f"/api/students/by-activity?activity={activity}",
            name="/api/students/by-activity?activity=[name]"
        )

    @task(1)
    def view_analytics(self):
        """View activity analytics."""
        activity = random.choice(ACTIVITY_NAMES)
        self.client.get(
            f"/api/analytics/activity/{activity}",
            name="/api/analytics/activity/[name]"
        )

    @task(1)
    def load_login_page(self):
        """Load the staff login page."""
        self.client.get(
            "/pages/login/admin-auth.html",
            name="/pages/login/admin-auth.html"
        )


# ===========================================================================
# USER TYPE 3 — GUEST  (unauthenticated)
# Simulates someone visiting the site without logging in
# ===========================================================================
class GuestUser(HttpUser):
    """Represents a visitor who hasn't logged in yet."""
    weight = 2          # 20% of simulated users are guests
    wait_time = between(1, 3)

    @task(5)
    def load_homepage(self):
        """Load the main index page."""
        self.client.get("/", name="/ [Homepage]")

    @task(2)
    def load_login_page(self):
        """View the login page."""
        self.client.get("/pages/login/student-login.html", name="/pages/login/student-login.html")

    @task(1)
    def load_student_login_page(self):
        """View the student panel page."""
        self.client.get("/pages/student/student-panel.html", name="/pages/student/student-panel.html")

    @task(1)
    def load_js_bundle(self):
        """Load main JS bundle (app-all.js) — tests static file serving."""
        self.client.get("/js/app-all.js", name="/js/app-all.js  [STATIC]")


# ===========================================================================
# EVENT HOOKS — print a summary line when the test ends
# ===========================================================================
@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    stats = environment.stats
    total = stats.total
    print("\n" + "=" * 70)
    print("STRESS TEST COMPLETE — SUMMARY")
    print("=" * 70)
    print(f"  Total requests  : {total.num_requests}")
    print(f"  Failures        : {total.num_failures}")
    print(f"  Fail rate       : {total.fail_ratio * 100:.1f}%")
    print(f"  Avg response    : {total.avg_response_time:.0f} ms")
    print(f"  Max response    : {total.max_response_time:.0f} ms")
    print(f"  P95 response    : {total.get_response_time_percentile(0.95):.0f} ms")
    print(f"  Req/s (peak)    : {total.current_rps:.1f}")
    print("=" * 70)
    if total.fail_ratio > 0.05:
        print("⚠  WARNING: Failure rate > 5% — server may be struggling")
    elif total.avg_response_time > 2000:
        print("⚠  WARNING: Average response > 2s — server is slow under load")
    else:
        print("✓  All good — failure rate and response times look acceptable")
    print("=" * 70 + "\n")
