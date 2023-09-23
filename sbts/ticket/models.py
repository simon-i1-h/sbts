from django.db import models

import uuid


class Ticket(models.Model):
    class Manager(models.Manager):
        def sorted_tickets(self):
            return self.order_by('created_at')

    class Meta:
        default_manager_name = 'objects'

    objects = Manager()

    key = models.UUIDField(primary_key=True, default=uuid.uuid4)
    title = models.TextField()
    created_at = models.DateTimeField()

    def sorted_comments(self):
        return self.comment_set.order_by('created_at')


class Comment(models.Model):
    key = models.UUIDField(primary_key=True, default=uuid.uuid4)
    comment = models.TextField()
    created_at = models.DateTimeField()
    last_updated = models.DateTimeField()
    is_modified = models.BooleanField(default=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
