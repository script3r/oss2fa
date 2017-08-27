import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Challenge

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Challenge)
def on_challenge_created_perform_challenge(sender, instance, created,
                                           **kwargs):
    if created:
        logger.info(
            u'processing challenge creation for `{0}` with device kind `{1}`'.
            format(instance.pk, instance.device.kind))

        # obtain the device handler module
        module = instance.device.kind.get_module()

        # create the challenge
        _, err = module.challenge_create(instance)
        if err:
            instance.status = Challenge.STATUS_FAILED
            instance.save()

            logger.error(u'failed to process challenge `{0}` due to: {1}'.
                         format(instance.pk, err))
            return

        # mark the challenge as in-progress
        instance.status = Challenge.STATUS_IN_PROGRESS
        instance.save()
