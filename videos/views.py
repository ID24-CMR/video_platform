from datetime import timezone
from decimal import Decimal
import logging

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect, render
from django.urls import reverse

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.utils.http import url_has_allowed_host_and_scheme

from django.http import FileResponse, Http404
import stripe

from django.db import IntegrityError, transaction
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator

from .models import (
    Purchase,
    VideoAccessGrant,
    ProcessedStripeEvent,
)

from config import settings
from .models import Purchase, Video, VideoAccessGrant

from .forms import RegistrationForm

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from .forms import CategoryForm, VideoForm
from .models import Video

from videos.forms import VideoForm

from .models import Category, Video

logger = logging.getLogger(__name__)


def is_main_admin(user):
    return (
        user.is_authenticated
        and user.is_active
        and user.is_superuser
    )


@user_passes_test(is_main_admin, login_url="/admin/login/")
def admin_dashboard(request):
    context = {
        "total_videos": Video.objects.count(),
        "published_videos": Video.objects.filter(
            is_published=True
        ).count(),
        "draft_videos": Video.objects.filter(
            is_published=False
        ).count(),
        "total_categories": Category.objects.count(),
        "recent_videos": Video.objects.select_related(
            "category"
        ).order_by("-created_at")[:5],
    }

    return render(
        request,
        "admin_dashboard/dashboard.html",
        context,
    )


@user_passes_test(is_main_admin, login_url="/admin/login/")
def add_video(request):
    if request.method == "POST":
        form = VideoForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            video = form.save()
            messages.success(
                request,
                f'La vidéo "{video.title}" a été ajoutée avec succès.',
            )
            return redirect(reverse("videos:add_video"))

        messages.error(
            request,
            "Le formulaire contient des erreurs. Vérifie les champs.",
        )
    else:
        form = VideoForm()

    return render(
        request,
        "admin_dashboard/add_video.html",
        {"form": form},
    )

@user_passes_test(is_main_admin, login_url="/admin/login/")
def manage_videos(request):
    videos = Video.objects.select_related("category").all()

    search_query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "")
    status = request.GET.get("status", "")
    access_type = request.GET.get("access_type", "")

    if search_query:
        videos = videos.filter(
            Q(title__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    if category_id.isdigit():
        videos = videos.filter(category_id=int(category_id))

    if status in ["published", "draft"]:
        videos = videos.filter(
            is_published=(status == "published")
        )

    if access_type in ["free", "paid"]:
        videos = videos.filter(access_type=access_type)

    # Pagination
    paginator = Paginator(videos, 5)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "videos": page_obj,
        "page_obj": page_obj,
        "paginator": paginator,
        "categories": Category.objects.all(),
        "search_query": search_query,
        "selected_category": category_id,
        "selected_status": status,
        "selected_access_type": access_type,
    }

    return render(
        request,
        "admin_dashboard/manage_videos.html",
        context,
    )


@user_passes_test(is_main_admin, login_url="/admin/login/")
def edit_video(request, video_id):
    video = get_object_or_404(Video, pk=video_id)

    if request.method == "POST":
        form = VideoForm(
            request.POST,
            request.FILES,
            instance=video,
        )

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Video updated successfully.",
            )
            return redirect("videos:manage_videos")
    else:
        form = VideoForm(instance=video)

    return render(
        request,
        "admin_dashboard/edit_video.html",
        {"form": form, "video": video},
    )


@user_passes_test(is_main_admin, login_url="/admin/login/")
@require_POST
def toggle_video_publication(request, video_id):
    video = get_object_or_404(Video, pk=video_id)

    video.is_published = not video.is_published
    video.save(update_fields=["is_published", "updated_at"])

    messages.success(
        request,
        "Video publication status updated.",
    )

    return redirect("videos:manage_videos")


@user_passes_test(is_main_admin, login_url="/admin/login/")
@require_POST
def delete_video(request, video_id):
    video = get_object_or_404(Video, pk=video_id)
    video.delete()

    messages.success(
        request,
        "Video deleted successfully.",
    )

    return redirect("videos:manage_videos")

@user_passes_test(is_main_admin, login_url="/admin/login/")
def manage_categories(request):
    categories = Category.objects.all()

    return render(
        request,
        "admin_dashboard/manage_categories.html",
        {"categories": categories}
    )


@user_passes_test(is_main_admin, login_url="/admin/login/")
def add_category(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Category added successfully.")
            return redirect("videos:manage_categories")
    else:
        form = CategoryForm()

    return render(
        request,
        "admin_dashboard/category_form.html",
        {"form": form, "page_title": "Add Category"}
    )


@user_passes_test(is_main_admin, login_url="/admin/login/")
def edit_category(request, category_id):
    category = get_object_or_404(Category, pk=category_id)

    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)

        if form.is_valid():
            form.save()
            messages.success(request, "Category updated successfully.")
            return redirect("videos:manage_categories")
    else:
        form = CategoryForm(instance=category)

    return render(
        request,
        "admin_dashboard/category_form.html",
        {"form": form, "page_title": "Edit Category"}
    )


@user_passes_test(is_main_admin, login_url="/admin/login/")
@require_POST
def delete_category(request, category_id):
    category = get_object_or_404(Category, pk=category_id)

    if category.videos.exists():
        messages.error(
            request,
            "This category cannot be deleted because it contains videos."
        )
    else:
        category.delete()
        messages.success(request, "Category deleted successfully.")

    return redirect("videos:manage_categories")

def public_video_library(request):
    videos = Video.objects.filter(
        is_published=True
    ).select_related("category")

    categories = Category.objects.all()

    search_query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "").strip()
    access_type = request.GET.get("access", "").strip()

    # Search by title or description
    if search_query:
        videos = videos.filter(
            Q(title__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    # Filter by category
    if category_id.isdigit():
        videos = videos.filter(category_id=int(category_id))

    # Filter free or paid videos
    if access_type in ["free", "paid"]:
        videos = videos.filter(access_type=access_type)

    context = {
        "videos": videos,
        "categories": categories,
        "search_query": search_query,
        "selected_category": category_id,
        "selected_access": access_type,
    }

    return render(
        request,
        "videos/public_library.html",
        context
    )


def public_video_detail(request, video_id):
    video = get_object_or_404(
        Video.objects.select_related("category"),
        pk=video_id,
        is_published=True
    )

    return render(
        request,
        "videos/video_detail.html",
        {"video": video}
    )

def register_view(request):
    if request.user.is_authenticated:
        return redirect("videos:account")

    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)

            messages.success(
                request,
                "Your account has been created successfully."
            )

            return redirect("videos:account")
    else:
        form = RegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form}
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect("videos:account")

    if request.method == "POST":
        form = AuthenticationForm(
            request,
            data=request.POST
        )

        if form.is_valid():
            user = form.get_user()
            login(request, user)

            next_url = request.POST.get("next") or request.GET.get("next")

            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure()
            ):
                return redirect(next_url)

            return redirect("videos:account")
    else:
        form = AuthenticationForm(request)

    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
            "next": request.GET.get("next", "")
        }
    )


@login_required(login_url="videos:login")
def account_view(request):
    return render(
        request,
        "accounts/account.html",
        {"account_user": request.user}
    )


@login_required(login_url="videos:login")
@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")

    return redirect("videos:public_library")

@login_required(login_url="videos:login")
def stream_video(request, video_id):
    video = get_object_or_404(
        Video,
        pk=video_id,
        is_published=True
    )

    # Free videos are available to all registered users.
    # Paid videos require an explicit access grant.
    has_access = (
        video.access_type == Video.AccessType.FREE
        or request.user.is_superuser
        or VideoAccessGrant.objects.filter(
            user=request.user,
            video=video
        ).exists()
    )

    if not has_access:
        raise Http404("Video not found.")

    try:
        video_file = video.video_file.open("rb")
    except (FileNotFoundError, OSError, ValueError):
        raise Http404("Video file not found.")

    return FileResponse(
        video_file,
        content_type="application/octet-stream"
    )

@login_required(login_url="videos:login")
@require_POST
def create_checkout_session(request, video_id):

    if not settings.STRIPE_SECRET_KEY:
        messages.error(
            request,
            "Payments are not configured yet."
        )
        return redirect(
            "videos:video_detail",
            video_id=video_id
        )

    stripe.api_key = settings.STRIPE_SECRET_KEY

    video = get_object_or_404(
        Video,
        pk=video_id,
        is_published=True,
        access_type=Video.AccessType.PAID
    )

    # Prevent a user from purchasing the same video twice.
    existing_grant = VideoAccessGrant.objects.filter(
        user=request.user,
        video=video
    ).exists()

    if existing_grant:
        messages.info(
            request,
            "You already have access to this video."
        )
        return redirect(
            "videos:video_detail",
            video_id=video.id
        )

    currency = settings.STRIPE_CURRENCY

    if currency != "cad":
        messages.error(
            request,
            "This checkout workflow is currently configured for CAD."
        )
        return redirect(
            "videos:video_detail",
            video_id=video.id
        )

    # Convert the database price to integer cents.
    amount_in_cents = int(
        (video.price * Decimal("100")).quantize(
            Decimal("1")
        )
    )

    if amount_in_cents <= 0:
        messages.error(
            request,
            "This video has an invalid price."
        )
        return redirect(
            "videos:video_detail",
            video_id=video.id
        )

    # Create the pending purchase before contacting Stripe.
    purchase = Purchase.objects.create(
        user=request.user,
        video=video,
        amount=video.price,
        currency=currency,
        status=Purchase.Status.PENDING
    )

    success_url = request.build_absolute_uri(
        reverse("videos:purchase_success")
    )

    cancel_url = request.build_absolute_uri(
        reverse(
            "videos:video_detail",
            args=[video.id]
        )
    )

    try:
        session = stripe.checkout.Session.create(
            mode="payment",

            payment_method_types=["card"],

            line_items=[
                {
                    "price_data": {
                        "currency": currency,
                        "product_data": {
                            "name": video.title,
                            "description": (
                                f"VideoHub video #{video.id}"
                            ),
                        },
                        "unit_amount": amount_in_cents,
                    },
                    "quantity": 1,
                }
            ],

            customer_email=request.user.email or None,

            client_reference_id=str(purchase.id),

            metadata={
                "purchase_id": str(purchase.id),
                "user_id": str(request.user.id),
                "video_id": str(video.id),
            },

            success_url=(
                success_url
                + "?session_id={CHECKOUT_SESSION_ID}"
            ),

            cancel_url=cancel_url,
        )

        purchase.stripe_checkout_session_id = session.id
        purchase.save(
            update_fields=["stripe_checkout_session_id"]
        )

        return redirect(session.url, permanent=False)

    except stripe.StripeError:
        purchase.status = Purchase.Status.FAILED
        purchase.save(update_fields=["status"])

        messages.error(
            request,
            "We could not start checkout. Please try again."
        )

        return redirect(
            "videos:video_detail",
            video_id=video.id
        )

@login_required(login_url="videos:login")
def purchase_success(request):

    session_id = request.GET.get("session_id", "").strip()

    if not session_id:
        return render(
            request,
            "videos/purchase_pending.html"
        )

    purchase = Purchase.objects.filter(
        user=request.user,
        stripe_checkout_session_id=session_id
    ).first()

    if purchase is None:
        return render(
            request,
            "videos/purchase_pending.html"
        )

    return render(
        request,
        "videos/purchase_result.html",
        {"purchase": purchase}
    )


@csrf_exempt
@require_POST
def stripe_webhook(request):

    if not settings.STRIPE_WEBHOOK_SECRET:
        logger.error("Stripe webhook secret is not configured.")
        return HttpResponse(status=500)

    stripe.api_key = settings.STRIPE_SECRET_KEY

    signature = request.headers.get("Stripe-Signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload=request.body,
            sig_header=signature,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )

    except (ValueError, stripe.SignatureVerificationError):
        return HttpResponseBadRequest(
            "Invalid webhook signature or payload."
        )

    event_id = event["id"]
    event_type = event["type"]
    session = event["data"]["object"]

    supported_events = {
        "checkout.session.completed",
        "checkout.session.async_payment_succeeded",
        "checkout.session.async_payment_failed",
    }

    if event_type not in supported_events:
        return HttpResponse(status=200)

    metadata = session.get("metadata") or {}
    purchase_id = metadata.get("purchase_id")

    if not purchase_id:
        logger.warning(
            "Stripe event %s has no purchase ID.",
            event_id
        )
        return HttpResponse(status=200)

    try:
        with transaction.atomic():

            # Reserve this Stripe event ID. A duplicate event
            # cannot be processed twice.
            ProcessedStripeEvent.objects.create(
                event_id=event_id,
                event_type=event_type,
            )

            purchase = (
                Purchase.objects
                .select_for_update()
                .select_related("user", "video")
                .get(pk=purchase_id)
            )

            # Verify that the event corresponds to this purchase.
            if (
                str(purchase.user_id) != str(metadata.get("user_id"))
                or str(purchase.video_id) != str(metadata.get("video_id"))
                or session.get("id")
                != purchase.stripe_checkout_session_id
            ):
                logger.error(
                    "Stripe metadata mismatch for purchase %s.",
                    purchase_id
                )
                raise ValueError("Purchase metadata mismatch.")

            # Confirm that the checkout session is a payment
            # session for the expected amount and currency.
            if session.get("mode") != "payment":
                raise ValueError("Unexpected checkout mode.")

            if session.get("currency") != purchase.currency:
                raise ValueError("Currency mismatch.")

            if session.get("amount_total") != int(
                purchase.amount * Decimal("100")
            ):
                raise ValueError("Payment amount mismatch.")

            if event_type in {
                "checkout.session.completed",
                "checkout.session.async_payment_succeeded",
            }:

                if session.get("payment_status") != "paid":
                    # Do not grant access for an unpaid session.
                    return HttpResponse(status=200)

                # Never let a later event change an already-paid
                # purchase back to another state.
                if purchase.status != Purchase.Status.PAID:
                    purchase.status = Purchase.Status.PAID
                    purchase.paid_at = timezone.now()
                    purchase.stripe_payment_intent_id = (
                        session.get("payment_intent") or ""
                    )

                    purchase.save(
                        update_fields=[
                            "status",
                            "paid_at",
                            "stripe_payment_intent_id",
                        ]
                    )

                VideoAccessGrant.objects.get_or_create(
                    user=purchase.user,
                    video=purchase.video,
                    defaults={
                        "source": VideoAccessGrant.GrantSource.PAYMENT
                    }
                )

            elif (
                event_type
                == "checkout.session.async_payment_failed"
            ):
                if purchase.status == Purchase.Status.PENDING:
                    purchase.status = Purchase.Status.FAILED
                    purchase.save(update_fields=["status"])

    except ProcessedStripeEvent.DoesNotExist:
        return HttpResponse(status=200)

    except IntegrityError:
        # Most commonly, Stripe delivered a duplicate event.
        return HttpResponse(status=200)

    except Purchase.DoesNotExist:
        logger.warning(
            "Stripe event %s refers to a missing purchase.",
            event_id
        )
        return HttpResponse(status=200)

    except ValueError:
        logger.exception(
            "Stripe event %s failed purchase verification.",
            event_id
        )
        return HttpResponseBadRequest(
            "Purchase verification failed."
        )

    return HttpResponse(status=200)

def public_video_detail(request, video_id):
    video = get_object_or_404(
        Video.objects.select_related("category"),
        pk=video_id,
        is_published=True
    )

    has_access = (
        video.access_type == Video.AccessType.FREE
        or (
            request.user.is_authenticated
            and (
                request.user.is_superuser
                or VideoAccessGrant.objects.filter(
                    user=request.user,
                    video=video
                ).exists()
            )
        )
    )

    return render(
        request,
        "videos/video_detail.html",
        {
            "video": video,
            "has_access": has_access,
        }
    )