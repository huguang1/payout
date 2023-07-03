# -*- coding: utf-8 -*-
# 18-11-5 下午7:02
# AUTHOR:June
from django.db import connection


def insert_data(file):
    with connection.cursor() as cursor:
        number = cursor.execute("load data local infile '%s' into table major_record fields terminated by ',' lines terminated by '\r\n' ignore 1 lines (name, money, qq, tel, email, state, create_time) set create_time = CURRENT_TIMESTAMP;" % file)
    return number
