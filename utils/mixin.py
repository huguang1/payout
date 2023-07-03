# -*- coding: utf-8 -*-
# 18-11-3 下午12:47
# AUTHOR:June
from django.views.generic import View
from django.contrib.auth.decorators import login_required


class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        # 使用super调用as_view
        view = super().as_view(**initkwargs)

        # 调用login_required装饰器函数
        return login_required(view)
