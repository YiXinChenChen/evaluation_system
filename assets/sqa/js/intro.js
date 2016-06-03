!function($){
    $('.btn-start-test').on('click',function(){
        $('.btn-start-test').prop('disabled', true);

        var suiteUUID = $('#input-suite-uuid').val();
        $.get('/sqa/' + suiteUUID + '/get-execution',
            function(data){
                if (data.code == 0){
                    location.href = "presentation"
                } else {
                    var redirectUrl = data.redirect_url || false;
                    if (redirectUrl) {
                        location.href = redirectUrl;
                    } else {
                        alert("开始评测失败，原因：" + data.msg);
                        $('.btn-start-test').prop('disabled', false);
                    }
                }
            },'json').error(function(){
                alert("开始评测失败，原因：网络出错");
                $('.btn-start-test').prop('disabled', false);
            })
    })
}(jQuery);