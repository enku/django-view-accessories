from __future__ import unicode_literals

from django.db import models


class Widget(models.Model):
    text = models.CharField(max_length=300)

    def __unicode__(self):
        return self.text
