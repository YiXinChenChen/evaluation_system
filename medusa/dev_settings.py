import os

DEBUG = True

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'management',
    'sqa',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'subjective_test',
        'USER': 'subjective_test',
        'PASSWORD': '123456',
        'HOST': '172.19.101.12',
        'PORT': '',
    }
}
