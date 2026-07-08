from .base import Distributor, Report
from .email import EmailDistributor
from .telegram import TelegramDistributor
from .file import FileDistributor


DISTRIBUTOR_REGISTRY = {
    "email": EmailDistributor,
    "telegram": TelegramDistributor,
    "file": FileDistributor,
}


def get_all_distributors(email_config: dict = None):
    distributors = []
    for name, cls in DISTRIBUTOR_REGISTRY.items():
        if name == "email" and email_config:
            distributors.append(cls(email_config))
        elif name != "email":
            distributors.append(cls())
    return distributors


def get_distributor(name: str, **kwargs) -> Distributor:
    if name in DISTRIBUTOR_REGISTRY:
        return DISTRIBUTOR_REGISTRY[name](**kwargs)
    raise ValueError(f"Unknown distributor: {name}")
