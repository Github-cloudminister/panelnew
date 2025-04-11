from hashlib import blake2b, sha1
import hmac, base64
from django.db.models import F
from requests import request


def hmac_sha1_encoding(encoded_key, encoded_URL):
    hashed = hmac.new(encoded_key, msg=encoded_URL, digestmod=sha1)
    digested_hash = hashed.digest()
    base64_encoded_result = base64.b64encode(digested_hash)
    final_result = base64_encoded_result.decode('utf-8').replace('+', '-').replace('/', '_').replace('=', '')
    return final_result

# ================ get object or none ==================
def _get_queryset(klass):
    """
    Return a QuerySet or a Manager.
    Duck typing in action: any class with a `get()` method (for
    get_object_or_404) or a `filter()` method (for get_list_or_404) might do
    the job.
    """
    # If it is a model class or anything else with ._default_manager
    if hasattr(klass, '_default_manager'):
        return klass._default_manager.all()
    return klass


def get_object_or_none(klass, *args, **kwargs):
    """
    Use get() to return an object, or raise a Http404 exception if the object
    does not exist.

    klass may be a Model, Manager, or QuerySet object. All other passed
    arguments and keyword arguments are used in the get() query.

    Like with QuerySet.get(), MultipleObjectsReturned is raised if more than
    one object is found.
    """
    queryset = _get_queryset(klass)
    if not hasattr(queryset, 'get'):
        klass__name = klass.__name__ if isinstance(klass, type) else klass.__class__.__name__
        raise ValueError(
            "First argument to get_object_or_none() must be a Model, Manager, "
            "or QuerySet, not '%s'." % klass__name
        )
    try:
        return queryset.get(*args, **kwargs)
    except Exception as e:
        return None
# ================ get object or none ==================


def callOfferWallApi(api_url, req_method="get", data=None, json=None):
    if data:
        offerwall_req = request(req_method, api_url, data=data)
    elif json:
        offerwall_req = request(req_method, api_url, json=json)
    else:
        offerwall_req = request(req_method, api_url)
    return offerwall_req


def callOpinionsDealApi(api_url, req_method="get", data=None, json=None):
    if data:
        opinionsdeal_req = request(req_method, api_url, data=data)
    elif json:
        opinionsdeal_req = request(req_method, api_url, json=json)
    else:
        opinionsdeal_req = request(req_method, api_url)
    return opinionsdeal_req