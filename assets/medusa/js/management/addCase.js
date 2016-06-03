!function($){
    $('.form-filter').submit(function (e) {
        e.preventDefault();
        var appName = $.trim($('#appName').val());
        var sceneName = $.trim($('#sceneName').val());
        var tagVal = $.trim($('#tagVal').val());
        var filePath = $.trim($('#filePath').val());
        window.location.href = $.query.set('app_name', appName).set('scene_name', sceneName).set('tag_val', tagVal).set('file_path', filePath).set('page_no', 1);
    });
    
    // 禁用按钮
    if (data.disable_cud === true) {
         $('.btm-delete, .btm-add, .btm-order-sub, .input-sm').attr('disabled', 'disabled');
    } else {
         $('.btm-delete, .btm-add, .btm-order-sub, .input-sm').removeAttr('disabled');
        //, .btm-order-sub, .input-sm
    }

    //model 编辑
     $('#EditModal').on('shown.bs.modal', function (e) {
        var case_id = data.case_id;
        var testobj_id = $(e.relatedTarget).attr('data-id');


         $.post('/management/case_testObj_get_order',
             {
                 case_id: case_id,
                 testobj_id: testobj_id
             },
            function (data) {
                $('#pic_order_num').val(0);
                if (data['code'] != 0) {
                    alert('操作失败：' + data['msg']);
                }
                else {
                    var id = data['id'];
                    var order = data['order'];
                     $('#case_obj_id').val(id);
                     $('#pic_order_num').val(order);
                }
            }, 'json').error(function () {
            alert('网络原因，无法获取信息');
        })


    });

    //提交修改顺序
    $('.btm-order-sub').on('click', function(){
        var order= $(this).parent().prev().children('input').val()
        var id = $(this).attr('data-id');
        if (!$.isNumeric(order))
        {
            alert('输入必须为数字');
            return;
        }
        else
        {
            $.post('/management/case_testObj_sub_order',
                {
                    case_obj_id: id,
                    order: order,
                },
                function (data) {
                    if (data['code'] != 0) {
                        alert('操作失败：' + data['msg']);
                    }
                    else {
                        alert('修改成功');
                        window.location.reload();
                        //var appName = $.trim($('#appName').val());
                        //var sceneName = $.trim($('#sceneName').val());
                        //var tagVal = $.trim($('#tagVal').val());
                        //var filePath = $.trim($('#filePath').val());
                        //window.location.href = $.query.set('app_name', appName).set('scene_name', sceneName).set('tag_val', tagVal).set('file_path', filePath);
                    }
                }, 'json').error(function () {
                alert('网络原因，无法获取信息');
            })
        }


    });

    //添加test_obj
    $('.btm-add').on('click', function () {
        var case_id = data.case_id;
        var testobj_id = $(this).attr('data-id');
        var page_no = $.query.get('page_no');
        if (page_no === ''){
            page_no = 1
        }
        var suite_id = data.suite_id;
        $.post('add_case_testobj', {
            case_id: case_id,
            testobj_id: testobj_id,
            suite_id: suite_id
        }, function (data) {
            if (data.code == 0) {
                var appName = $.trim($('#appName').val());
                var sceneName = $.trim($('#sceneName').val());
                var tagVal = $.trim($('#tagVal').val());
                var filePath = $.trim($('#filePath').val());
                window.location.href = $.query.set('app_name', appName).set('scene_name', sceneName).set('tag_val', tagVal).set('file_path', filePath);
                // window.location.href = 'add_case_index?case_id=' + case_id + '&suite_id=' + suite_id + '&page_no=' + page_no;
            } else {
                alert('添加testobj失败： ' + data.msg);
            }
        }, 'json');
    });

    //删除test_obj
    $('.btm-delete').on('click', function () {
        var case_id = data.case_id;
        var testobj_id = $(this).attr('data-id');
        var suite_id = data.suite_id;
        var page_no = $.query.get('page_no');
        if (page_no === ''){
            page_no = 1
        }
        $.post('delete_case_testobj', {
            case_id: case_id,
            testobj_id: testobj_id
        }, function (data) {
            if (data.code == 0) {
                var appName = $.trim($('#appName').val());
                var sceneName = $.trim($('#sceneName').val());
                var tagVal = $.trim($('#tagVal').val());
                var filePath = $.trim($('#filePath').val());
                window.location.href = $.query.set('app_name', appName).set('scene_name', sceneName).set('tag_val', tagVal).set('file_path', filePath);
               // window.location.href = 'add_case_index?case_id=' + case_id + '&suite_id=' + suite_id + '&page_no=' + page_no;;
            } else {
                alert("删除case_testobj失败： " + data.msg)
            }
        }, 'json').error(function(){
            alert("无法删除case_testobj，原因：网络出错")
        })
    });

     //悬停显示
    $('.show-img').popover({
        html: true,
        title: '缩略图',
        trigger: 'hover',
        container: false,
        placement: 'top',
        content: function () {
            var $this = $(this);
            var path = '../assets/';
            var file_path =  $this.attr('data-path').replace(/\\/g, "\/");
            path = path + file_path;
            var content = $('<div/>').addClass('hover-hovercard').append(
                    $('<img/>').prop({
                        src: path,
                        height: 200
                    })
                );
            return content;
        }
    });

    $('.btm-source').on('click', function (){
        var path = '../assets/';
        var file_path =  $(this).attr('data-path').replace(/\\/g, "\/");
        path = path + file_path;
        window.open(path);
        console.log(path);
    });


    //分页插件
    $('.pagination').jqPaginator({
        totalCounts: data.paginator.totalCounts,
        visiblePages: 6,
        currentPage: data.paginator.pageNo,
        pageSize: data.paginator.pageSize,
        onPageChange: function (arg_num, arg_type) {
            //type的值有 init 和 change 两种，表示 控件初始化 和 已初始化后的状态改变
            //console.log('当前第' + arg_num + '页', arg_type);
            if (arg_type === 'change') {
                location.href = $.query.set('page_no', arg_num);
            }
        },
        //first: '<li><a href="javascript:;">首页</a></li>',
        prev: '<li><a href="javascript:;"><span aria-hidden="true">&laquo;</span></a></li>',
        next: '<li><a href="javascript:;"><span aria-hidden="true">&raquo;</span></a></li>',
        //last: '<li><a href="javascript:;">尾页</a></li>',
        page: '<li><a href="javascript:;">{{page}}</a></li>'
    });
    $(".input-page-size").val(data.paginator.pageSize);
    $(".form-page-size").submit(function(e) {
        e.preventDefault();
        var pageSize = $.trim($('.input-page-size').val());
        window.location.href = $.query.set('page_no', 1).set('page_size', pageSize);
    });
}(jQuery);