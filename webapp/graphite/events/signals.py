from django.db.models import signals



def taggeditem_delete(sender, **kwargs):
    deleted = kwargs['instance']
    try:
        ob_id = int(deleted.pk)
    except ValueError:
        return
    from django.contrib.contenttypes.models import ContentType
    from tagging.models import TaggedItem
    ctype = ContentType.objects.get_for_model(deleted)
    item_tags = TaggedItem.objects.filter(content_type=ctype, object_id=ob_id,)
    item_tags.delete()

signals.post_delete.connect(taggeditem_delete)
