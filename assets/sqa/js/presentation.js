!function ($) {

    var pic = $(new Image());
    pic.on('load', function () {
        var clock = 6;

        var step_key = data.case_id + "_step";

        var case_id = parseInt($.cookie("case_id"), 10);
        var step = undefined;
        if (case_id != undefined) {
            step = parseInt($.cookie(step_key), 10);
        }

        if (data.case_id == case_id) {
            if (data.step <= step) {
                clock = 0;
            } else {
                $.cookie(step_key, data.step);
            }
        }

        var timeCount = function () {
            $("#clock-text").text(clock + '秒');
            if (clock > 0) {
                clock = clock - 1;
                t = setTimeout(timeCount, 1000);
            } else {
                $('.btn-last').removeClass('hide');
                $('.btn-next').removeClass('hide');
                $('.btn-vote').removeClass('hide');

                $.cookie('case_id', data.case_id);
                $.cookie('step', data.step);
            }
        };

        timeCount();

    });

    pic.addClass('center-block');
    pic.attr('src', data.img_src);
    $('#pic-div').append(pic);

}(jQuery);