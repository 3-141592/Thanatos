from rauth import OAuth1Service, OAuth2Service
from flask import current_app, url_for, request, redirect, session
from random import randint

class OAuthSignIn(object):
    providers = None

    def __init__(self, provider_name):
        self.provider_name = provider_name
        credentials = current_app.config['OAUTH_CREDENTIALS'][provider_name]
        self.consumer_id = credentials['id']
        self.consumer_secret = credentials['secret']

    def authorize(self):
        pass

    def callback(self):
        pass

    def get_callback_url(self):
        return url_for('oauth_callback', provider=self.provider_name,
                       _external=True)

    @classmethod
    def get_provider(self, provider_name):
        if self.providers is None:
            self.providers = {}
            for provider_class in self.__subclasses__():
                provider = provider_class()
                self.providers[provider.provider_name] = provider
        return self.providers[provider_name]

class GitHubSignIn(OAuthSignIn):
    def __init__(self):
        super(GitHubSignIn, self).__init__('github')
        self.state = randint(1000,5000)
        self.service = OAuth2Service(
        name='github',
        client_id=self.consumer_id,
        client_secret = self.consumer_secret,
        authorize_url = 'https://github.com/login/oauth/authorize',
        access_token_url = 'https://github.com/login/oauth/access_token',
        base_url = 'https://api.github.com'
        )

    def authorize(self):
        return redirect(self.service.get_authorize_url(scope='',state=str(self.state),redirect_uri=self.get_callback_url()))


    def callback(self):
        if 'code' not in request.args or 'state' not in request.args or request.args['state'] != str(self.state):
            return None,None,None
        oauth_session = self.service.get_auth_session(
        data={'code':request.args['code'],
        'redirect_uri':self.get_callback_url(),
        'state':str(self.state)
        }
        )
        print request.args
        me = oauth_session.get('user').json()
        print me
        return ('github$'+str(me['id']),me['login'],me['email'])
