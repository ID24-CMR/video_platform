from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from config import settings

from .models import Category, Video, VideoAccessGrant, Purchase, ProcessedStripeEvent
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch

import stripe


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

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_fake",
        STRIPE_CURRENCY="cad",
        )
    @patch("videos.views.stripe.checkout.Session.create")
    def test_user_can_create_checkout_session(self, mock_stripe):
        mock_stripe.return_value.id = "cs_test_123"
        mock_stripe.return_value.url = "https://checkout.stripe.com/test"

        self.client.login(
            username="testuser",
            password="testpassword123",
        )

        response = self.client.post(
            reverse(
                "videos:create_checkout_session",
                args=[self.paid_video.id],
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            "https://checkout.stripe.com/test",
        )

        purchase = Purchase.objects.get(user=self.user)

        self.assertEqual(purchase.status, Purchase.Status.PENDING)
        self.assertEqual(purchase.amount, Decimal("15.00"))
        self.assertEqual(purchase.currency, "cad")
        self.assertEqual(
            purchase.stripe_checkout_session_id,
            "cs_test_123",
        )

        mock_stripe.assert_called_once()

    @patch("videos.views.settings.STRIPE_SECRET_KEY", "")
    @patch("videos.views.settings.STRIPE_CURRENCY", "cad")
    def test_checkout_fails_when_stripe_is_not_configured(self):
        self.client.login(
            username="testuser",
            password="testpassword123",
        )

        response = self.client.post(
            reverse(
                "videos:create_checkout_session",
                args=[self.paid_video.id],
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Purchase.objects.count(), 0)
        # self.assertEqual(
        #     Purchase.objects.count(),
        #     0,
        #     msg=(
        #         f"DEBUG: "
        #         f"Stripe key={repr(settings.STRIPE_SECRET_KEY)}, "
        #         f"Response status={response.status_code}, "
        #         f"Response URL={response.url}, "
        #         f"Purchase count={Purchase.objects.count()}"
        #     ),
        # )

    @patch("videos.views.settings.STRIPE_SECRET_KEY", "sk_test_fake")
    @patch("videos.views.settings.STRIPE_CURRENCY", "usd")
    def test_user_cannot_purchase_video_twice(self):
        VideoAccessGrant.objects.create(
            user=self.user,
            video=self.paid_video,
            source="payment",
        )

        self.client.login(
            username="testuser",
            password="testpassword123",
        )

        response = self.client.post(
            reverse(
                "videos:create_checkout_session",
                args=[self.paid_video.id],
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Purchase.objects.count(), 0)
        

    @override_settings(STRIPE_SECRET_KEY="sk_test_fake",STRIPE_CURRENCY="cad",)
    @patch("videos.views.stripe.checkout.Session.create")
    def test_stripe_failure_marks_purchase_as_failed(self, mock_stripe):
        mock_stripe.side_effect = stripe.StripeError(
            "Stripe service unavailable"
        )

        self.client.login(
            username="testuser",
            password="testpassword123",
        )

        response = self.client.post(
            reverse(
                "videos:create_checkout_session",
                args=[self.paid_video.id],
            )
        )

        self.assertEqual(response.status_code, 302)

        purchase = Purchase.objects.get(user=self.user)

        self.assertEqual(purchase.status, Purchase.Status.FAILED)

    def test_anonymous_user_cannot_start_checkout(self):
        response = self.client.post(
            reverse(
                "videos:create_checkout_session",
                args=[self.paid_video.id],
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)
        self.assertEqual(Purchase.objects.count(), 0)

    def test_checkout_requires_post(self):
        self.client.login(
            username="testuser",
            password="testpassword123",
        )

        response = self.client.get(
            reverse(
                "videos:create_checkout_session",
                args=[self.paid_video.id],
            )
        )

        self.assertEqual(response.status_code, 405)

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_fake",
        STRIPE_CURRENCY="cad",
    )
    def test_checkout_returns_404_for_unpublished_video(self):
        self.paid_video.is_published = False
        self.paid_video.save()

        self.client.login(
            username="testuser",
            password="testpassword123",
        )

        response = self.client.post(
            reverse(
                "videos:create_checkout_session",
                args=[self.paid_video.id],
            )
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            Purchase.objects.count(), 0)
    
        def test_purchase_success_without_session_id_shows_pending_page(self):
            self.client.login(
                username="testuser",
                password="testpassword123",
            )

            response = self.client.get(
                reverse("videos:purchase_success")
            )

            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(
                response,
                "videos/purchase_pending.html",
            )

    def test_purchase_success_with_unknown_session_id_shows_pending_page(self):
        self.client.login(
            username="testuser",
            password="testpassword123",
        )

        response = self.client.get(
            reverse("videos:purchase_success"),
            {"session_id": "cs_unknown_123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "videos/purchase_pending.html",
        )

    def test_purchase_success_displays_user_purchase(self):
        purchase = Purchase.objects.create(
            user=self.user,
            video=self.paid_video,
            amount=Decimal("15.00"),
            currency="cad",
            status=Purchase.Status.PENDING,
            stripe_checkout_session_id="cs_test_123",
        )

        self.client.login(
            username="testuser",
            password="testpassword123",
        )

        response = self.client.get(
            reverse("videos:purchase_success"),
            {"session_id": "cs_test_123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "videos/purchase_result.html",
        )
        self.assertEqual(
            response.context["purchase"],
            purchase,
        )

    def test_user_cannot_view_another_users_purchase(self):
        another_user = User.objects.create_user(
            username="anotheruser",
            password="anotherpassword123",
        )

        Purchase.objects.create(
            user=another_user,
            video=self.paid_video,
            amount=Decimal("15.00"),
            currency="cad",
            status=Purchase.Status.PAID,
            stripe_checkout_session_id="cs_private_123",
        )

        self.client.login(
            username="testuser",
            password="testpassword123",
        )

        response = self.client.get(
            reverse("videos:purchase_success"),
            {"session_id": "cs_private_123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "videos/purchase_pending.html",
        )

    def test_anonymous_user_cannot_access_purchase_success(self):
        response = self.client.get(
            reverse("videos:purchase_success"),
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)


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


class ManageVideosViewTests(TestCase):

    def setUp(self):
        self.category = Category.objects.create(
            name="Technology"
        )

        self.other_category = Category.objects.create(
            name="Business"
        )

        self.admin = User.objects.create_superuser(
            username="video_admin",
            email="admin@example.com",
            password="adminpassword123",
        )

        self.user = User.objects.create_user(
            username="regular_user",
            password="userpassword123",
        )

        # Create 12 videos to test pagination.
        for i in range(12):
            Video.objects.create(
                title=f"Python Tutorial {i}",
                description=f"Description {i}",
                category=self.category,
                access_type="free",
                price=0,
                is_published=True,
            )

        # Additional videos for filter testing.
        Video.objects.create(
            title="Advanced Django",
            description="Advanced Django course",
            category=self.other_category,
            access_type="paid",
            price=Decimal("20.00"),
            is_published=False,
        )

    def test_anonymous_user_cannot_access_manage_videos(self):
        response = self.client.get(
            reverse("videos:manage_videos")
        )

        self.assertEqual(response.status_code, 302)

    def test_regular_user_cannot_access_manage_videos(self):
        self.client.login(
            username="regular_user",
            password="userpassword123",
        )

        response = self.client.get(
            reverse("videos:manage_videos")
        )

        self.assertEqual(response.status_code, 302)

    def test_admin_can_access_manage_videos(self):
        self.client.login(
            username="video_admin",
            password="adminpassword123",
        )

        response = self.client.get(
            reverse("videos:manage_videos")
        )

        self.assertEqual(response.status_code, 200)

    def test_video_pagination_displays_ten_videos(self):
        self.client.login(
            username="video_admin",
            password="adminpassword123",
        )

        response = self.client.get(
            reverse("videos:manage_videos")
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["videos"]), 10)
        self.assertEqual(
            response.context["paginator"].count,
            13,
        )

    def test_second_page_displays_remaining_videos(self):
        self.client.login(
            username="video_admin",
            password="adminpassword123",
        )

        response = self.client.get(
            reverse("videos:manage_videos"),
            {"page": 2},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["videos"]), 3)

    def test_search_filter_works(self):
        self.client.login(
            username="video_admin",
            password="adminpassword123",
        )

        response = self.client.get(
            reverse("videos:manage_videos"),
            {"q": "Advanced Django"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["videos"]), 1)

    def test_category_filter_works(self):
        self.client.login(
            username="video_admin",
            password="adminpassword123",
        )

        response = self.client.get(
            reverse("videos:manage_videos"),
            {"category": self.other_category.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["videos"]), 1)

    def test_published_filter_works(self):
        self.client.login(
            username="video_admin",
            password="adminpassword123",
        )

        response = self.client.get(
            reverse("videos:manage_videos"),
            {"status": "published"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["paginator"].count,
            12,
        )
        self.assertEqual(len(response.context["videos"]), 10)

    def test_draft_filter_works(self):
        self.client.login(
            username="video_admin",
            password="adminpassword123",
        )

        response = self.client.get(
            reverse("videos:manage_videos"),
            {"status": "draft"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["videos"]), 1)

    def test_paid_filter_works(self):
        self.client.login(
            username="video_admin",
            password="adminpassword123",
        )

        response = self.client.get(
            reverse("videos:manage_videos"),
            {"access_type": "paid"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["videos"]), 1)


#this is 5 test for admin side 
class AdminDashboardAndAddVideoTests(TestCase):

    def setUp(self):
        self.category = Category.objects.create(
            name="Technology"
        )

        self.admin = User.objects.create_superuser(
            username="dashboard_admin",
            email="admin@example.com",
            password="adminpassword123",
        )

        self.user = User.objects.create_user(
            username="regular_user",
            password="userpassword123",
        )

        # Create published videos.
        for i in range(3):
            Video.objects.create(
                title=f"Published Video {i}",
                description="Published tutorial",
                category=self.category,
                access_type="free",
                price=0,
                is_published=True,
            )

        # Create draft videos.
        for i in range(2):
            Video.objects.create(
                title=f"Draft Video {i}",
                description="Draft tutorial",
                category=self.category,
                access_type="free",
                price=0,
                is_published=False,
            )

    def test_anonymous_user_cannot_access_dashboard(self):
        response = self.client.get(
            reverse("videos:admin_dashboard")
        )

        self.assertEqual(response.status_code, 302)

    def test_regular_user_cannot_access_dashboard(self):
        self.client.login(
            username="regular_user",
            password="userpassword123",
        )

        response = self.client.get(
            reverse("videos:admin_dashboard")
        )

        self.assertEqual(response.status_code, 302)

    def test_admin_dashboard_displays_correct_statistics(self):
        self.client.login(
            username="dashboard_admin",
            password="adminpassword123",
        )

        response = self.client.get(
            reverse("videos:admin_dashboard")
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_videos"], 5)
        self.assertEqual(response.context["published_videos"], 3)
        self.assertEqual(response.context["draft_videos"], 2)
        self.assertEqual(response.context["total_categories"], 1)
        self.assertEqual(len(response.context["recent_videos"]), 5)

    def test_add_video_page_loads(self):
        self.client.login(
            username="dashboard_admin",
            password="adminpassword123",
        )

        response = self.client.get(
            reverse("videos:add_video")
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)

    def test_add_video_invalid_form_displays_error(self):
        self.client.login(
            username="dashboard_admin",
            password="adminpassword123",
        )

        response = self.client.post(
            reverse("videos:add_video"),
            {},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)
        self.assertTrue(response.context["form"].errors)

    def test_admin_can_successfully_add_video(self):
        self.client.login(
            username="dashboard_admin",
            password="adminpassword123",
        )

        video_file = SimpleUploadedFile(
            "python_tutorial.mp4",
            b"fake video content",
            content_type="video/mp4",
        )

        response = self.client.post(
            reverse("videos:add_video"),
            {
                "title": "New Python Tutorial",
                "description": "Introduction to Python.",
                "category": self.category.id,
                "video_file": video_file,
                "access_type": "free",
                "price": "0",
                "is_published": "on",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            Video.objects.filter(
                title="New Python Tutorial"
            ).exists()
        )

        self.assertContains(
            response,
            "a été ajoutée avec succès",
        )

    def test_edit_video_page_loads(self):
        video = Video.objects.first()

        self.client.login(
            username="dashboard_admin",
            password="adminpassword123",
        )

        response = self.client.get(
            reverse("videos:edit_video", args=[video.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)
        self.assertEqual(response.context["video"], video)


def test_admin_can_edit_video(self):
    video = Video.objects.first()

    self.client.login(
        username="dashboard_admin",
        password="adminpassword123",
    )

    response = self.client.post(
        reverse("videos:edit_video", args=[video.id]),
        {
            "title": "Updated Python Tutorial",
            "description": "Updated description.",
            "category": self.category.id,
            "access_type": "free",
            "price": "0",
            "is_published": "on",
        },
    )

    video.refresh_from_db()

    self.assertEqual(response.status_code, 302)
    self.assertEqual(video.title, "Updated Python Tutorial")
    self.assertEqual(video.description, "Updated description.")


def test_admin_can_unpublish_video(self):
    video = Video.objects.filter(is_published=True).first()

    self.client.login(
        username="dashboard_admin",
        password="adminpassword123",
    )

    response = self.client.post(
        reverse(
            "videos:toggle_video_publication",
            args=[video.id],
        )
    )

    video.refresh_from_db()

    self.assertEqual(response.status_code, 302)
    self.assertFalse(video.is_published)


def test_admin_can_publish_video(self):
    video = Video.objects.filter(is_published=False).first()

    self.client.login(
        username="dashboard_admin",
        password="adminpassword123",
    )

    response = self.client.post(
        reverse(
            "videos:toggle_video_publication",
            args=[video.id],
        )
    )

    video.refresh_from_db()

    self.assertEqual(response.status_code, 302)
    self.assertTrue(video.is_published)


def test_publication_toggle_requires_post(self):
    video = Video.objects.filter(is_published=True).first()

    self.client.login(
        username="dashboard_admin",
        password="adminpassword123",
    )

    response = self.client.get(
        reverse(
            "videos:toggle_video_publication",
            args=[video.id],
        )
    )

    self.assertEqual(response.status_code, 405)


def test_admin_can_delete_video(self):
    video = Video.objects.first()
    video_id = video.id

    self.client.login(
        username="dashboard_admin",
        password="adminpassword123",
    )

    response = self.client.post(
        reverse(
            "videos:delete_video",
            args=[video_id],
        )
    )

    self.assertEqual(response.status_code, 302)
    self.assertFalse(
        Video.objects.filter(id=video_id).exists()
    )


class CategoryManagementViewTests(TestCase):

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="category_admin",
            email="categoryadmin@example.com",
            password="adminpassword123",
        )

        self.client.login(
            username="category_admin",
            password="adminpassword123",
        )

        self.category = Category.objects.create(
            name="Technology",
            description="Technology tutorials",
        )

        self.empty_category = Category.objects.create(
            name="Business",
            description="Business tutorials",
        )

    def test_manage_categories_page_loads(self):
        response = self.client.get(
            reverse("videos:manage_categories")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Technology")
        self.assertContains(response, "Business")

    def test_add_category_page_loads(self):
        response = self.client.get(
            reverse("videos:add_category")
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)

    def test_admin_can_add_category(self):
        response = self.client.post(
            reverse("videos:add_category"),
            {
                "name": "Artificial Intelligence",
                "description": "AI tutorials",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Category.objects.filter(
                name="Artificial Intelligence"
            ).exists()
        )

    def test_admin_cannot_add_duplicate_category(self):
        response = self.client.post(
            reverse("videos:add_category"),
            {
                "name": "Technology",
                "description": "Duplicate category",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Category.objects.count(), 2)

    def test_edit_category_page_loads(self):
        response = self.client.get(
            reverse(
                "videos:edit_category",
                args=[self.category.id],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)

    def test_admin_can_edit_category(self):
        response = self.client.post(
            reverse(
                "videos:edit_category",
                args=[self.category.id],
            ),
            {
                "name": "Software Development",
                "description": "Programming tutorials",
            },
        )

        self.category.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.category.name,
            "Software Development",
        )

    def test_admin_can_delete_empty_category(self):
        category_id = self.empty_category.id

        response = self.client.post(
            reverse(
                "videos:delete_category",
                args=[category_id],
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Category.objects.filter(id=category_id).exists()
        )

    def test_admin_cannot_delete_category_with_videos(self):
        Video.objects.create(
            title="Python Tutorial",
            description="Python basics",
            category=self.category,
            access_type="free",
            price=0,
            is_published=True,
        )

        response = self.client.post(
            reverse(
                "videos:delete_category",
                args=[self.category.id],
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Category.objects.filter(id=self.category.id).exists()
        )

    def test_delete_category_requires_post(self):
        response = self.client.get(
            reverse(
                "videos:delete_category",
                args=[self.empty_category.id],
            )
        )

        self.assertEqual(response.status_code, 405)

class StripeWebhookTests(TestCase):

    def setUp(self):
        self.category = Category.objects.create(
            name="Technology"
        )

        self.user = User.objects.create_user(
            username="stripeuser",
            email="stripe@example.com",
            password="password123",
        )

        self.video = Video.objects.create(
            title="Advanced Django",
            description="Advanced Django tutorial",
            category=self.category,
            access_type="paid",
            price=Decimal("15.00"),
            is_published=True,
        )

        self.purchase = Purchase.objects.create(
            user=self.user,
            video=self.video,
            amount=Decimal("15.00"),
            currency="cad",
            status=Purchase.Status.PENDING,
            stripe_checkout_session_id="cs_test_123",
        )

    def create_event(
        self,
        event_type="checkout.session.completed",
        event_id="evt_test_123",
        **session_overrides
    ):
        session = {
            "id": "cs_test_123",
            "mode": "payment",
            "payment_status": "paid",
            "currency": "cad",
            "amount_total": 1500,
            "payment_intent": "pi_test_123",
            "metadata": {
                "purchase_id": str(self.purchase.id),
                "user_id": str(self.user.id),
                "video_id": str(self.video.id),
            },
        }

        session.update(session_overrides)

        return {
            "id": event_id,
            "type": event_type,
            "data": {
                "object": session,
            },
        }

    def post_webhook(self, event):
        with patch(
            "videos.views.stripe.Webhook.construct_event",
            return_value=event,
        ):
            return self.client.post(
                reverse("videos:stripe_webhook"),
                data=b'{"test": "payload"}',
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE="test_signature",
            )

    @patch("videos.views.settings.STRIPE_WEBHOOK_SECRET", "whsec_test")
    def test_successful_payment_grants_video_access(self):
        event = self.create_event()

        response = self.post_webhook(event)

        self.purchase.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.purchase.status,
            Purchase.Status.PAID,
        )

        self.assertIsNotNone(self.purchase.paid_at)

        self.assertTrue(
            VideoAccessGrant.objects.filter(
                user=self.user,
                video=self.video,
            ).exists()
        )

        self.assertEqual(
            ProcessedStripeEvent.objects.count(),
            1,
        )

    @patch("videos.views.settings.STRIPE_WEBHOOK_SECRET", "whsec_test")
    def test_duplicate_event_is_not_processed_twice(self):
        event = self.create_event()

        first_response = self.post_webhook(event)
        second_response = self.post_webhook(event)

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)

        self.assertEqual(
            ProcessedStripeEvent.objects.count(),
            1,
        )

        self.assertEqual(
            VideoAccessGrant.objects.filter(
                user=self.user,
                video=self.video,
            ).count(),
            1,
        )

    @patch("videos.views.settings.STRIPE_WEBHOOK_SECRET", "whsec_test")
    def test_unpaid_session_does_not_grant_access(self):
        event = self.create_event(
            payment_status="unpaid",
        )

        response = self.post_webhook(event)

        self.purchase.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.purchase.status,
            Purchase.Status.PENDING,
        )

        self.assertFalse(
            VideoAccessGrant.objects.filter(
                user=self.user,
                video=self.video,
            ).exists()
        )

    @patch("videos.views.settings.STRIPE_WEBHOOK_SECRET", "whsec_test")
    def test_failed_async_payment_marks_purchase_failed(self):
        event = self.create_event(
            event_type="checkout.session.async_payment_failed",
        )

        response = self.post_webhook(event)

        self.purchase.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.purchase.status,
            Purchase.Status.FAILED,
        )

        self.assertFalse(
            VideoAccessGrant.objects.filter(
                user=self.user,
                video=self.video,
            ).exists()
        )

    @patch("videos.views.settings.STRIPE_WEBHOOK_SECRET", "whsec_test")
    def test_invalid_signature_is_rejected(self):
        with patch(
            "videos.views.stripe.Webhook.construct_event",
            side_effect=ValueError("Invalid signature"),
        ):
            response = self.client.post(
                reverse("videos:stripe_webhook"),
                data=b"invalid payload",
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE="invalid",
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            ProcessedStripeEvent.objects.count(),
            0,
        )

    @patch("videos.views.settings.STRIPE_WEBHOOK_SECRET", "")
    def test_missing_webhook_secret_returns_500(self):
        response = self.client.post(
            reverse("videos:stripe_webhook"),
            data=b"{}",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 500)

    @patch("videos.views.settings.STRIPE_WEBHOOK_SECRET", "whsec_test")
    def test_unsupported_event_is_ignored(self):
        event = self.create_event(
            event_type="customer.created",
        )

        response = self.post_webhook(event)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            ProcessedStripeEvent.objects.count(),
            0,
        )

    @patch("videos.views.settings.STRIPE_WEBHOOK_SECRET", "whsec_test")
    def test_metadata_mismatch_is_rejected(self):
        event = self.create_event(
            metadata={
                "purchase_id": str(self.purchase.id),
                "user_id": "999999",
                "video_id": str(self.video.id),
            }
        )

        response = self.post_webhook(event)

        self.assertEqual(response.status_code, 400)

        self.purchase.refresh_from_db()

        self.assertEqual(
            self.purchase.status,
            Purchase.Status.PENDING,
        )

        self.assertEqual(
            ProcessedStripeEvent.objects.count(),
            0,
        )

    @patch("videos.views.settings.STRIPE_WEBHOOK_SECRET", "whsec_test")
    def test_wrong_payment_amount_is_rejected(self):
        event = self.create_event(
            amount_total=1000,
        )

        response = self.post_webhook(event)

        self.assertEqual(response.status_code, 400)

        self.purchase.refresh_from_db()

        self.assertEqual(
            self.purchase.status,
            Purchase.Status.PENDING,
        )

        self.assertFalse(
            VideoAccessGrant.objects.filter(
                user=self.user,
                video=self.video,
            ).exists()
        )