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
    distributors = [FileDistributor()]
    if email_config:
        distributors.append(EmailDistributor(email_config))
    distributors.append(TelegramDistributor())
    return distributors


def get_distributor(name: str, **kwargs) -> Distributor:
    if name in DISTRIBUTOR_REGISTRY:
        return DISTRIBUTOR_REGISTRY[name](**kwargs)
    raise ValueError(f"Unknown distributor: {name}")