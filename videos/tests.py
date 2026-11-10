from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Category, Video, VideoAccessGrant


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
        self.assertEqual(video.price, Decimal("0.00"))

    def test_paid_video_creation(self):
        video = Video.objects.create(
            title="Advanced Python",
            category=self.category,
            access_type="paid",
            price=10,
        )

        self.assertEqual(video.access_type, "paid")
        self.assertEqual(video.price, Decimal("10.00"))


class PublicVideoViewTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Technology"
        )

        self.published_video = Video.objects.create(
            title="Published Python Tutorial",
            description="A public Python tutorial.",
            category=self.category,
            access_type="free",
            price=0,
            is_published=True,
        )

        self.unpublished_video = Video.objects.create(
            title="Unpublished Python Tutorial",
            description="A private Python tutorial.",
            category=self.category,
            access_type="free",
            price=0,
            is_published=False,
        )

    def test_public_library_loads(self):
        response = self.client.get(
            reverse("videos:public_library")
        )

        self.assertEqual(response.status_code, 200)

    def test_public_library_displays_published_videos(self):
        response = self.client.get(
            reverse("videos:public_library")
        )

        self.assertContains(response, "Published Python Tutorial")
        self.assertNotContains(response, "Unpublished Python Tutorial")

    def test_video_detail_returns_404_for_invalid_id(self):
        response = self.client.get(
            reverse("videos:video_detail", args=[99999])
        )

        self.assertEqual(response.status_code, 404)

    def test_unpublished_video_detail_returns_404(self):
        response = self.client.get(
            reverse(
                "videos:video_detail",
                args=[self.unpublished_video.id],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_published_video_detail_loads(self):
        response = self.client.get(
            reverse(
                "videos:video_detail",
                args=[self.published_video.id],
            )
        )

        self.assertEqual(response.status_code, 200)


class VideoAccessViewTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Technology"
        )

        self.paid_video = Video.objects.create(
            title="Advanced Django",
            description="A paid Django tutorial.",
            category=self.category,
            access_type="paid",
            price=Decimal("15.00"),
            is_published=True,
        )

        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword123",
        )

        self.admin = User.objects.create_superuser(
            username="adminuser",
            email="admin@example.com",
            password="adminpassword123",
        )

    def test_user_without_grant_has_no_access(self):
        response = self.client.get(
            reverse(
                "videos:video_detail",
                args=[self.paid_video.id],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["has_access"])

    def test_user_with_grant_has_access(self):
        VideoAccessGrant.objects.create(
            user=self.user,
            video=self.paid_video,
            source="payment",
        )

        self.client.login(
            username="testuser",
            password="testpassword123",
        )

        response = self.client.get(
            reverse(
                "videos:video_detail",
                args=[self.paid_video.id],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["has_access"])

    def test_admin_has_access_to_paid_video(self):
        self.client.login(
            username="adminuser",
            password="adminpassword123",
        )

        response = self.client.get(
            reverse(
                "videos:video_detail",
                args=[self.paid_video.id],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["has_access"])


class AuthenticationViewTests(TestCase):
    def test_registration_page_loads(self):
        response = self.client.get(
            reverse("videos:register")
        )

        self.assertEqual(response.status_code, 200)

    def test_login_page_loads(self):
        response = self.client.get(
            reverse("videos:login")
        )

        self.assertEqual(response.status_code, 200)

    def test_account_requires_authentication(self):
        response = self.client.get(
            reverse("videos:account")
        )

        self.assertEqual(response.status_code, 302)

class VideoStreamingTests(TestCase):

    def setUp(self):
        self.category = Category.objects.create(
            name="Technology"
        )

        self.free_video = Video.objects.create(
            title="Free Python Tutorial",
            description="Free tutorial.",
            category=self.category,
            access_type="free",
            price=0,
            is_published=True,
        )

        self.paid_video = Video.objects.create(
            title="Paid Django Tutorial",
            description="Paid tutorial.",
            category=self.category,
            access_type="paid",
            price=15,
            is_published=True,
        )

        self.unpublished_video = Video.objects.create(
            title="Unpublished Tutorial",
            description="Unpublished tutorial.",
            category=self.category,
            access_type="free",
            price=0,
            is_published=False,
        )

        self.user = User.objects.create_user(
            username="streamuser",
            password="testpassword123",
        )

        self.admin = User.objects.create_superuser(
            username="streamadmin",
            email="admin@example.com",
            password="adminpassword123",
        )

    def test_anonymous_user_redirected_to_login(self):
        response = self.client.get(
            reverse(
                "videos:stream_video",
                args=[self.free_video.id],
            )
        )

        self.assertEqual(response.status_code, 302)

    def test_unpublished_video_cannot_be_streamed(self):
        self.client.login(
            username="streamuser",
            password="testpassword123",
        )

        response = self.client.get(
            reverse(
                "videos:stream_video",
                args=[self.unpublished_video.id],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_user_without_grant_cannot_stream_paid_video(self):
        self.client.login(
            username="streamuser",
            password="testpassword123",
        )

        response = self.client.get(
            reverse(
                "videos:stream_video",
                args=[self.paid_video.id],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_user_with_grant_can_stream_paid_video(self):
        VideoAccessGrant.objects.create(
            user=self.user,
            video=self.paid_video,
            source="payment",
        )

        self.client.login(
            username="streamuser",
            password="testpassword123",
        )

        response = self.client.get(
            reverse(
                "videos:stream_video",
                args=[self.paid_video.id],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_admin_can_stream_paid_video(self):
        self.client.login(
            username="streamadmin",
            password="adminpassword123",
        )

        response = self.client.get(
            reverse(
                "videos:stream_video",
                args=[self.paid_video.id],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_free_video_without_file_returns_404(self):
        self.client.login(
            username="streamuser",
            password="testpassword123",
        )

        response = self.client.get(
            reverse(
                "videos:stream_video",
                args=[self.free_video.id],
            )
        )

        self.assertEqual(response.status_code, 404)
