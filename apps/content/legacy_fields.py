"""Database-only field retained for migrations created with CKEditor 4.

The old upload field stored ordinary text. Keeping this stub lets existing and
fresh databases run that history without installing the retired editor.
"""
from django.db import models


class RichTextUploadingField(models.TextField):
    pass
