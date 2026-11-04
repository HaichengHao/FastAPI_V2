
auth_prefix = f'/api/v1/auth'
def test_user_creation(fake_session,fake_user_service,test_client):
    signup_data = {
            "username":"fake_username",
            "email":"fakemail@163.com",
            "first_name":"fake_first_name",
            "last_name":"fake_last_name",
            "password":"fake_password",
        }
    response = test_client.post(
        url=f'{auth_prefix}/signup',
        json=signup_data
    )

    assert fake_user_service.user_exists_called_once()
    assert fake_user_service.user_exists_called_once_with(signup_data['email'],fake_session)


