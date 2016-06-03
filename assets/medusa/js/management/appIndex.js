!function ($) {
    // 添加APP
    $('.form-add').submit(function (e) {
        e.preventDefault();
        var app_name = $.trim($('#add-app-name').val());
        var app_display_name = $.trim($('#add-app-display-name').val());
        if (!app_name) {
            alert("英文名称不能为空");
            return;
        }
        if (!app_display_name) {
            alert("中文名称不能为空");
            return;
        }
        $.post('/management/add_app', {'app_name': app_name, 'app_display_name': app_display_name}, function (data) {
            if (data['code'] != 0) {
                if (data['code'] == 4) {
                    alert('操作失败: 英文名称已存在');
                    return;
                }
                alert("操作失败：" + data['msg']);
            } else {
                alert("操作成功");
                location.reload();
            }
        }, 'json').error(function () {
                alert("操作失败，服务器错误");
            }
        )
    });

    // 编辑模态框监听事件
    $('#edit-modal')
        .on('shown.bs.modal', function (e) {
            var app_id = $(e.relatedTarget).attr('data-id');
            $('#edit-app-id').val(app_id);
            $('#edit-app-name').val($('#app-' + app_id + '-name').html());
            $('#edit-app-display-name').val($('#app-' + app_id + '-display-name').html());
        })
        .on('hidden.bs.modal', function () {
            $('#edit-app-id').val('');
            $('#edit-app-name').val('');
            $('#edit-app-display-name').val('');
        });

    // 编辑APP
    $('.form-edit').submit(function (e) {
        e.preventDefault();
        var app_id = $('#edit-app-id').val();
        var app_name = $.trim($('#edit-app-name').val());
        var app_display_name = $.trim($('#edit-app-display-name').val());
        if (!app_name) {
            alert("英文名称不能为空");
            return;
        }
        if (!app_display_name) {
            alert("中文名称不能为空");
            return;
        }
        $.post('/management/edit_app', {
            'app_id': app_id,
            'app_name': app_name,
            'app_display_name': app_display_name
        }, function (data) {
            if (data['code'] != 0) {
                if (data['code'] == 5) {
                    alert('操作失败: 英文名称已存在');
                    return;
                }
                alert('操作失败：' + data['msg'])
            } else {
                alert('操作成功');
                location.reload();
            }
        }, 'json').error(function () {
                alert('操作失败，服务器错误');
            }
        )
    });

    // 删除APP
    $('.btn-delete').click(function () {
        if (confirm("确定要删除应用？") == false) {
            return;
        }

        var app_id = $(this).attr('data-id');

        $.post('/management/delete_app', {'app_id': app_id}, function (data) {
            if (data['code'] != 0) {
                alert('操作失败：' + data['msg'])
            } else {
                alert('操作成功');
                location.reload();
            }
        }, 'json').error(function () {
                alert('操作失败，服务器错误');
            }
        )
    });

    //分页
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
    $(".form-page-size").submit(function (e) {
        e.preventDefault();
        var pageSize = $.trim($('.input-page-size').val());
        window.location.href = $.query.set('page_no', 1).set('page_size', pageSize);
    });

}(jQuery);
