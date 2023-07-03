from django.shortcuts import render, redirect
from utils.VerifyCode import VerifyCode
from utils.mixin import LoginRequiredMixin
from utils.script import insert_data
from django.views.generic import View
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from major.models import Record, User, Login, Upload, AdminGroup,AdminPermission
from django.core.paginator import Paginator
from django.utils.timezone import make_aware
import os
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
import csv
import json
import datetime
from utils.required import group_required
import random
import datetime


# Create your views here.
class LoginView(View):
    """登录视图"""
    def get(self, request):  # 显示登录页面
        randomnum = random.random()
        return render(request, 'login.html', {'randomnum': randomnum})

    def post(self,request):  # 登录（按钮）请求
        # 获取ip信息
        if 'HTTP_X_FORWARDED_FOR' in request.META.values():
            ip = request.META['HTTP_X_FORWARDED_FOR']
        else:
            ip = request.META['REMOTE_ADDR']
        yzm = request.POST.get('chkcode')
        verifycode = request.session['verifycode']
        if yzm.lower() != verifycode.lower():
            return render(request, 'login.html', {'errmsg': '参数不完整'})

        # 1.接收参数
        username = request.POST.get('username')
        password = request.POST.get('password')

        # 2.参数校验(后端校验)
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '参数不完整'})

        # 3.业务处理：登录校验
        user = authenticate(username=username, password=password)
        if user is not None:
            # 用户名和密码正确
            if user.is_active:
                # 用户已激活
                # 记住用户的登录状态
                login(request, user)
                Login.objects.create(name=username, state=True, ip=ip)
                # 获取用户登录之前访问的url地址，默认跳转到首页
                next_url = request.GET.get('next', reverse('major:index')) # None
                # 跳转到next_url
                response = redirect(next_url)  # HttpResponseRedirect
                # 跳转到首页
                return response
            else:
                # 用户未激活
                return render(request, 'login.html', {'errmsg': '用户未激活'})
        else:
            # 用户名或密码错误
            Login.objects.create(name=username, state=False, ip=ip)
            return render(request, 'login.html', {'errmsg': '用户名或密码错误，请重新输入！'})


class LogoutView(View):
    """退出"""
    def get(self, request):
        """退出"""
        # 清除用户登录状态
        logout(request)

        # 跳转到登录
        return redirect(reverse('major:login'))


class IndexView(LoginRequiredMixin, View):
    """首页视图"""
    def get(self, request):
        not_sent = Record.objects.filter(state=False).count()  # 未派的数数量
        sent = Record.objects.filter(state=True).count()  # 已派送人数
        context = {
            "total": format(not_sent+sent, ','),  # 记录总数
            "not_sent": format(not_sent, ','),  # 未发送
            "sent": format(sent, ',')  # 已发送
        }
        return render(request, 'index.html', context)


class LoginRecView(LoginRequiredMixin, View):
    """登录记录视图"""
    @group_required('管理员模块')  # 权限装饰器，传入该接口所需要权限
    def get(self, request, page):  # 显示登录记录
        login_recs = Login.objects.all().order_by('-create_time')  # 获取所有登录记录，根据时间倒序
        paginator = Paginator(login_recs, 9)  # 分页，每页9条数据
        page = int(page)   # 前端传入页面，转换为int类型
        if page > paginator.num_pages:  # 传入页码page大于分页后的总页码，重置page为1
            page = 1
        # 获取第page页内容, 返回Page类的实例对象
        login_rec = paginator.page(page)
        num_pages = paginator.num_pages  # 总页码
        if num_pages < 5:  # 如果总页码<5
            pages = range(1, num_pages+1)  # 前端显示页码为 1 到 总页码+1
        elif page <= 3:  # 总页码不少于5，并且前端输入页码<=3时， 前端显示页码应为 1-5页
            pages = range(1, 6)
        elif num_pages - page <=2:  # 总页码-前端传入的页码 <=2时， 前端应显示 总页码-4 到总页码
            # num_pages-4, num_pages
            pages = range(num_pages-4, num_pages+1)
        else:
            # 除以上情况，前端都应该显示 前端传入页码-2 至 前端传入页码+3
            pages = range(page-2, page+3)
        context = {
            "pages": pages,  # 前端显示页码
            "login_rec": login_rec  # 登录记录
        }
        return render(request, 'aduRecord.html', context)

    @group_required('管理员模块')
    def post(self, request, page):  # 搜索登录记录
        search_word = request.POST.get('search_val')  # 搜索词
        try:
            user = User.objects.get(username=search_word)
        except Exception as e:
            return JsonResponse({"stat": 1})  # 搜索失败，没有该用户记录
        login_rec = Login.objects.filter(name=user.username).order_by('-create_time')  # 获取该用户的所有记录时间倒序
        rec_list = []
        for rec in login_rec:
            data = {
                "id": rec.id,
                "name": rec.name,
                "login_ip": rec.ip,  # ip
                "login_time": (rec.create_time+datetime.timedelta(hours=8)). strftime("%Y-%m-%d %H:%M:%S"),  # 登录时间
                "login_type": '登陆成功' if rec.state else '登陆失败',
            }
            rec_list.append(data)
        return JsonResponse({"stat": 0, "data": rec_list})


class SetPwdView(LoginRequiredMixin, View):
    """ 修改管理员"""
    @group_required('管理员模块')
    def get(self, request, page):  # 显示修改管理员页面
        groups = AdminGroup.objects.all()  # 获取所有组
        obj_list = []
        for obj in groups:
            group_data = {
                'name': obj.name,
                'id': obj.id
            }
            obj_list.append(group_data)
        users = User.objects.all().order_by('id')  # 获取所有用户
        paginator = Paginator(users, 8)  # 分页，每页8条数据
        page = int(page)  # 前端传入页面，转换为int类型
        if page > paginator.num_pages:  # 传入页码page大于分页后的总页码，重置page为1
            page = 1
        # 获取第page页内容, 返回Page类的实例对象
        user_objs = paginator.page(page)
        num_pages = paginator.num_pages  # 总页码
        if num_pages < 5:  # 如果总页码<5
            pages = range(1, num_pages+1)  # 前端显示页码为 1 到 总页码+1
        elif page <= 3:  # 总页码不少于5，并且前端输入页码<=3时， 前端显示页码应为 1-5页
            pages = range(1, 6)
        elif num_pages - page <=2:  # 总页码-前端传入的页码 <=2时， 前端应显示 总页码-4 到总页码
            pages = range(num_pages-4, num_pages+1)
        else:
            # 除以上情况，前端都应该显示 前端传入页码-2 至 前端传入页码+3
            pages = range(page-2, page+3)
        user_list = []
        for user_obj in user_objs:
            login_last = Login.objects.filter(name=user_obj.username).last()  # 最后登录的记录
            group = AdminGroup.objects.filter(group_user=user_obj).last()  # 最后加入的组
            user_data = {
                "id": user_obj.id,
                "name": user_obj.username,
                "last_time": login_last.create_time if login_last else '',  # 最后登陆的时间
                "last_ip": login_last.ip if login_last else '',  # 最后登陆ip
                "group": group.name if group else '',  # 所属管理组（如果组存在，获取组名，不存在返回空）
                "group_id": group.id if group else '',  # 管理组id（如果组存在，获取组ID，不存在返回空）
            }
            user_list.append(user_data)
        return render(request, 'updatePass.html', {"group_data": obj_list, "user_data": user_list,"pages": pages, "userobj":user_objs})

    @group_required('管理员模块')
    def post(self, request, page):  # 提交修改用户请求
        userid = request.POST.get('userid')  # 获取要修改的用户的id
        rename = request.POST.get('username')  # 新用户名
        repwd = request.POST.get('newpwd')  # 新密码
        group_id = request.POST.get('group')  # 要加入的组
        # 校验加入的组是否存在
        try:
            group_obj = AdminGroup.objects.get(id=group_id)
        except Exception as e:
            return JsonResponse({"stat": 2})  # 不存在该组
        # 判断用户名是否存在，如果存在则无法修改，不存在才可以修改
        try:
            use_obj = User.objects.get(username=rename)
        except Exception as e:
            userobj = User.objects.get(id=userid)
            userobj.username = rename
            # 修改密码 ， 如果提交的密码为空为不修改密码，否则为修改密码
            if repwd != '':
                userobj.set_password('%s' % repwd)
            try:
                AdminGroup.objects.filter(group_user=userobj).last().group_user.remove(userobj)  # 把该用户所在的组，删除该用户
            finally:
                group_obj.group_user.add(userobj)  # 该组加入该用户
                userobj.save()
            return JsonResponse({'stat': 0})

        return JsonResponse({"stat": 1})  # 该用户名已经存在，不能修改为该用户名


class UploadDataView(LoginRequiredMixin, View):
    """上传数据"""
    @group_required('上传数据包')
    def get(self, request):
        return render(request, 'uploadData.html')

    @group_required('上传数据包')
    def post(self, request):
        myFile = request.FILES.get("myfile", None)  # 获取上传的文件，如果没有文件，则默认为None
        msg = request.POST['msg']  # 上传文件备注名
        if not myFile:  # 文件不存在
            return HttpResponse("error!")
        filepath = os.path.join("/var/www/static/payout/upload", myFile.name)  # 使用文件名拼接文件路径(linux)
        destination = open(filepath, 'wb+')  # 打开特定的文件进行二进制的写操作
        for chunk in myFile.chunks():  # 分块写入文件
            destination.write(chunk)
        destination.close()             # 关闭
        number = insert_data(filepath)  # 读取文件导入数据库，返回一个成功插入数据的条数
        Upload.objects.create(dataname=msg, filename=myFile, number=number, bywho=request.user.username)
        return render(request, 'uploadData.html', {"msg": "上传成功"})


class SearchView(LoginRequiredMixin, View):
    """信息查询"""
    def get(self, request):  # 显示页
        return render(request, 'msgSearch.html')
    @group_required('信息查询')
    def post(self, request):
        code = request.POST.get('BankCode')
        msg = request.POST.get('msg')
        if code == '1101':
            recs = Record.objects.filter(name=msg)
        elif code == '1102':
            recs = Record.objects.filter(tel=msg)
        elif code == '1103':
            recs = Record.objects.filter(qq=msg)
        elif code == '1104':
            recs = Record.objects.filter(email=msg)
        else:
            recs = ''
        context = {
            "recs": recs
        }
        return render(request, 'msgSearch.html', context)


class SendView(LoginRequiredMixin, View):
    """发送视图"""
    @group_required('信息查询')
    def post(self, request):
        send_id = request.POST['id']  # 要发送的id
        send_rec = Record.objects.get(id=int(send_id))
        time_now = datetime.datetime.now()
        send_rec.state = True  # 修改发送状态
        send_rec.send_time = time_now
        send_rec.operator = request.user.username  # 修改发送人
        send_rec.save()
        data = {
            "sendTime": time_now.strftime("%Y年%m月%d日 %H:%M"),
            "status": 0,
            "bywho": request.user.username
        }
        return JsonResponse(data)


# by xiao LI
class AduLogView(LoginRequiredMixin, View):
    """管理员的记录"""
    @group_required('信息管理')
    def get(self, request):
        adus = User.objects.all()  # 获取所有管理员，前端渲染下拉选择框
        return render(request, 'adulog.html', {'adus': adus, 'result': 0})

    @group_required('信息管理')
    def post(self, request):  # 查询管理员记录
        startTime = request.POST['startTime']  # 开始时间
        endTime = request.POST['endTime']      # 结束时间
        BankCode = request.POST['BankCode']    # 管理员
        startTime += ' 00:00:00'
        endTime += ' 23:59:59'
        startTime = datetime.datetime.strptime(startTime, '%Y-%m-%d %H:%M:%S')
        endTime = datetime.datetime.strptime(endTime, '%Y-%m-%d %H:%M:%S')
        if BankCode != '0':  # 如果选择了某个管理员
            records = Record.objects.filter(send_time__range=(startTime, endTime), operator=BankCode).order_by('-send_time')
        else:
            records = Record.objects.filter(send_time__range=(startTime, endTime)).order_by('-send_time')
        adus = User.objects.all()
        if not records.exists():
            context = {
                'adus': adus,
                'result': 1
            }
            return render(request, 'adulog.html', context)
        paginator = Paginator(records, 9)
        page = 1
        if page > paginator.num_pages:
            page = 1
        login_records = paginator.page(page)
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)
        context = {
            'adus': adus,
            'result': 1,
            'records': login_records,
            'pages': pages,
            'startTime': startTime,
            'endTime': endTime,
            'BankCode': BankCode,
            'count': len(records)
        }
        return render(request, 'adulog.html', context)


class AduLogpageView(LoginRequiredMixin, View):
    # 管理员登陆的记录的分页视图
    @group_required('信息管理')
    def get(self, request):
        startTime = request.GET['startTime']
        endTime = request.GET['endTime']
        endTime += '23:59:59'
        BankCode = request.GET['BankCode']
        page = request.GET['page']
        if BankCode != '0':
            records = Record.objects.filter(send_time__gte=startTime).filter(send_time__lte=endTime).filter(
                operator=BankCode)
        else:
            records = Record.objects.filter(send_time__gte=startTime).filter(send_time__lte=endTime)
        adus = User.objects.all()
        paginator = Paginator(records, 9)
        page = int(page)
        if page > paginator.num_pages:
            page = 1
        login_records = paginator.page(page)
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)
        context = {
            'adus': adus,
            'result': '有结果',
            'records': login_records,
            'pages': pages,
            'startTime': startTime,
            'endTime': endTime,
            'BankCode': BankCode,
            'count': len(records)
        }
        return render(request, 'adulog.html', context)


class BatchDeleteView(LoginRequiredMixin, View):
    """删除数据"""
    @group_required('信息管理')
    def get(self, request):
        return render(request, 'batchDelete.html')

    @group_required('信息管理')
    def post(self, request):
        startTime = request.POST['startTime']
        endTime = request.POST['endTime']
        endTime += ' 23:59:59'
        print(startTime, endTime)
        try:
            recodes = Record.objects.filter(create_time__gte=startTime).filter(create_time__lte=endTime)
        except Exception as e:
            index = "ERR"
        else:
            if recodes:
                recodes.delete()
                index = "OK"
            else:
                index = "NO"
        return render(request, 'batchDelete.html', {"index": index})


class DownloadInfoView(LoginRequiredMixin, View):
    """将数据下载下来"""
    @group_required('信息管理')
    def get(self, request):
        return render(request, 'downloadInfo.html')

    @group_required('信息管理')
    def post(self, request):
        startTime = request.POST['startTime']
        endTime = request.POST['endTime']
        endTimes = endTime
        endTime += ' 23:59:59'
        try:
            state = request.POST['state']
            if state == 'on':
                state = 1
            else:
                state = 0
        except Exception as e:
            state = 0
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="%s__%s__%s.csv"' % (request.user.username, startTime, endTimes)
        writer = csv.writer(response)
        records = Record.objects.filter(create_time__gte=startTime).filter(create_time__lte=endTime).filter(state=state)
        if records:
            writer.writerow(['id', 'name', 'money', 'qq', 'tel', 'email', 'state', 'create_time', 'send_time', 'operator'])
            for record in records:
                writer.writerow([record.id, record.name, record.money, record.qq, record.tel, record.email, record.state,
                                 record.create_time.strftime('%Y-%m-%d %H:%M:%S'), record.send_time.strftime('%Y-%m-%d %H:%M:%S') if record.send_time else None, record.operator])
            return response
        else:
            index = 'NO'
            return render(request, 'downloadInfo.html', {'index': index})


class UploadRecord(LoginRequiredMixin, View):
    """上传数据的记录"""
    @group_required(['信息管理', '上传数据包'])
    def get(self, request):
        uploads = Upload.objects.all()
        paginator = Paginator(uploads, 9)
        try:
            page = request.GET['page']
        except Exception as e:
            page = '1'
        page = int(page)
        if page > paginator.num_pages:
            page = 1
        login_uploads = paginator.page(page)
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)
        context = {
            'result': '有结果',
            'records': login_uploads,
            'pages': pages,
            'count': len(uploads)
        }
        return render(request, 'uploadRecord.html', context)

    @group_required(['信息管理', '上传数据包'])
    def post(self, request):  # 搜索上传记录
        searchinfo = request.POST['searchinfo']   # 搜索关键词
        uploads = Upload.objects.filter(Q(dataname=searchinfo) | Q(filename=searchinfo) | Q(bywho=searchinfo))  #搜索上传人或文件=搜索关键词
        if not uploads:
            index = 'NO'
        else:
            index = 'YES'
        paging = 'NO'
        context = {
            'index': index,
            'paging': paging,
            'records': uploads
        }
        return render(request, 'uploadRecord.html', context)


# by xiao Tang
class DeleteView(LoginRequiredMixin, View):
    """删除用户"""
    @group_required('管理员模块')
    def post(self, request):
        username = request.POST.get('username')  # 获取用户名
        try:
            user = User.objects.get(username=username)
        except Exception as e:
            return JsonResponse({"stat": 1})  # 用户不存在
        user.delete()  # 删除用户
        return JsonResponse({"stat": 0})


class AduManageView(LoginRequiredMixin, View):
    """添加管理员"""
    @group_required('管理员模块')
    def get(self, request, page):
        groups = AdminGroup.objects.all()  # 获取所有的组，前端展示
        obj_list = []
        for obj in groups:
            group_data = {
                'name': obj.name,
                'id': obj.id
            }
            obj_list.append(group_data)

        # 获取所有用户，倒序，前端展示
        users = User.objects.all().order_by('id')
        paginator = Paginator(users, 8)  # 分页，每页8条数据
        page = int(page)  # 前端传入页面，转换为int类型
        if page > paginator.num_pages:  # 传入页码page大于分页后的总页码，重置page为1
            page = 1
        # 获取第page页内容, 返回Page类的实例对象
        user_objs = paginator.page(page)
        num_pages = paginator.num_pages  # 总页码
        if num_pages < 5:  # 如果总页码<5
            # 1-num_pages
            pages = range(1, num_pages+1)  # 前端显示页码为 1 到 总页码+1
        elif page <= 3:  # 总页码不少于5，并且前端输入页码<=3时， 前端显示页码应为 1-5页
            pages = range(1, 6)
        elif num_pages - page <=2:  # 总页码-前端传入的页码 <=2时， 前端应显示 总页码-4 到总页码
            # num_pages-4, num_pages
            pages = range(num_pages-4, num_pages+1)
        else:
            # 除以上情况，前端都应该显示 前端传入页码-2 至 前端传入页码+3
            pages = range(page-2, page+3)
        user_list = []
        for obj in user_objs:
            login_last = Login.objects.filter(name=obj.username).last()  # 最后登陆的时间
            group = AdminGroup.objects.filter(group_user=obj).last()  # 所属组
            user_data = {
                "id": obj.id,
                "name": obj.username,
                "last_time": login_last.create_time if login_last else '',  # 最后登陆的时间
                "last_ip": login_last.ip if login_last else '',  # 最后登陆ip
                "group": group.name if group else '',  # 所属管理组
                "group_id": group.id if group else '',  # 管理组id
            }
            user_list.append(user_data)

        return render(request, 'aduManage.html', {"group_data": obj_list, "user_data": user_list,"pages":pages,"userobj":user_objs})

    @group_required('管理员模块')
    def post(self, request, page):
        rename = request.POST.get('username')  # 添加管理员名
        repwd = request.POST.get('newpwd')  # 添加管理员密码
        group_id = request.POST.get('group')  # 加入的组
        if not all([rename,repwd,group_id]):  # 信息不完整
            return JsonResponse({"stat":10})
        # 判断用户名是否存在
        try:
            use_obj = User.objects.get(username=rename)
        except Exception as e:
            # 用户不存在
            try:
                group_obj = AdminGroup.objects.get(id=group_id)
            except Exception as e:
                return JsonResponse({"stat": 4})
            # 创建用户加入职员 和 加入组
            user = User.objects.create_user(
                username=rename,
                password=repwd,
                is_staff=True,
            )
            group_obj.group_user.add(user)
            return JsonResponse({"stat":0})
        return JsonResponse({"stat": 5})


class AdgManageView(LoginRequiredMixin, View):
    """显示组"""
    @group_required('管理员模块')
    def get(self, request, page):
        groups = AdminGroup.objects.all().order_by('id')  # 获取所有组
        paginator = Paginator(groups, 9)  # 分页，每页9条数据
        page = int(page)   # 前端传入页面，转换为int类型
        if page > paginator.num_pages:  # 传入页码page大于分页后的总页码，重置page为1
            page = 1
        # 获取第page页内容, 返回Page类的实例对象
        groups_page = paginator.page(page)
        num_pages = paginator.num_pages  # 总页码
        if num_pages < 5:  # 如果总页码<5
            # 1-num_pages
            pages = range(1, num_pages+1)  # 前端显示页码为 1 到 总页码+1
        elif page <= 3:  # 总页码不少于5，并且前端输入页码<=3时， 前端显示页码应为 1-5页
            pages = range(1, 6)
        elif num_pages - page <=2:  # 总页码-前端传入的页码 <=2时， 前端应显示 总页码-4 到总页码
            # num_pages-4, num_pages
            pages = range(num_pages-4, num_pages+1)
        else:
            # 除以上情况，前端都应该显示 前端传入页码-2 至 前端传入页码+3
            pages = range(page-2, page+3)
        group_list = []
        for group in groups_page:  # 遍历该页的所有组
            pmsions = [i.name for i in group.permission.all()]
            data = {
                "id": group.id,
                "name": group.name,
                "count": group.group_user.count(),
                "pmsion": pmsions
            }
            group_list.append(data)
        return render(request, 'adgManage.html', {"data": group_list, "groupobj": groups_page, "pages": pages})


class AddGroupView(LoginRequiredMixin,View):
    """添加组"""
    @group_required('管理员模块')
    def post(self, request):
        groupname = request.POST.get('groupname')  # 获取组名
        checkbox_list = request.POST.get('checkdata')  # 获取权限列表
        checkbox_data = json.loads(checkbox_list)  # 把json字符串转为python对象
        pmsion_set = []  # 权限对象列表
        for i in checkbox_data:
            try:
                pmsobj = AdminPermission.objects.get(name=i)
            except Exception as e:
                return JsonResponse({"stat": 2})
            pmsion_set.append(pmsobj)
        # 判断该组是否已经存在
        try:
            group_obj = AdminGroup.objects.get(name=groupname)
        except Exception as e:
            # 不存在则创建组
            group = AdminGroup.objects.create(name=groupname)
            group.permission.set(pmsion_set)
            return JsonResponse({"stat": 0})
        # 存在则修改组里的权限
        group_obj.permission.set(pmsion_set)
        return JsonResponse({'stat': 1})


class DelGroupView(LoginRequiredMixin,View):
    """删除组"""
    @group_required('管理员模块')
    def post(self, request):
        groupname= request.POST.get('groupname')  # 获取组名
        try:
            group_obj = AdminGroup.objects.get(name=groupname)
        except Exception as e:
            # 组不存在
            return JsonResponse({"stat": 1})
        group_obj.delete()
        return JsonResponse({"stat": 0})


class SearchAdminView(LoginRequiredMixin, View):
    """管理员搜索"""
    @group_required('管理员模块')
    def post(self, request):
        search_word = request.POST.get('search_val')  # 搜索词
        try:
            user = User.objects.get(username=search_word)
        except Exception as e:
            # 用户不存在
            return JsonResponse({"stat": 1})
        group = AdminGroup.objects.filter(group_user=user).first()  # 该用户所在的组
        login_rec = Login.objects.filter(name=user.username).order_by('-id').first()  # 用户登录记录
        data = {
            "stat": 0,
            "id": user.id,
            "name": user.username,
            "group": group.name if group else '',
            "last_ip": login_rec.ip if login_rec else '',
            "last_time": (login_rec.create_time+datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S") if login_rec else '',
            'group_id': group.id if group else '',
        }
        return JsonResponse(data)


class SearchGroupView(LoginRequiredMixin, View):
    """组搜索"""
    @group_required('管理员模块')
    def post(self, request):
        group_name = request.POST.get('search_val')  # 搜索词
        try:
            group_obj = AdminGroup.objects.get(name=group_name)
        except Exception as e:
            # 组不存在
            return JsonResponse({"stat": 1})
        data = {
            "stat": 0,
            "id": group_obj.id,
            "name": group_obj.name,
            "count": group_obj.group_user.count(),  # 该组的用户数量
        }

        return JsonResponse(data)


class LoginRecSearchView(LoginRequiredMixin, View):
    """登陆记录搜索"""
    @group_required('管理员模块')
    def get(self, request, page):
        search_word = request.GET['search']  # 搜索词
        login_recs = Login.objects.filter(name=search_word).order_by('-create_time')  # 获取该用户记录，倒序
        if login_recs.exists():  # 如果记录存在
            paginator = Paginator(login_recs, 9)  # 分页，每页9条数据
            page = int(page)
            if page > paginator.num_pages:
                page=1
            login_rec = paginator.page(page)
            num_pages = paginator.num_pages
            if num_pages < 5:
                # 1-num_pages
                pages = range(1, num_pages+1)
            elif page <= 3:
                pages = range(1, 6)
            elif num_pages - page <=2:
                # num_pages-4, num_pages
                pages = range(num_pages-4, num_pages+1)
            else:
                # page-2, page+2
                pages = range(page-2, page+3)
            context = {
                "pages": pages,
                "login_rec": login_rec,
                "search_word": search_word,
            }
            return render(request, 'aduRecordSearch.html', context)
        else:  # 没有记录
            context = {
                "msg": "该用户不存在"
            }
            return render(request, 'aduRecordSearch.html', context)


class VerifyCodeView(View):
    """验证码"""
    def get(self, request):
        verifycode = VerifyCode(bgcolor='#3D1769', width=100, height=38)  # 颜色，宽，高
        buf = verifycode.getverifycode(request)
        return HttpResponse(buf.getvalue(), 'image/png')




