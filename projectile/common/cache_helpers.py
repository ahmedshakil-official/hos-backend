import logging
from datetime import timedelta

from django.core.cache import cache
from common.cache_keys import (
    QS_COUNT_CACHE_KEY_PREFIX,
    ORG_CUMULATIVE_DISCOUNT_FACTOR_VALUE_CACHE_KEY,
    ORGANIZATION_AND_AREA_DISCOUNT_CACHE_KEY,
    ORGANIZATION_HAS_ORDER_ON_DELIVERY_DATE,
    NOTIFICATION_COUNT_USER_CACHE_KEY_PREFIX
)


logger = logging.getLogger(__name__)


def delete_qs_count_cache(model):
    """
    Expiring the cache of query set counts for invoice group related view
    """
    model_name = model.__name__
    cache_key_prefix = f"{QS_COUNT_CACHE_KEY_PREFIX}{model_name}*"
    cache.delete_many(keys=cache.keys(cache_key_prefix))


def get_or_clear_cumulative_discount_factor(
    organization_id = None,
    organization_ids = None,
    clear=False
):
    """
    Retrieve or clear the cumulative discount factor for a specific organization from the cache.

    Args:
    - organization_id (int): The ID of the organization.
    - organization_ids (list): List of organization ids
    - clear (bool, optional): If True, clears the cached value. Defaults to False.

    Returns:
    - bool or float: If `clear` is True, returns True on successful cache clearance.
        Otherwise, returns the cached cumulative discount factor (if present).
    """
    # Generate cache key based on organization ID
    cache_key = f"{ORG_CUMULATIVE_DISCOUNT_FACTOR_VALUE_CACHE_KEY}{organization_id}"

    if clear and organization_ids:
        # generate key list from organization id list
        try:
            key_list = [
                f"{ORG_CUMULATIVE_DISCOUNT_FACTOR_VALUE_CACHE_KEY}{id[0]}"
                for id in organization_ids
            ]
        except TypeError:
            key_list = [
                f"{ORG_CUMULATIVE_DISCOUNT_FACTOR_VALUE_CACHE_KEY}{id}"
                for id in organization_ids
            ]
        cache.delete_many(keys=key_list)
        logger.info(
            f"Deleted cached cumulative discount factor for organizations: {list(organization_ids)}"
        )
        return True

    if clear and organization_id:
        # If clear flag is True, delete the cached value and return True
        cache.delete(key=cache_key)
        logger.info(
            f"Deleted cache cumulative discount factor for organization: {organization_id}"
        )
        return True

    # Otherwise, attempt to retrieve the value from the cache
    return cache.get(key=cache_key)


def clear_organization_and_area_discount_cache(organization_ids):
    """
    Clear cached organization and area discount data based on organization IDs.
    Args:
    organization_ids (list): A list of organization IDs for which cached data needs to be cleared.
    """
    # Create a list of cache keys based on the provided organization IDs
    key_list = [
        f"{ORGANIZATION_AND_AREA_DISCOUNT_CACHE_KEY}{id[0]}"
        for id in organization_ids
    ]

    # Delete cached data associated with the generated keys
    cache.delete_many(keys=key_list)


def set_or_clear_delivery_date_cache(organization_id, delivery_date, clear=False):
    """
    Manages caching or clearing of a delivery date for a specific organization.

    Args:
    - organization_id (int): The ID of the organization.
    - delivery_date (datetime): The date of the delivery.
    - clear (bool, optional): If True, clears the cached delivery date.

    Returns:
    - bool: True if the operation is successful.

    """
    from pharmacy.helpers import is_order_exists_on_delivery_date

    # Create keys for caching delivery dates specific to the organization
    delivery_date_key = f"{ORGANIZATION_HAS_ORDER_ON_DELIVERY_DATE}{delivery_date}_{organization_id}"

    # Retrieve cached delivery date
    has_delivery = cache.get(key=delivery_date_key)

    # Cache the delivery date if it doesn't exist in the cache
    if has_delivery is None and not clear:
        has_order = is_order_exists_on_delivery_date(
            organization_id=organization_id,
            delivery_date=delivery_date,
        )
        cache.set(
            key=delivery_date_key,
            value=has_order,
            timeout=timedelta(hours=24).total_seconds()
        )
        # Log the action of caching delivery date for the organization
        logger.info(f"Cached delivery date for organization id: {organization_id}")

    # Clear cached delivery date if 'clear' is True
    if clear:
        cache.delete(key=delivery_date_key)
        # Log the action of clearing cached delivery date for the organization
        logger.info(f"Deleted cached delivery date for organization id: {organization_id}")


def clear_notification_count_data_cache(user_id):
    # Create keys for caching notification count specific to the user
    notification_count_cache_key = f"{NOTIFICATION_COUNT_USER_CACHE_KEY_PREFIX}{user_id}"

    cache.delete(key=notification_count_cache_key)
    # Log the action of clearing cached notification count data for the user
    logger.info(f"Deleted cached notification count data for user id: {user_id}")