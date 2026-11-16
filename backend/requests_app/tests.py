
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from .models import Category, ServiceRequest


User = get_user_model()


class ServiceRequestExtensionTests(TestCase):

    def setUp(self):
        self.requester = User.objects.create_user(
            username="test_requester",
            password="test_password_123",
        )

        self.category = Category.objects.create(
            name="Test Electrical",
            description="Testing electrical requests",
        )

    def create_request(self, **overrides):
        data = {
            "requester": self.requester,
            "category": self.category,
            "title": "Test service request",
            "description": "Testing service request validation",
            "location": "Test Laboratory",
            "priority": 2,
            "status": ServiceRequest.Status.OPEN,
        }

        data.update(overrides)

        return ServiceRequest(**data)

    def test_due_at_can_be_empty(self):
        request = self.create_request(due_at=None)
        request.full_clean()

        self.assertIsNone(request.due_at)

    def test_resolved_request_requires_resolution_date(self):
        request = self.create_request(
            status=ServiceRequest.Status.RESOLVED,
            resolution_summary="Repair completed successfully.",
        )

        with self.assertRaises(ValidationError):
            request.full_clean()

    def test_resolved_request_requires_resolution_summary(self):
        request = self.create_request(
            status=ServiceRequest.Status.RESOLVED,
            resolved_at=timezone.now(),
        )

        with self.assertRaises(ValidationError):
            request.full_clean()

    def test_closed_request_requires_resolution_details(self):
        request = self.create_request(
            status=ServiceRequest.Status.CLOSED,
        )

        with self.assertRaises(ValidationError):
            request.full_clean()

    def test_valid_resolved_request_passes_validation(self):
        request = self.create_request(
            status=ServiceRequest.Status.RESOLVED,
            resolved_at=timezone.now(),
            resolution_summary="The faulty socket was repaired.",
        )

        request.full_clean()

        self.assertEqual(
            request.status,
            ServiceRequest.Status.RESOLVED,
        )

    def test_due_date_can_be_set_in_the_future(self):
        
        future_date = timezone.now() + timedelta(days=7)

        request = self.create_request(due_at=future_date)
        request.full_clean()

        self.assertEqual(request.due_at, future_date)
