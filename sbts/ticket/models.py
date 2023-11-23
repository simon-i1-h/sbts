from django.db import models

import uuid


class Ticket(models.Model):
    class Manager(models.Manager):
        def sorted_tickets(self):
            return self.order_by('-created_at')

    class Meta:
        default_manager_name = 'objects'

    objects = Manager()

    key = models.UUIDField(primary_key=True, default=uuid.uuid4)
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField()

    def sorted_comments(self):
        return self.comment_set.order_by('created_at')

    @property
    def lastmod(self):
        lastcommented_at = self.comment_set.aggregate(models.Max('created_at'))['created_at__max']
        if lastcommented_at is not None:
            return lastcommented_at
        return self.created_at


class Comment(models.Model):
    key = models.UUIDField(primary_key=True, default=uuid.uuid4)
    username = models.CharField(max_length=150)
    comment = models.CharField(max_length=65535)
    created_at = models.DateTimeField()
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
