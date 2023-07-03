from PIL import Image, ImageDraw, ImageFont
from django.utils.six import BytesIO
import random
import os


class VerifyCode(object):
    """验证码封装"""

    def __init__(self, bgcolor, width, height):
        self.bgcolor = bgcolor
        self.width = width
        self.height = height

    def getverifycode(self, request):
        # 创建画面对象
        im = Image.new('RGB', (self.width, self.height), self.bgcolor)
        # 创建画笔对象
        draw = ImageDraw.Draw(im)
        # 调用画笔的point()函数绘制噪点
        for i in range(0, 100):
            xy = (random.randrange(0, self.width), random.randrange(0, self.height))
            fill = (random.randrange(0, 255), 255, random.randrange(0, 255))
            draw.point(xy, fill=fill)
        # 定义验证码的备选值
        str1 = 'ABCD123EFGHIJK456LMNOPQRS789TUVWXYZ0'
        # 随机选取4个值作为验证码
        rand_str = ''
        for i in range(0, 4):
            rand_str += str1[random.randrange(0, len(str1))]
        # 构造字体对象
        font_path = os.path.join(os.path.dirname(os.path.realpath(__file__))  , 'FreeMono.ttf')
        font = ImageFont.truetype(font_path, 33)
        # 构造字体颜色
        fontcolor = (255, random.randrange(0, 255), random.randrange(0, 255))
        # 绘制4个字
        draw.text((5, 2), rand_str[0], font=font, fill=fontcolor)
        draw.text((25, 2), rand_str[1], font=font, fill=fontcolor)
        draw.text((50, 2), rand_str[2], font=font, fill=fontcolor)
        draw.text((75, 2), rand_str[3], font=font, fill=fontcolor)
        # 释放画笔
        del draw
        # 存入session，用于做进一步验证
        request.session['verifycode'] = rand_str
        # 内存文件操作
        buf = BytesIO()
        # 将图片保存在内存中，文件类型为png
        im.save(buf, 'png')
        # 将内存中的图片数据返回给客户端，MIME类型为图片png
        return buf