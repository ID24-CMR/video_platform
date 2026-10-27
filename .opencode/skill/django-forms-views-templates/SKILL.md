---
name: django-forms-views-templates
description: Django forms, class-based views, templates with partials, messages, HTMX-free progressive enhancement. Load for UI/server-rendered work.
---
# Forms, Views, Templates

## Forms
```python
class CheckoutForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=20)
    def clean_quantity(self): ...
```
- ModelForm: always list `fields = [...]` explicitly, never `"__all__"`. Exclude privileged fields (`user`, `status`, Stripe IDs); set them in the service.
- Validation: field `clean_<name>`, cross-field `clean()`; DB constraints still required.

## View pattern
```python
class OrderCreateView(LoginRequiredMixin, FormView):
    form_class = OrderForm
    template_name = "orders/form.html"
    def form_valid(self, form):
        order = create_order(user=self.request.user, **form.cleaned_data)
        messages.success(self.request, "Order created.")
        return redirect("orders:detail", pk=order.pk)
```
Detail/update views: `get_queryset()` returns `orders_for_user(self.request.user)`.

## JSON endpoints (no DRF)
```python
@require_POST
@login_required
def api_toggle(request, pk):
    obj = get_object_or_404(selectors.items_for_user(request.user), pk=pk)
    services.toggle(obj)
    return JsonResponse({"active": obj.active})
```
Validate input with a Form even for JSON (`json.loads` -> `Form(data)`). Return correct status codes; consistent error shape `{"error": {"code": "...", "message": "..."}}`.

## Templates
- `base.html` with blocks `title`, `content`, `extra_head`, `extra_js`.
- `{% csrf_token %}` in every POST form. Pass CSRF header for fetch calls.
- Partials (Django 6): `{% partialdef card %}...{% endpartialdef %}` then `{% partial card %}`.
- Custom 404/403/500 templates under `templates/`.
- i18n-ready: `{% trans %}` / `gettext_lazy` if multilingual is planned.

## Pagination and filtering
`paginate_by`, preserve query string in links; filter via GET `Form` in the selector, never raw `request.GET` into queries.
