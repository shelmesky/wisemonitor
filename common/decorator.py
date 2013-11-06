import functools

def require_login(method):
    def wrapper(self, *args, **kwargs):
        user = self.get_secure_cookie("wisemonitor_user")
        if not user:
            self.redirect("/login/")
        else:
            return method(self, *args, **kwargs)
    return wrapper
