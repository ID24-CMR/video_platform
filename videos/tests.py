from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.test import TestCase

from .models import Category, Video


class CategoryModelTests(TestCase):
    def test_category_creation(self):
        category = Category.objects.create(
            name="Technology"
        )

        self.assertEqual(category.name, "Technology")


class VideoModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Technology"
        )

    def test_free_video_creation(self):
        video = Video.objects.create(
            title="Python Tutorial",
            category=self.category,
            access_type="free",
            price=0,
        )

        self.assertEqual(video.access_type, "free")
        self.assertEqual(video.price, 0)

    def test_paid_video_creation(self):
        video = Video.objects.create(
            title="Advanced Python",
            category=self.category,
            access_type="paid",
            price=10,
        )

        self.assertEqual(video.access_type, "paid")
        self.assertEqual(video.price, 10)

class PublicVideoViewTests(TestCase):

    def test_public_library_loads(self):
        response = self.client.get(reverse("videos:public_library"))

        self.assertEqual(response.status_code, 200)

    def test_video_detail_returns_404_for_invalid_id(self):
        response = self.client.get(
            reverse("videos:video_detail", args=[99999])
        )

        self.assertEqual(response.status_code, 404)


class AuthenticationViewTests(TestCase):

    def test_registration_page_loads(self):
        response = self.client.get(reverse("videos:register"))

        self.assertEqual(response.status_code, 200)

    def test_login_page_loads(self):
        response = self.client.get(reverse("videos:login"))

        self.assertEqual(response.status_code, 200)

    def test_account_requires_authentication(self):
        response = self.client.get(reverse("videos:account"))

        self.assertNotEqual(response.status_code, 200)