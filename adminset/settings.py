#-*-coding:utf8-*-
"""
Django settings for adminset project.

Generated by 'django-admin startproject' using Django 1.9.8.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os
import ConfigParser
import celery


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'n@s)3&f$tu#-^^%k-dj__th2)7m!m*(ag!fs=6ezyzb7l%@i@9'

CELERY_BROKER_URL = 'redis://localhost/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_BACKEND = 'django-db'
CELERY_TASK_SERIALIZER = 'json'
CELERY_ENABLE_UTC = True
CELERYD_MAX_TASKS_PER_CHILD = 3
CELERY_TIMEZONE = 'UTC'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# SECURITY WARNING: don't run with debug turned on in production!

CELERY_IMPORTS = (
    'dbmanage.myapp.include.mon',
)





DEBUG = True

ALLOWED_HOSTS = ['*']

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Application definition

INSTALLED_APPS = [
    'setup',
    'navi',
    'cmdb',
    'config',
    'accounts',
    'monitor',
    'appconf',
    'dbmanage',
    # 'dbmanage.monitor',
    'dbmanage.mongodb',
    'dbmanage.chartapi',
    'dbmanage.passforget',
    'dbmanage.blacklist',
    'dbmanage.myapp',
    'dbmanage.archer.sql',
    'dbmanage.bkrs',
    'django_celery_results',
    'django_celery_beat',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 'werkzeug_debugger_runserver',
    # 'django_extensions',


]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'adminset.urls'
# LOGIN_URL = '/accout/'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'),os.path.join(BASE_DIR, 'dbmanage/myapp/templates'),
                 os.path.join(BASE_DIR, 'dbmanage/monitor/templates'),os.path.join(BASE_DIR, 'dbmanage/bkrs/templates'),]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'dbmanage.archer.sql.processor.global_info',
            ],
        },
    },
]

WSGI_APPLICATION = 'adminset.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#     }
# }
config = ConfigParser.ConfigParser()
config.read(os.path.join(BASE_DIR, 'adminset.conf'))

DATABASES = {}
if config.get('db', 'engine') == 'mysql':
    DB_HOST = config.get('db', 'host')
    DB_PORT = config.getint('db', 'port')
    DB_USER = config.get('db', 'user')
    DB_PASSWORD = config.get('db', 'password')
    DB_DATABASE = config.get('db', 'database')
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': DB_DATABASE,
            'USER': DB_USER,
            'PASSWORD': DB_PASSWORD,
            'HOST': DB_HOST,
            'PORT': DB_PORT,
        }
    }
elif config.get('db', 'engine') == 'sqlite':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': config.get('db', 'database'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }


EMAIL_HOST='smtp.163.com'
EMAIL_HOST_USER='ljd8210@163.com'
EMAIL_HOST_PASSWORD='2528107752'
EMAIL_PORT = 25
EMAIL_SENDER = 'ljd8210@163.com'
# EMAIL_USE_TLS = True
# URL_FOR_PASSWD = 'http://192.168.70.128:8000'




SELECT_LIMIT = int(config.get('db_platform','select_limit'))
EXPORT_LIMIT = int(config.get('db_platform','export_limit'))
WRONG_MSG = config.get('db_platform','wrong_msg')
SQLADVISOR_SWITCH = int(config.get('db_platform','sqladvisor_switch'))
SQLADVISOR = config.get('db_platform','sqladvisor')
PT_TOOL = config.get('db_platform','pt_tool')
PATH_TO_MYSQLDIFF = config.get('db_platform','path_to_mysqldiff')

PUBLIC_USER = config.get('db_platform','public_user')
PTTOOL_SWITCH = config.get('db_platform','pt_tool')
PTTOOL_PATH = config.get('db_platform','pt_tool_path')

#inception组件所在的地址
INCEPTION_USER = config.get('db_platform','incp_user')
INCEPTION_PASSWORD = config.get('db_platform','incp_passwd')
INCEPTION_HOST = config.get('db_platform','incp_host')
INCEPTION_PORT = config.get('db_platform','incp_port')
#查看回滚SQL时候会用到，这里要告诉archer去哪个mysql里读取inception备份的回滚信息和SQL.
#注意这里要和inception组件的inception.conf里的inception_remote_XX部分保持一致.
INCEPTION_REMOTE_BACKUP_HOST=config.get('db_platform','incept_backup_host')
INCEPTION_REMOTE_BACKUP_PORT=config.get('db_platform','incept_backup_port')
INCEPTION_REMOTE_BACKUP_USER=config.get('db_platform','incept_backup_user')
INCEPTION_REMOTE_BACKUP_PASSWORD=config.get('db_platform','incept_backup_passwd')
#是否开启邮件提醒功能：发起SQL上线后会发送邮件提醒审核人审核，执行完毕会发送给DBA. on是开，off是关，配置为其他值均会被archer认为不开启邮件功能
MAIL_ON_OFF=config.get('db_platform','MAIL_ON_OFF')
MAIL_REVIEW_SMTP_SERVER=config.get('db_platform','MAIL_REVIEW_SMTP_SERVER')
MAIL_REVIEW_SMTP_PORT=config.get('db_platform','MAIL_REVIEW_SMTP_PORT')
MAIL_REVIEW_FROM_ADDR=config.get('db_platform','MAIL_REVIEW_FROM_ADDR')                                         #发件人，也是登录SMTP server需要提供的用户名
MAIL_REVIEW_FROM_PASSWORD=config.get('db_platform' ,'MAIL_REVIEW_FROM_PASSWORD')                                                    #发件人邮箱密码，如果为空则不需要login SMTP server
MAIL_REVIEW_DBA_ADDR=config.get('db_platform' ,'MAIL_REVIEW_DBA_ADDR')      #DBA地址，执行完毕会发邮件给DBA，以list形式保存
#是否过滤【DROP DATABASE】|【DROP TABLE】|【TRUNCATE PARTITION】|【TRUNCATE TABLE】等高危DDL操作：
#on是开，会首先用正则表达式匹配sqlContent，如果匹配到高危DDL操作，则判断为“自动审核不通过”；off是关，直接将所有的SQL语句提交给inception，对于上述高危DDL操作，只备份元数据
CRITICAL_DDL_ON_OFF=config.get('db_platform','CRITICAL_DDL_ON_OFF')


# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/
# sys.path.append(os.path.join(BASE_DIR, 'vendor').replace('\\', '/'))
#STATIC_ROOT = os.path.join(APP_PATH,'static').replace('\\','/')
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static').replace('\\', '/'),
)
'''
REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ]
}
'''
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    )
}

AUTH_USER_MODEL = 'accounts.UserInfo'





LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
    },
}



SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_AGE=60*30