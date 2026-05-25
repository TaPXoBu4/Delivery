from werkzeug.security import check_password_hash, generate_password_hash


class WerkzeugPasswordHasher:
    def hash(self, password: str) -> str:
        return generate_password_hash(password)

    def verify(self, password: str, password_hash: str | None) -> bool:
        if not password_hash:
            return False
        return check_password_hash(password_hash, password)
