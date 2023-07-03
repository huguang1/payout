# -*- coding: utf-8 -*-
# 18-11-3 下午1:21
# AUTHOR:June
from django.conf.urls import url
from major.views import LoginView, LogoutView, IndexView, LoginRecView, SetPwdView\
    , UploadDataView, SearchView, SendView, AduLogView, AduLogpageView, BatchDeleteView, DownloadInfoView\
    , UploadRecord,AdgManageView,AduManageView,DeleteView,SearchAdminView,LoginRecSearchView\
    , AddGroupView,DelGroupView,SearchGroupView,VerifyCodeView

app_name = 'major'
urlpatterns = [
    url(r'^login$', LoginView.as_view(), name='login'),
    url(r'^logout$', LogoutView.as_view(), name='logout'),
    url(r'^index$', IndexView.as_view(), name='index'),
    url(r'^loginrecs/(?P<page>\d+)$', LoginRecView.as_view(), name='loginRec'),
    url(r'^uploadData$', UploadDataView.as_view(), name='uploadData'),  # end june
    url(r'^search$', SearchView.as_view(), name='search'),
    url(r'^send$', SendView.as_view(), name='send'),
    url(r'^adulog$', AduLogView.as_view(), name='adulog'),
    url(r'^adulogpage$', AduLogpageView.as_view(), name='adulogpage'),
    url(r'^batchdelete$', BatchDeleteView.as_view(), name='batchdelete'),
    url(r'^downloadinfo$', DownloadInfoView.as_view(), name='downloadinfo'),
    url(r'^uploadrecord$', UploadRecord.as_view(), name='uploadrecord'),  # end li
    url(r'^updatepwd/(?P<page>\d+)$', SetPwdView.as_view(), name='updatepwd'),
    url(r'^delete$', DeleteView.as_view(), name='delete'),  # 删除用户
    url(r'^adumanage/(?P<page>\d+)$', AduManageView.as_view(), name='adumanage'),
    url(r'^adgmanage/(?P<page>\d+)$', AdgManageView.as_view(), name='adgmanage'),
    url(r'^delgroup$', DelGroupView.as_view(), name='delgroup'),
    url(r'^addgroup$', AddGroupView.as_view(), name='AddGroupView'),
    url(r'^search/group$', SearchGroupView.as_view(), name='addgroup'),
    url(r'^search/admin$', SearchAdminView.as_view(), name='searchadmin'),
    url(r'^login/search/(?P<page>\d+)$', LoginRecSearchView.as_view(), name='loginrecsearch'),  # end tang
    url(r'^verifycode$', VerifyCodeView.as_view(), name='verifycode'),
]