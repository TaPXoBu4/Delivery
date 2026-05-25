from flask_login import LoginManager, UserMixin

login_manager = LoginManager()


class FlaskUser(UserMixin):
    def __init__(self, domain_user):
        self._user = domain_user
        self.id = domain_user.id
        self.name = domain_user.name
        self.is_admin = domain_user.is_admin


@login_manager.user_loader
def load_user(user_id):
    from flask import current_app

    use_cases = current_app.extensions["use_cases"]
    user = use_cases.get_user(int(user_id))
    if user:
        return FlaskUser(user)
    return None
