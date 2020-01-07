from pyramid.authentication import AuthTktCookieHelper
from pyramid.authorization import ACLHelper
from pyramid.csrf import CookieCSRFStoragePolicy
from pyramid.security import (
    Authenticated,
    Everyone,
)

from . import models


class MySecurityPolicy:
    def __init__(self, secret):
        self.authtkt = AuthTktCookieHelper(secret)
        self.acl = ACLHelper()

    def authenticated_identity(self, request):
        identity = self.authtkt.identify(request)
        if identity is None:
            return None

        userid = identity['userid']
        user = request.dbsession.query(models.User).get(userid)
        return user

    def authenticated_userid(self, request):
        user = self.authenticated_identity(request)
        if user is not None:
            return user.id

    def remember(self, request, userid, **kw):
        return self.authtkt.remember(request, userid, **kw)

    def forget(self, request, **kw):
        return self.authtkt.forget(request, **kw)

    def permits(self, request, context, permission):
        principals = self.effective_principals(request)
        return self.acl.permits(context, principals, permission)

    def effective_principals(self, request):
        principals = [Everyone]
        user = self.authenticated_identity(request)
        if user is not None:
            principals.append(Authenticated)
            principals.append('u:' + str(user.id))
            principals.append('role:' + user.role)
        return principals

def includeme(config):
    settings = config.get_settings()

    config.set_csrf_storage_policy(CookieCSRFStoragePolicy())
    config.set_default_csrf_options(require_csrf=True)

    config.set_security_policy(MySecurityPolicy(settings['auth.secret']))
    config.add_request_method(
        lambda request: request.authenticated_identity, 'user', property=True)
