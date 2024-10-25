from versatileimagefield.utils import (
    get_rendition_key_set,
    validate_versatileimagefield_sizekey_list
)
from common.utils import (
    get_healthos_settings,
    build_versatileimagefield_url_set_from_image_name,
)
from common.tasks import get_documents
from core.enums import AllowOrderFrom
from pharmacy.utils import (
    get_delivery_date_for_product,
    get_organization_order_closing_and_reopening_time,
)


def prepare_image(image_name, image_key_set="product_images"):
    sizes = validate_versatileimagefield_sizekey_list(get_rendition_key_set(image_key_set))
    image_set = build_versatileimagefield_url_set_from_image_name(image_name, sizes)
    return image_set

def prepare_delivery_date(is_queueing_item):
    return get_delivery_date_for_product(is_queueing_item)

def prepare_is_order_enabled():
    order_closing_date, order_reopening_date = get_organization_order_closing_and_reopening_time()

    return not order_closing_date and not order_reopening_date

def prepare_current_order_mode(order_mode):
    try:
        setting = get_healthos_settings()
        if setting.overwrite_order_mode_by_product:
            product_order_mode = order_mode
        else:
            product_order_mode = setting.allow_order_from
    except:
        product_order_mode = 0
    return product_order_mode

def prepare_is_out_of_stock(orderable_stock, order_mode):
    # Stock_and_Open:
    # 1. if order mode is Stock_and_Open then we consider product order mode as the order mode
    # 2. if product order_mode is Stock_and_Next_day then we need to return False unless product
    #    has orderable quantity greater then 0 the we need to return True
    # we are getting updated order mode of the product from get_product_order_mode
    # if order mode is by Organization and its Stock_and_Open
    setting = get_healthos_settings()
    if (
            order_mode == AllowOrderFrom.STOCK_AND_NEXT_DAY and
            orderable_stock <= 0 and
            setting.allow_order_from == AllowOrderFrom.STOCK_AND_OPEN and
            not setting.overwrite_order_mode_by_product
        ):
            order_mode = AllowOrderFrom.STOCK

    return orderable_stock <= 0 and order_mode == AllowOrderFrom.STOCK

def get_related_object(alias, name):
    if not alias:
        return {}
    return {
        "alias": alias,
        "name": name,
    }

def get_ranking_value(is_queueing_item:bool, is_salesable_item: bool, is_stock_remainder: bool):
    """_summary_

    Args:
        is_queueing_item (bool): Define a product is regular or pre order mode
        is_salesable_item (bool): Define a product is available in out catalog or a wishlist item
        is_stock_remainder (bool): Define a stock is available or in remainder mode

    Returns:
        _type_: float value based on ranking value(Here the order will be Regular > Pre Order > Remainder -> Wish List)
    """
    IN_STOCK = 4
    PRE_ORDER = 3
    STOCK_REMAINDER = 1.5
    WISH_LIST = 1

    if is_salesable_item:
        if is_queueing_item and not is_stock_remainder:
            return PRE_ORDER
        elif not is_queueing_item and not is_stock_remainder:
            return IN_STOCK
        elif is_stock_remainder:
            return STOCK_REMAINDER
    else:
        return WISH_LIST


def prepare_stock_document(instance):

    data = {
        "id": instance.get("id"),
        "alias": instance.get("alias"),
        "status": instance.get("status"),
        "current_order_mode": prepare_current_order_mode(instance.get("product__order_mode")),
        "is_out_of_stock": prepare_is_out_of_stock(instance.get("orderable_stock"), instance.get("product__order_mode")),
        "delivery_date": prepare_delivery_date(instance.get("product__is_queueing_item")),
        "is_order_enabled": prepare_is_order_enabled(),
        "orderable_stock": instance.get("orderable_stock"),
        "organization": {
            "pk": instance.get("organization_id")
        },
        "store_point": {
            "pk": instance.get("store_point_id")
        },
        "ranking": get_ranking_value(
            instance.get("product__is_queueing_item"),
            instance.get("product__is_salesable"),
            prepare_is_out_of_stock(instance.get("orderable_stock"), instance.get("product__order_mode"))
        ),
        "product": {
            "id": instance.get("product_id"),
            "alias": instance.get("product__alias"),
            "order_mode": instance.get("product__order_mode"),
            "is_published": instance.get("product__is_published"),
            "is_queueing_item": instance.get("product__is_queueing_item"),
            "is_salesable": instance.get("product__is_salesable"),
            "trading_price": instance.get("product__trading_price"),
            "discount_rate": instance.get("product__discount_rate"),
            "product_discounted_price": instance.get("product__trading_price") - (instance.get("product__trading_price") * instance.get("product__discount_rate")) / 100,
            "order_limit_per_day": instance.get("product__order_limit_per_day"),
            "order_limit_per_day_mirpur": instance.get("product__order_limit_per_day_mirpur"),
            "order_limit_per_day_uttara": instance.get("product__order_limit_per_day_uttara"),
            "name": instance.get("product__name"),
            "name_not_analyzed": instance.get("product__name"),
            "image": prepare_image(instance.get("product__image"), "product_images"),
            "strength": instance.get("product__strength"),
            "display_name": instance.get("product__display_name"),
            "full_name": instance.get("product__full_name"),
            "generic": get_related_object(instance.get("product__generic__alias", ""), instance.get("product__generic__name")),
            "form": get_related_object(instance.get("product__form__alias", ""), instance.get("product__form__name")),
            "manufacturing_company": {
                "id": instance.get("product__manufacturing_company__id"),
                "alias": instance.get("product__manufacturing_company__alias"),
                "name": instance.get("product__manufacturing_company__name")
            },
            "subgroup": {
                "alias": instance.get("product__subgroup__alias"),
                "product_group": {
                    "alias": instance.get("product__subgroup__product_group__alias"),
                }
            }
        }
    }
    return data
