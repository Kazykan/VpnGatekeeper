from datetime import date, timedelta
import pytest

from myapp.domain.credentials.exceptions import NoActiveSubscription
from myapp.domain.credentials.services import generate_new_config_for_user


@pytest.mark.django_db
def test_old_configs_are_blocked(
    user_factory, credential_factory, server_factory, mocker
):
    user = user_factory(end_date=date.today() + timedelta(days=10))
    old_server = server_factory(name="Old_server", type="amnezia")

    cred = credential_factory(
        user=user,
        wg_conf_old_server=True,
        wg_conf_ip="10.0.0.2",
        active=True,
    )

    mock_gateway = mocker.patch("myapp.domain.vpn.services.AmneziaGateway")

    generate_new_config_for_user(user)

    cred.refresh_from_db()
    assert not cred.active
    mock_gateway.return_value.block_ip.assert_called_once_with("10.0.0.2")


@pytest.mark.django_db
def test_no_subscription(user_factory):
    user = user_factory(end_date=date.today() - timedelta(days=1))

    with pytest.raises(NoActiveSubscription):
        generate_new_config_for_user(user)
