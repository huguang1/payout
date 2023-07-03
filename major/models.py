from django.db import models
from django.contrib.auth.models import AbstractUser
from payout import settings
# Create your models here.

usermodels = settings.AUTH_USER_MODEL


class User(AbstractUser):

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = verbose_name


class AdminPermission(models.Model):
    name = models.CharField('权限', max_length=15)


class AdminGroup(models.Model):
    name = models.CharField('组名', max_length=15)
    permission = models.ManyToManyField(AdminPermission, verbose_name='权限')
    group_user = models.ManyToManyField(usermodels, '用户')


class Record(models.Model):
    name = models.CharField('姓名', max_length=20)
    money = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='彩金')
    qq = models.CharField('QQ', max_length=20)
    tel = models.CharField('电话号码', max_length=20)
    email = models.CharField('邮箱', max_length=20)
    state = models.BooleanField('状态', default=False)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    send_time = models.DateTimeField('派送时间', blank=True, null=True)
    operator = models.CharField('操作人', max_length=20, blank=True, null=True)


class Login(models.Model):
    name = models.CharField('姓名', max_length=20)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='操作时间')
    state = models.BooleanField('操作类型')
    ip = models.GenericIPAddressField('IP地址')


class Upload(models.Model):
    dataname = models.CharField('数据名称', max_length=32)
    create_time = models.DateTimeField('上传时间', auto_now_add=True)
    filename = models.CharField('文件名称', max_length=20)
    number = models.IntegerField('导入数量')
    bywho = models.CharField('上传人', max_length=20)
