from helpers.payment_providers.base import PROVIDER_STATUS_COMING_SOON, unavailable_payment


provider_id = "tripay"
display_name = "Tripay"
status = PROVIDER_STATUS_COMING_SOON
capabilities = {
    "supports_payment_link": True,
    "supports_qris": True,
    "supports_va": True,
    "supports_webhook": False,
}

create_payment = unavailable_payment
check_payment_status = unavailable_payment
get_payment_status = unavailable_payment


def validate_config(*_args, **_kwargs):
    return False
