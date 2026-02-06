import datetime


def test_authorization_code_expires_in_future(app):
    with app.app_context():
        from src.models import VC_AuthorizationCode, db

        now = datetime.datetime.now(datetime.timezone.utc)
        entry = VC_AuthorizationCode(client_id="test-client", code_challenge="abc")
        db.session.add(entry)
        db.session.commit()

        assert entry.expires_at is not None
        # expires_at must be strictly in the future
        assert entry.expires_at > now


def test_token_expires_in_future(app):
    with app.app_context():
        from src.models import VC_Token, db

        now = datetime.datetime.now(datetime.timezone.utc)
        token = VC_Token(token="tok-1")
        db.session.add(token)
        db.session.commit()

        assert token.expires_at is not None
        assert token.expires_at > now
