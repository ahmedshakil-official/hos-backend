from common.cache_helpers import clear_notification_count_data_cache


def post_save_expo_notification(sender, instance, created, **kwargs):
    # Clear cached notification count data for the user
    clear_notification_count_data_cache(user_id=instance.user_id)
