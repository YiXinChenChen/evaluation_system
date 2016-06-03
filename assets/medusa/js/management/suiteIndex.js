!function ($) {
    function resetForm($form) {
        $('input', $form).each(function() {
            var $this = $(this);
            if ($this.attr('name') == 'csrfmiddlewaretoken') {
                // do not reset csrftoken
                return;
            }
            $this.val(null);
        });
    }

    //搜索
    $('.form-filter').submit(function (e) {
        e.preventDefault();
        var suiteName = $.trim($('#suiteName').val());
        window.location.href = $.query.set('suiteName', suiteName);
    });

    //添加新的测试
    $('.form-add').submit(function (e) {
        e.preventDefault();
        var suiteName = $.trim($('#add-suite-name').val());
        var suite_split_type = $.trim($('#add-suite-split-type').val());
        var suite_case_obj_count = $.trim($('#add-suite-case-obj-count').val());
        if (suiteName == ''){
            alert('任务名称不能为空');
            return
        }
        if (suite_split_type == ''){
            alert('case 划分类型不能为空');
            return
        }
        if (suite_case_obj_count == ''){
            alert('case 数目不能为空');
            return
        }
        var suite_case_obj_count_int =parseInt(suite_case_obj_count);
        if (suite_case_obj_count_int < 2 || suite_case_obj_count_int > 4){
            alert('case 数目为2-4');
            return
        }

        $.get('/management/add_suite',{
            suiteName:suiteName,
            splitType:suite_split_type,
            caseCount:suite_case_obj_count
        },function(data){
            if(data.code === 0){
                // alert('操作成功');
                location.reload();
            }else{
                alert('添加任务失败，原因：' + data.msg)
            }
        },'json')
            .error(function(){
                alert("添加任务失败，原因：网络出错")
            })
    });

    $('#edit-modal')
        .on('shown.bs.modal', function (e) {
            var suite_id = $(e.relatedTarget).attr('data-id');
            $('#edit-suite-id').val(suite_id).html();
            $('#edit-suite-name').val($('#suite-' + suite_id + '-name').html());
            $('#edit-suite-split-type').val($('#suite-' + suite_id + '-split-type').attr('data-type'));
            $('#edit-suite-case-obj-count').val($('#suite-' + suite_id + '-case-obj-count').html());
        })
        .on('hidden.bs.modal', function () {
            $('#edit-suite-name').val('');
            $('#edit-suite-split-type').val('');
            $('#edit-suite-case-obj-count').val('');
        });

    $('.form-edit').submit(function (e) {
        e.preventDefault();
        var suite_id =  $.trim($('#edit-suite-id').val());
        var suiteName = $.trim($('#edit-suite-name').val());
        var suite_split_type = $.trim($('#edit-suite-split-type').val());
        var suite_case_obj_count = $.trim($('#edit-suite-case-obj-count').val());
        if (suiteName == ''){
            alert('任务名称不能为空');
            return
        }
        if (suite_split_type == ''){
            alert('case 划分类型不能为空');
            return
        }
        if (suite_case_obj_count == ''){
            alert('case 数目不能为空');
            return
        }
        var suite_case_obj_count_int =parseInt(suite_case_obj_count);
        if (suite_case_obj_count_int < 2 || suite_case_obj_count_int > 4){
            alert('case 数目为2-4');
            return
        }


        $.post('/management/edit_suite',{
            suite_id:suite_id,
            suite_name:suiteName,
            split_type:suite_split_type,
            case_count:suite_case_obj_count
        },function(data){
            if(data.code == 0){
                // alert('操作成功');
                location.reload();
            }else{
                alert('编辑任务失败，原因：' + data.msg)
            }
        },'json').error(function(){
            alert("添加任务失败，原因：网络出错")
        })
    });

    $('.btm-start').on('click', function () {
        var $this = $(this);
        var id = $this.attr('data-id');
        // reset form
        resetForm($('#start-modal .form-start'))
        $('#start-suite-id').val(id);
        $('#start-modal').modal('show');

        //if (confirm("确定要开始任务吗？") == false) {
        //    return
        //}
        //var suite_id = $(this).attr('data-id');
        //$.post('/management/start_suite', {
        //    suite_id: suite_id
        //}, function (data) {
        //    if (data.code == 0) {
        //        //window.location.href = "/management/index?page_no=1"
        //        window.location.reload(true);
        //    } else {
        //        alert('开始任务失败，原因：' + data.msg)
        //    }
        //}, 'json').error(function () {
        //    alert("开始任务失败，原因：网络出错")
        //})
    });
    
    //结束任务
    $('.btm-finish').on('click', function(){
        if (confirm("确定要结束任务吗？") == false) {
            return
        }
       var suite_id =  $(this).attr('data-id');
        $.post('/management/finish_suite',{
            suite_id :suite_id
        },function(data){
            if(data.code == 0){
                window.location.href = "/management/index?page_no=1"
            }else{
                alert('结束任务失败，原因：' + data.msg)
            }
        },'json').error(function(){
            alert("结束任务失败，原因：网络出错")
        })
    });

    $('.btm-group').on('click', function(){
        var suite_id =  $(this).attr('data-id');
        window.location.href = "/management/suite_group_index?suite_id="+suite_id;
    });

    $('.btm-delete').on('click', function(){
        var suite_id =  $('.btm-start').attr('data-id');
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

    $('.btm-check').on('click',function(){
        var uuid = $(this).attr('data-uuid');
        $('#uuid_hide').val(uuid);

    });

    function getSuiteViewUrl(uuid) {
        var ref = $('#suite-view-ref').val();
        var host = window.location.host;
        var url = 'http://'+host +'/sqa/'+uuid+'/welcome';
        var query = ref.length == 0? '': ('ref=' + encodeURIComponent(ref));

        if (query.length != 0) {
            url += '?' + query;
        }

        return url;
    }

    function updateSuiteViewLink(uuid) {
        var url = getSuiteViewUrl(uuid);

        $('#suite-view-link').empty().append(
            $('<a/>').attr({
                'target': '_blank',
                'href': url
            }).addClass('btn btn-primary').text('查看')
        );
    }

    $('#view-modal')
        .on('show.bs.modal', function (e) {
            var uuid = $(e.relatedTarget).attr('data-uuid');
            //var host = $(e.relatedTarget).attr('data-address');
            $('#suite-view-uuid').val(uuid);

            updateSuiteViewLink(uuid);
        })
        .on('hidden.bs.modal', function () {
            $('#suite-view-uuid').val('');
            $('#suite-view-link').empty();
        });

    $('#suite-view-ref').change(function() {
        var uuid = $('#suite-view-uuid').val();
        updateSuiteViewLink(uuid);
    });

    // start modal
    $('.input-group-date').datetimepicker({});

    $('#btn-suite-start').click(function(e) {
        $('#form-suite-start').submit();
    });

    $('#form-suite-start').submit(function(e) {
        e.preventDefault();

        var $this = $(this);
        var formArray = $this.serializeArray();
        var formData = {};

        for (var i in formArray) {
            var name = formArray[i]['name'];
            var value = formArray[i]['value'];
            formData[name] = value;
        }

        var suite_id = $(this).attr('data-id');
        $.post('/management/start_suite', formData, function (data) {
            if (data.code == 0) {
                window.location.reload(true);
            } else {
                alert('开始任务失败，原因：' + data.msg)
            }
        }, 'json').error(function () {
            alert("开始任务失败，原因：网络出错")
        })
    });

}(jQuery);