!function ($) {

    //取消自动提交
    $('form').submit(function (e) {
        e.preventDefault();
    });


    $('button#scene_add').click(function () {
        var $id = '自动生成';
        $('#scene_id_edit').val($id);
        $('#scene_name_edit').val('');

    });


    $('button#scene_edit').click(function () {


        var $id = $(this).attr('data-id');
        var $name = $(this).attr('data-name');

        $('#scene_id_edit').val($id);
        $('#scene_name_edit').val($name);

    });


    $('button#scene_edit_sub').click(function () {

        var $id = $('#scene_id_edit').val();
        var $name = $('#scene_name_edit').val();
        $id = $.trim($id);
        $name = $.trim($name);
        if ($name == '') {
            alert('场景名称不能为空');
            return;
        }

        if ($id == '自动生成') {
            $id = '';
        }
        $.post('/management/scene_edit_add', {scene_id: $id, scene_name: $name},
            function (data) {
                if (data['code'] != 0) {
                    if (data['code'] == 3) {
                        alert('该应用已经存在');
                    }
                    else
                        alert('操作失败：' + data['msg']);
                }
                else {
                    alert('操作成功');
                    location.href = "/management/scene_index";
                }
            }, 'json').error(function () {
            alert('网络原因，无法提交');
        })

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
