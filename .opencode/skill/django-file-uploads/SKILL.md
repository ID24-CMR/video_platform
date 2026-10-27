---
name: django-file-uploads
description: Safe image/file upload handling with Django and Pillow 12: validation, size limits, random names, thumbnails. Load for ImageField/FileField work.
---
# File Uploads with Pillow

## Model
```python
import uuid
from pathlib import Path

def upload_to(instance, filename: str) -> str:
    return f"{instance._meta.model_name}/{uuid.uuid4().hex}{Path(filename).suffix.lower()}"

class Avatar(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="avatar")
    image = models.ImageField(upload_to=upload_to, validators=[validate_image_size, FileExtensionValidator(["jpg", "jpeg", "png", "webp"])])
```

## Validators
```python
from django.core.exceptions import ValidationError
MAX_BYTES = 5 * 1024 * 1024

def validate_image_size(f):
    if f.size > MAX_BYTES:
        raise ValidationError("Image must be 5 MB or smaller.")
```
`ImageField` already verifies via Pillow; additionally set `DATA_UPLOAD_MAX_MEMORY_SIZE` and `FILE_UPLOAD_MAX_MEMORY_SIZE`, and limit pixel counts: `PIL.Image.MAX_IMAGE_PIXELS = 50_000_000` (decompression-bomb guard; keep Pillow's warning->error behavior).

## Processing
```python
from io import BytesIO
from PIL import Image, ImageOps

def make_thumbnail(file, size=(400, 400)) -> ContentFile:
    with Image.open(file) as img:
        img = ImageOps.exif_transpose(img)         # honor orientation
        img.thumbnail(size)
        buf = BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=85, optimize=True)  # strips EXIF
    return ContentFile(buf.getvalue(), name="thumb.jpg")
```
Re-encoding strips metadata and malicious payloads. Do heavy processing via background task, not in the request.

## Rules
- Never trust client `content_type` or filename; random server-side names.
- Do not store uploads under `STATIC_ROOT` or any executable path.
- Serve through storage URL; private files via authorized view with `FileResponse`.
- Delete old files on replace (service function), not in `save()` overrides.
- Forms need `enctype="multipart/form-data"`.
- Tests: generate PNG bytes with Pillow, use `SimpleUploadedFile`.
