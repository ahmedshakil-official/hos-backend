from django.db.models.query import QuerySet

from elasticsearch_dsl import Q

from common.tasks import get_documents


def update_stock_es_doc(filters=None, queryset=None):
    filters = filters if filters else {}
    model_string = "pharmacy.models.Stock"
    parallel = True
    refresh = True
    for doc in get_documents(model_string):
        # qs = doc().get_indexing_queryset(filters)
        if isinstance(queryset, QuerySet):
            qs = doc().get_queryset(queryset=queryset)
        else:
            qs = doc().get_queryset(filters)
        doc().update(qs, parallel=parallel, refresh=refresh)


def search_by_multiple_aliases(request, search):
    """
    This methdod apply search by multiple aliases.
    The query parameter should be aliases.
    Returns True or False with search for setting pagination size.
    """
    aliases = request.query_params.get("aliases", None)
    # If aliases exists in the query paramter then apply filter and return filtered search.
    if aliases:
        search = search.query(
            Q("match", alias=aliases)
        )
        return search, True

    return search, False

def update_order_invoice_group_es_doc(filters=None, _queryset=None):
    filters = filters if filters else {}
    model_string = "ecommerce.models.OrderInvoiceGroup"
    parallel = True
    refresh = True
    for doc in get_documents(model_string):
        if isinstance(_queryset, QuerySet):
            qs = doc().get_queryset(_queryset=_queryset)
        else:
            qs = doc().get_queryset(filters)
        doc().update(qs, parallel=parallel, refresh=refresh)
