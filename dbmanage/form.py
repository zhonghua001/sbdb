# -*- coding: utf-8 -*-
from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.forms import fields,widgets
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


