# -*- coding: utf-8 -*-
# 18-11-10 下午3:17
# AUTHOR:June
import functools
from major.models import AdminGroup,AdminPermission
from django.http import HttpResponseForbidden
from django.db.models import Q


def group_required(module):
    def _group_required(func):
        @functools.wraps(func)
        def wrapper(self, request, *args, **kwargs):
            login_user = request.user
            if login_user.is_superuser:
                return func(self, request, *args, **kwargs)
            try:
                if isinstance(module, list):
                    one = AdminPermission.objects.get(name=module[0])
                    two = AdminPermission.objects.get(name=module[1])
                    group_objs = AdminGroup.objects.filter(Q(permission=one)|Q(permission=two)).all()
                else:
                    pmsion = AdminPermission.objects.get(name=module)
                    group_objs = AdminGroup.objects.filter(permission=pmsion).all()
                login_group = AdminGroup.objects.get(group_user=login_user)
            except Exception as e:
                return HttpResponseForbidden()
            if login_group not in group_objs:
                return HttpResponseForbidden()
            # user_list = []
            # for i in group_objs:
            #    for p in i.group_user.all():
            #        user_list.append(p.username)
            # if login_user.username not in user_list:
            #     return HttpResponseForbidden()
            return func(self, request, *args, **kwargs)
        return wrapper
    return _group_required
