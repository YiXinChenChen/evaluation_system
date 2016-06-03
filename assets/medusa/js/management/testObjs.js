!function ($) {
    //搜索
    $('.form-filter').submit(function (e) {
        e.preventDefault();
        var tag = $.trim($('#tag').val());
        window.location.href = $.query.set('tag', tag);
    });

    //禁用
    $('.btn-disable').on('click', function () {
        if (confirm("确定禁用？") == false) {
            return
        }
        var testobj_id = $(this).attr('obj_id');
        $.post('disable_test_obj', {
            testobj_id: testobj_id
        }, function (data) {
            if (data.code == 0) {
                window.location.href = 'test_obj_index';
            } else {
                alert('禁用失败：' + data.msg);
            }
        }, 'json').error(function () {
            alert('网络原因，无法禁用');
        })
    });


    //加载上传控件
    $('#AddModal').on('shown.bs.modal', function () {

        $.get('/management/testObj_get_info', {test_obj_info: 'info'},
            function (data) {
                $('#app_sel_sub').children().remove();
                $('#scene_sel_sub').children().remove();
                if (data['code'] != 0) {
                    alert('操作失败：' + data['msg']);
                }
                else {
                    var apps = data['appsMap'];
                    var scenes = data['scenesMap']
                    for (var o in apps) {
                        $('#app_sel_sub').append("<option value='" + o + "'>" + apps[o] + "</option>");
                    }

                    for (var o in scenes) {
                        $('#scene_sel_sub').append("<option value='" + o + "'>" + scenes[o] + "</option>");
                    }

                }
            }, 'json').error(function () {
            alert('网络原因，无法获取信息');
        })

        UploadMult();

    });

    $('#EditModal').on('shown.bs.modal', function () {

        $.get('/management/testObj_get_info', {test_obj_info: 'info'},
            function (data) {
                $('#app_sel_edit').children().remove();
                $('#scene_sel_edit').children().remove();
                if (data['code'] != 0) {
                    alert('操作失败：' + data['msg']);
                }
                else {
                    var apps = data['appsMap'];
                    var scenes = data['scenesMap'];
                    for (var o in apps) {
                        $('#app_sel_edit').append("<option value='" + o + "'>" + apps[o] + "</option>");
                    }
                    for (var o in scenes) {
                        $('#scene_sel_edit').append("<option value='" + o + "'>" + scenes[o] + "</option>");
                    }
                }
            }, 'json').error(function () {
            alert('网络原因，无法获取信息');
        })


    });

    //清除组件
    $('.fade').on('hide.bs.modal', function () {

        location.href = "/management/test_obj_index";

    });


    //关闭时刷新界面
    $('.testObj_sub_close').click(function () {

        location.href = "/management/test_obj_index";
    });


    $('.test_obj_edit').click(function () {

        var id = $(this).attr('obj_id');
        $('#id_hider').val(id);

        var tag = $(this).attr('data-tag');
        $('#test_obj_tag_edit').val(tag);
    });

    $('#test_obj_sub').click(function () {

        var id = $('#id_hider').val();
        console.log(id);
        var app_id = $('#app_sel_edit').val();
        var scene_id = $('#scene_sel_edit').val();
        var tag = $('#test_obj_tag_edit').val();


        $.post('/management/test_obj_edit', {id: id, app_id: app_id, scene_id: scene_id, tag: tag},
            function (data) {
                if (data['code'] != 0) {
                    alert('操作失败：' + data['msg']);
                }
                else {
                    alert('操作成功');
                    location.href = "/management/test_obj_index";
                }
            }, 'json').error(function () {
            alert('网络原因，无法获取信息');
        })

    });


    //s悬停显示
    $('.show-img').popover({
        html: true,
        title: '缩略图',
        trigger: 'hover',
        container: false,
        placement: 'top',
        content: function () {
            var $this = $(this);
            var obj_id = $this.attr('data-id');
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
    /*
    TODO 这段东西是用来干嘛的? popover已经实现这个功能
    .on("mouseenter", function () {
        var _this = this;

        var pos = $(this).text().lastIndexOf(".");//查找最后一个\的位置
        var path = $(this).text();
        var final = path.substr(pos + 1); //截取最后一个\位置到字符长度，也就是截取文件名

        // console.log(final);
        final = final.toLowerCase();
        if (final == 'png' || final == 'jpg' || final == 'jpeg' || final == 'bmp') {
            $(this).popover("show");
            $(this).siblings(".popover").on("mouseleave", function () {
                $(_this).popover('hide');
            });
        }
        else {
            $(_this).popover('hide');
        }
    }).on("mouseleave", function () {
        var _this = this;
        setTimeout(function () {
            if (!$(".popover:hover").length) {
                $(_this).popover("hide")
            }
        }, 100);
    });*/

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

    //取消自动提交
    $('form').submit(function (e) {
        e.preventDefault();
    });


}(jQuery);