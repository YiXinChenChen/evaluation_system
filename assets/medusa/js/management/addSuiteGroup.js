!function ($) {
    // 禁用按钮
    if (data.disable_cud === true) {
        $('.btm-edit, .btm-delete, .btm-add, .btn-add-suite-group, .btn-delete-case').attr('disabled', 'disabled');
    } else {
         $('.btm-edit, .btm-delete, .btm-add, .btn-add-suite-group, .btn-delete-case').removeAttr('disabled');
    }

    //添加小组
    $('.btn-save-add').on('click', function () {
        var group_name = $.trim($('#add_group_name').val());
        if (group_name === '') {
            alert('小组名称不能为空');
            return;
        }

        var suite_id = data.suite_id;
        $.post('/management/add_suite_group', {
            suite_id: suite_id,
            group_name: group_name
        }, function (data) {
            if (data.code == 0) {
                window.location.href = "suite_group_index?suite_id="
                    + suite_id;
            } else {
                alert('添加小组失败: ' + data.msg);
            }
        }, 'json').error(function () {
            alert('无法添加小组')
        });
    });

    //搜索小组
    $('.btn-search').on('click', function (e) {
        e.preventDefault();
        var suite_id = data.suite_id;
        var group_name = $.trim($('#groupName').val());

        window.location.href = 'suite_group_index?suite_id=' + suite_id + '&group_name=' + group_name
    });

    //编辑小组
    $('.btn-save-edit').on('click', function () {
        var group_name = $.trim($('#edit_group_name').val());
        var group_id = $.trim($('#edit_group_id').val());
        var suite_id = data.suite_id;
        
        if (group_name == '') {
            alert('小组名称不能为空');
            return;
        }

        if (group_id) {
            $.post('/management/edit_group', {
                group_id: group_id,
                group_name: group_name,
                suite_id: suite_id
            }, function (data) {
                if (data.code == 0) {
                    window.location.href = "suite_group_index?suite_id="
                        + $('.btn-add-suite-group').attr('data-id');
                } else {
                    alert('修改小组名称失败: ' + data.msg);
                }
            }, 'json').error(function () {
                alert('无法修改小组名称')
            });
        }
    });

    $('#editGroupModal').on('shown.bs.modal', function (e) {
        var group_id = $(e.relatedTarget).attr('data-id');
        $('#edit_group_id').val(group_id).html();
        $('#edit_group_name').val($('#group_' + group_id + '_groupName').html());
    }).on('hidden.bs.modal', function () {
        $('#edit_group_id').val('').html();
        $('#edit_group_name').val('').html()
    });

    //删除小组
    $('.btm-delete').on('click', function () {
        if (confirm("确定要删除任务吗？") == false) {
            return
        }

        var group_id = $(this).attr('data-id');

        var  suite_id = data.suite_id;
        if (group_id) {
            $.post('/management/delete_group', {
                group_id: group_id,
                suite_id: suite_id
            }, function (data) {
                if (data.code == 0) {
                    window.location.href = "suite_group_index?suite_id=" + $('.btn-add-suite-group').attr('data-id');
                } else {
                    alert('删除小组失败: ' + data.msg);
                }
            }, 'json').error(function () {
                alert('无法删除小组')
            });
        }
    });


    //添加Case
    $('.btm-add').on('click', function() {
        if (confirm("确定要添加Case吗？") == false) {
            return
        }
        var group_id = $(this).attr('data-id');
        var suite_id = data.suite_id;
        $.post('add_case', {
            group_id: group_id,
            suite_id: suite_id
        }, function (data) {
            if (data.code == 0) {
                window.location.href = 'add_case_index?case_id=' + data.case_id + '&suite_id=' + suite_id;
            } else {
                alert('添加Case失败: ' + data.msg);
            }
        }, 'json');
        // window.location.href = 'add_case_index?suite_id=' + data.suite_id + '&group_id=' + group_id
    });

    ////查看Case
    //$('.btn-review').on('click', function () {
    //
    //    var case_id = $(this).attr('data-id');
    //    $.post('/management/case_view',
    //      {
    //        case_id: case_id,
    //      },
    //        function (data) {
    //        if (data.code == 0) {
    //
    //        } else {
    //            alert('删除case失败: ' + data.msg);
    //        }
    //    }, 'json').error(function () {
    //        alert('无法删除case')
    //    });
    //});

    //编辑Case
    $('.btn-edit-case').on('click', function () {
        var case_id = $(this).attr('data-id');
        var suite_id = data.suite_id;

        window.open('add_case_index?case_id=' + case_id + '&suite_id=' + suite_id + '&is_edit=true');
        //window.location.href = 'add_case_index?case_id=' + case_id + '&suite_id=' + suite_id + '&is_edit=true';
    });

    //删除Case
    $('.btn-delete-case').on('click', function () {
        if (confirm("确定删除此Case吗？") == false) {
            return
        }
        var case_id = $(this).attr('data-id');
        var suite_id = data.suite_id;

        $.post('delete_case', {
            case_id: case_id,
            suite_id: suite_id
        }, function (data) {
            if (data.code == 0) {
                window.location.href = "suite_group_index?suite_id="+ suite_id;
            } else {
                alert('删除case失败: ' + data.msg);
            }
        }, 'json').error(function () {
            alert('无法删除case')
        });
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