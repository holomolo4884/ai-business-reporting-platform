from rest_framework.throttling import AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """
    Rate limit для endpoint'а логина.

    Защищает от брутфорс атак: не более 5 попыток в минуту.
    """

    scope = "login"
