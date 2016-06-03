/**
 * Created by libx on 16/4/18.
 */
!(function($){
    function getScreenSize() {
        if (!screen) {
            return;
        }

        $('#text-screen-size').html(screen.width + '*' + screen.height);
    }

    function getWindowSize() {
        $('#text-window-size').html($(window).width() + '*' + $(window).height());
    }

    function getDocumentSize() {
        $('#text-document-size').html($(document).width() + '*' + $(document).height());
    }

    $(document).ready(function() {
        $('#text-user-agent').html(navigator.userAgent);

        $(window).resize(getScreenSize).resize(getWindowSize).resize(getDocumentSize);
    }).ready(getScreenSize).ready(getWindowSize).ready(getDocumentSize);
})(jQuery);