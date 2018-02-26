# -*- coding: utf-8 -*-
from django import forms
# from captcha.fields import CaptchaField
from dbmanage.myapp.models import Db_group,Db_name,Db_account,Db_instance,Oper_log,Upload,Task
from django.contrib.admin import widgets as adminwidgets
from django.forms import fields,widgets
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User
from django.core import validators
class LoginForm(forms.Form):
    username = forms.CharField(

        required=True,
        max_length=25,
        label="用户名:",
        error_messages={'required': u'请输入用户名'},
        widget=forms.TextInput(
            attrs={
                'placeholder':u"用户名",
            }
        ),
    )
    password = forms.CharField(
    required=True,
    max_length=25,
    label="密码:",
    error_messages={'required': u'请输入密码'},
    widget=forms.PasswordInput(
        attrs={
            'placeholder': u"密码",
            }
        ),
    )
    # captcha = CaptchaField(label="输入验证码:",)
    def clean(self):
        if not self.is_valid():
            raise forms.ValidationError(u"用户名和密码为必填项")
        else:
            cleaned_data = super(LoginForm, self).clean()

# class Userpri_form(forms.Form):
#     accountname = forms.CharField(max_length=25)

class AddForm (forms.Form):
    a = forms.CharField(widget=forms.Textarea(attrs={'id':"code","class":'col-md-12', 'display': 'none'}),required=False)

class SqlForm (forms.Form):
    a = forms.CharField(widget=forms.Textarea(attrs={'cols': 80, 'rows': 15}))
    filename = forms.FileField()

class Logquery(forms.Form):
    begin = forms.DateTimeField(label='dateinfo')
    end = forms.DateTimeField()

class Taskquery(forms.Form):
    end = forms.DateTimeField()

class Taskscheduler(forms.Form):
    sche_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'class':'period_date'}))
    expire_date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'class':'expire_date'}))


class Uploadform(forms.Form):
    filename = forms.FileField(required=False)

# class Captcha(forms.Form):
#     mycaptcha = CaptchaField(label="验证码:",)


class Dbgroupform(forms.ModelForm):
    class Meta:
        model = Db_group
        fields = '__all__'


class AddDBAccount(forms.Form):

    port = fields.IntegerField(
        required=True,
        widget=widgets.TextInput(attrs={'class': "form-control", 'placeholder': 'input port'}),

        error_messages={'required': 'Port不能为空',
                                                },
    )
    comment = fields.CharField(
        required=False,
        widget=widgets.TextInput(attrs={'class': "form-control", 'placeholder': '使用说明,少于20个字符'}),
        max_length=50,
        strip=True,
        error_messages={'max_length': '使用说明,少于20个字符'}
    )

    normal_db_account = fields.CharField(
        required=False,
        widget=widgets.TextInput(attrs={'class': "form-control", 'placeholder': '用户名为4-30个字符'}),
        min_length=4,
        max_length=30,
        strip=True,
        error_messages={'required': '标题不能为空',
                        'min_length': '用户名最少为4个字符',
                        'max_length': '用户名最不超过为30个字符'},
    )

    normal_db_password = fields.CharField(
        widget=widgets.PasswordInput(attrs={'class': "form-control", 'placeholder': '请输入密码，必须包含数字,字母,特殊字符'},
                                     render_value=True),
        required=False,
        min_length=8,
        max_length=30,
        strip=True,
        validators=[
            # 下面的正则内容一目了然，我就不注释了
            RegexValidator(r'([^a-z0-9A-Z])+', '必须包含特殊字符'),
            RegexValidator(r'[A-Z]+', '必须包含da字母'),
            RegexValidator(r'[a-z]+', '必须包含x字母'),
            # RegexValidator(r' ', '密码不能包含空白字符'),
            RegexValidator(r'[0-9]+', '必须包含数字'),
        ],  # 用于对密码的正则验证
        error_messages={'required': '密码不能为空!',
                        'min_length': '密码最少为8个字符',
                        'max_length': '密码最多不超过为30个字符!', },
    )
    normal_db_password_again = fields.CharField(

        # render_value会对于PasswordInput，错误是否清空密码输入框内容，默认为清除，我改为不清楚
        widget=widgets.PasswordInput(attrs={'class': "form-control", 'placeholder': '请再次输入密码!'}, render_value=True),
        required=False,
        strip=True,

        error_messages={

                        'required': '请再次输入密码!', }

    )

    admin_db_account = fields.CharField(
        required=False,
        widget=widgets.TextInput(attrs={'class': "form-control", 'placeholder': '用户名为4-30个字符'}),
        min_length=4,
        max_length=30,
        strip=True,
        error_messages={'required': '标题不能为空',
                        'min_length': '用户名最少为4个字符',
                        'max_length': '用户名最不超过为30个字符'},
    )

    admin_db_password = fields.CharField(
        widget=widgets.PasswordInput(attrs={'class': "form-control", 'placeholder': '请输入密码，必须包含数字,字母,特殊字符'},
                                     render_value=True),
        required=False,
        min_length=8,
        max_length=30,
        strip=True,
        validators=[
            # 下面的正则内容一目了然，我就不注释了
            RegexValidator(r'([^a-z0-9A-Z])+', '必须包含特殊字符'),
            RegexValidator(r'[A-Z]+', '必须包含大写字母'),
            RegexValidator(r'[a-z]+', '必须包含小写字母'),
            # RegexValidator(r' ', '密码不能包含空白字符'),
            RegexValidator(r'[0-9]+','必须包含数字'),
        ],  # 用于对密码的正则验证
        error_messages={'required': '密码不能为空!',
                        'min_length': '密码最少为8个字符',
                        'max_length': '密码最多不超过为30个字符!', },
    )
    admin_db_password_again = fields.CharField(
        # render_value会对于PasswordInput，错误是否清空密码输入框内容，默认为清除，我改为不清楚
        widget=widgets.PasswordInput(attrs={'class': "form-control", 'placeholder': '请再次输入密码!'}, render_value=True),
        required=False,
        strip=True,
        error_messages={'required': '请再次输入密码!', }

    )
    def clean_username(self):
        # 对username的扩展验证，查找用户是否已经存在
        username = self.cleaned_data.get('username')
        # users = models.User.objects.filter(username=username).count()
        # if users:
        #     raise ValidationError('用户已经存在！')
        return username



    def _clean_new_password2(self):  # 查看两次密码是否一致
        password1 = self.cleaned_data.get('normal_db_password')
        password2 = self.cleaned_data.get('normal_db_password_again')

        if password1 != password2:
                # self.error_dict['pwd_again'] = '两次密码不匹配'
                # raise ValidationError('两次密码不匹配！')
            self.add_error('normal_db_password_again', '两次密码不匹配')
        password3 = self.cleaned_data.get('admin_db_password')
        password4 = self.cleaned_data.get('admin_db_password_again')

        if password3 != password4:
                # self.error_dict['pwd_again'] = '两次密码不匹配'
            self.add_error('admin_db_password_again','两次密码不匹配')
                # raise ValidationError(('两次密码不匹配！'),
                #                      code = 'error4'
                #                       )

    def check_data(self):
        if len(self.cleaned_data['normal_db_account']) == 0 and len(self.cleaned_data['admin_db_account']) == 0:
            raise ValidationError(('Normal用户和admin用户至少有一个，不能全为空'))

    def clean(self):
        # 是基于form对象的验证，字段全部验证通过会调用clean函数进行验证
        self._clean_new_password2()  # 简单的调用而已
        self.check_data()






class AddDBAccountSetDB(forms.Form):



    normal_db_account = fields.CharField(
        required=False,
        widget=widgets.TextInput(attrs={'class': "form-control", 'placeholder': '用户名为4-30个字符'}),
        min_length=4,
        max_length=30,
        strip=True,
        error_messages={'required': '标题不能为空',
                        'min_length': '用户名最少为4个字符',
                        'max_length': '用户名最不超过为30个字符'},
    )

    normal_db_password = fields.CharField(
        widget=widgets.PasswordInput(attrs={'class': "form-control", 'placeholder': '请输入密码，必须包含数字,字母,特殊字符'},
                                     render_value=True),
        required=False,
        min_length=8,
        max_length=30,
        strip=True,
        validators=[
            # 下面的正则内容一目了然，我就不注释了
            RegexValidator(r'([^a-z0-9A-Z])+', '必须包含特殊字符'),
            RegexValidator(r'[A-Z]+', '必须包含da字母'),
            RegexValidator(r'[a-z]+', '必须包含x字母'),
            # RegexValidator(r' ', '密码不能包含空白字符'),
            RegexValidator(r'[0-9]+', '必须包含数字'),
        ],  # 用于对密码的正则验证
        error_messages={'required': '密码不能为空!',
                        'min_length': '密码最少为8个字符',
                        'max_length': '密码最多不超过为30个字符!', },
    )
    normal_db_password_again = fields.CharField(

        # render_value会对于PasswordInput，错误是否清空密码输入框内容，默认为清除，我改为不清楚
        widget=widgets.PasswordInput(attrs={'class': "form-control", 'placeholder': '请再次输入密码!'}, render_value=True),
        required=False,
        strip=True,

        error_messages={

                        'required': '请再次输入密码!', }

    )




    def _clean_new_password2(self):  # 查看两次密码是否一致
        password1 = self.cleaned_data.get('normal_db_password')
        password2 = self.cleaned_data.get('normal_db_password_again')

        if password1 != password2:
                # self.error_dict['pwd_again'] = '两次密码不匹配'
                # raise ValidationError('两次密码不匹配！')
            self.add_error('normal_db_password_again', '两次密码不匹配')

    def check_data(self):
        if self.cleaned_data.get('normal_db_account') is None or self.cleaned_data.get('normal_db_password') is None or self.cleaned_data.get('normal_db_password_again') is None:
            self.add_error('normal_db_account','User and password can not be empty')

    def clean(self):
        # 是基于form对象的验证，字段全部验证通过会调用clean函数进行验证
        self._clean_new_password2()  # 简单的调用而已
        self.check_data()











