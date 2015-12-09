from google.appengine.api import users
import webapp2

class AuthHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()

        if user:
            greeting = ('Welcome, %s! (<a href="%s">sign out</a>)' %
                        (user.nickname(), users.create_logout_url('/authtest')))

            if users.is_current_user_admin():
                greeting += ' <span>admin user</span>'
            else:
                greeting += ' <span>ordinary user</span>'

        else:
            greeting = ('<a href="%s">Sign in or register</a>.' %
                        users.create_login_url('/authtest'))

        self.response.out.write('<html><body>%s</body></html>' % greeting)

app = webapp2.WSGIApplication([
    ('/authtest', AuthHandler),
], debug=True)
