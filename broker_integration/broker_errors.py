"""Broker integration errors."""


class BrokerAdapterError(Exception):
    pass


class MissingCredentialsError(BrokerAdapterError):
    pass


class LiveTradingRejectedError(BrokerAdapterError):
    pass


class DependencyMissingError(BrokerAdapterError):
    pass


class StaleDataError(BrokerAdapterError):
    pass


class WideSpreadError(BrokerAdapterError):
    pass
