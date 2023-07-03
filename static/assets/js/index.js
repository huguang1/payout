
// 派送事件
$(document).on('click','.deliverybtn',function () {
    console.log($(this));
    var btn = $(this);
    $.ajax({
            url : '/send',
            type : 'POST',
            dataType : 'json',
            data: {id:$(this).attr("id"), csrfmiddlewaretoken:$('[name="csrfmiddlewaretoken"]').val()},
            success : function(result){
                if(result.status==0){
                    console.log($(this));
                    btn.parent().prev().html('已派送');
                    btn.parent().prev().addClass('deliveried');
                    btn.parent().next().html(result.sendTime);
                    btn.parent().html(result.bywho);
                }
            }
        });
})

// 增加管理组
$(document).on('click','.add-adgroup-btn',function () {
    $(this).hide()
    $('.addgroup').show();
})
// 增加管理组 提交
$(document).on('click','.addgroup .subBtnstl',function () {
    $('.addgroup').hide()
    $('.add-adgroup-btn').show();
    //$('#adgManage .panel-body tbody').append('<tr><td>11</td> <td>主管组</td> <td>2</td> <td><img class="edit-list" src="./assets/img/edit.jpg" alt=""><img class="delete-list" src="./assets/img/delete-icon.jpg" alt=""></td> </tr>')
})

// 时间input
$("#startTime").datetimepicker({
    minView: "month",//设置只显示到月份
    format : "yyyy-mm-dd",//日期格式
    autoclose:true,//选中关闭
    todayBtn: true//今日按钮
});
$("#endTime").datetimepicker({
    minView: "month",//设置只显示到月份
    format : "yyyy-mm-dd",//日期格式
    autoclose:true,//选中关闭
    todayBtn: true//今日按钮
});

// $(document).on('click','.first-nav>li',function () {
//     $(this).siblings().find('[data-toggle="in"]').length;
//     console.log($('.first-nav').siblings().find('div[data-toggle="collapse in"]').length)
//     console.log($(this).siblings().find('div[data-toggle="collapse in"]').length)
// })
