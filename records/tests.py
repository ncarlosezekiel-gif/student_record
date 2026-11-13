from datetime import date

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from academics.models import AcademicYear, Course, Enrollment, Semester
from .models import AuditLog, Student


class StudentRecordTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="registrar",
            password="test-password-123",
            role=get_user_model().Role.REGISTRAR,
        )
        self.student = Student.objects.create(
            first_name="Ari",
            last_name="Santos",
            date_of_birth=date(2008, 1, 15),
            gender=Student.Gender.FEMALE,
            address="School Road",
            email="ari.santos@example.com",
        )

    def test_student_id_is_generated_and_unique(self):
        second = Student.objects.create(
            first_name="Sam",
            last_name="Reyes",
            date_of_birth=date(2007, 5, 2),
            gender=Student.Gender.MALE,
            address="North Street",
        )
        self.assertTrue(self.student.student_id.startswith("SR"))
        self.assertNotEqual(self.student.student_id, second.student_id)

    def test_system_administrator_role_enables_admin_site_access(self):
        admin_user = get_user_model().objects.create_user(
            username="sysadmin",
            password="test-password-123",
            role=get_user_model().Role.ADMIN,
        )
        self.assertTrue(admin_user.is_staff)
        self.client.force_login(admin_user)
        self.assertEqual(self.client.get("/admin/").status_code, 200)

    def test_registrar_can_search_and_open_student_records(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("student_list"), {"q": self.student.student_id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.student.student_id)
        self.assertEqual(self.client.get(reverse("student_detail", args=[self.student.pk])).status_code, 200)

    def test_report_center_and_exports(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("report_center")).status_code, 200)
        for export_format, content_type in (
            ("csv", "text/csv"),
            ("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            ("pdf", "application/pdf"),
        ):
            response = self.client.get(reverse("report_export"), {"report": "students", "format": export_format})
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response["Content-Type"].startswith(content_type))

    def test_database_health_endpoint(self):
        response = self.client.get(reverse("health_check"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_student_can_create_account_with_matching_student_record(self):
        response = self.client.post(reverse("register_student_account"), {
            "student_id": self.student.student_id.lower(),
            "email": "ARI.SANTOS@example.com",
            "password1": "A-strong-example-password-92!",
            "password2": "A-strong-example-password-92!",
        })
        self.assertRedirects(response, reverse("login"))
        user = get_user_model().objects.get(email="ari.santos@example.com")
        self.student.refresh_from_db()
        self.assertEqual(user.role, get_user_model().Role.STUDENT)
        self.assertTrue(user.check_password("A-strong-example-password-92!"))
        self.assertEqual(self.student.user, user)
        self.assertTrue(self.client.login(username=user.username, password="A-strong-example-password-92!"))

    def test_account_creation_rejects_unmatched_student_details(self):
        response = self.client.post(reverse("register_student_account"), {
            "student_id": self.student.student_id,
            "email": "someone-else@example.com",
            "password1": "A-strong-example-password-92!",
            "password2": "A-strong-example-password-92!",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(get_user_model().objects.filter(role=get_user_model().Role.STUDENT).exists())
        self.assertIsNone(self.student.user)

    def test_account_creation_rejects_password_mismatch(self):
        response = self.client.post(reverse("register_student_account"), {
            "student_id": self.student.student_id,
            "email": self.student.email,
            "password1": "A-strong-example-password-92!",
            "password2": "A-different-example-password-92!",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(get_user_model().objects.filter(role=get_user_model().Role.STUDENT).exists())

    def test_login_and_logout_are_audited(self):
        self.assertTrue(self.client.login(username="registrar", password="test-password-123"))
        self.client.post(reverse("logout"))
        self.assertEqual(
            list(AuditLog.objects.order_by("created_at").values_list("action", flat=True)),
            ["LOGIN", "LOGOUT"],
        )

    def test_registrar_can_create_student_with_guardian(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("student_create"), {
            "first_name": "Mia",
            "last_name": "Rivera",
            "date_of_birth": "2008-07-14",
            "gender": Student.Gender.FEMALE,
            "address": "Central District",
            "status": Student.Status.ACTIVE,
            "guardians-TOTAL_FORMS": "1",
            "guardians-INITIAL_FORMS": "0",
            "guardians-MIN_NUM_FORMS": "0",
            "guardians-MAX_NUM_FORMS": "1000",
            "guardians-0-name": "Pat Rivera",
            "guardians-0-relationship": "Parent",
            "guardians-0-contact_number": "09123456789",
            "guardians-0-email": "pat@example.com",
            "guardians-0-address": "Central District",
        })
        self.assertEqual(response.status_code, 302)
        created = Student.objects.get(first_name="Mia")
        self.assertEqual(created.guardians.get().name, "Pat Rivera")

    def test_student_role_can_open_only_linked_personal_record(self):
        user_model = get_user_model()
        student_user = user_model.objects.create_user(username="learner", password="test-password-123", role=user_model.Role.STUDENT)
        self.student.user = student_user
        self.student.save()
        other = Student.objects.create(
            first_name="Lee",
            last_name="Cruz",
            date_of_birth=date(2008, 6, 8),
            gender=Student.Gender.OTHER,
            address="East Road",
        )
        self.client.force_login(student_user)
        self.assertEqual(self.client.get(reverse("student_detail", args=[self.student.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("student_detail", args=[other.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse("student_list")).status_code, 403)


class EnrollmentConstraintTests(TestCase):
    def test_duplicate_enrollment_period_is_rejected(self):
        student = Student.objects.create(
            first_name="Noah",
            last_name="Garcia",
            date_of_birth=date(2009, 3, 10),
            gender=Student.Gender.MALE,
            address="West Avenue",
        )
        year = AcademicYear.objects.create(name="2026-2027", start_date=date(2026, 6, 1), end_date=date(2027, 3, 31))
        semester = Semester.objects.create(academic_year=year, name="First", start_date=date(2026, 6, 1), end_date=date(2026, 10, 31))
        course = Course.objects.create(code="BSIT", name="Information Technology")
        Enrollment.objects.create(student=student, academic_year=year, semester=semester, course=course, year_level="1", status=Enrollment.Status.ENROLLED)
        with self.assertRaises(IntegrityError):
            Enrollment.objects.create(student=student, academic_year=year, semester=semester, course=course, year_level="1")
