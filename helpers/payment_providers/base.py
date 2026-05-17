from dataclasses import asdict, dataclass, field


PROVIDER_STATUS_AVAILABLE = "available"
PROVIDER_STATUS_COMING_SOON = "coming_soon"
PROVIDER_STATUS_UNSUPPORTED = "unsupported"
PROVIDER_UNAVAILABLE_MESSAGE = "Provider pembayaran ini belum tersedia."


@dataclass(frozen=True)
class PaymentProviderInfo:
    provider_id: str
    display_name: str
    status: str
    capabilities: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


def unavailable_payment(*_args, **_kwargs):
    raise ValueError(PROVIDER_UNAVAILABLE_MESSAGE)


def default_validate_config(*_args, **_kwargs):
    return True
