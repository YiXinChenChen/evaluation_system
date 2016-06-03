!function($){
    var clip = null
    function init() {
			clip = new ZeroClipboard.Client();
			clip.setHandCursor( true );
			clip.glue( 'copy' );
            clip.addEventListener('mouseOver', my_mouse_over);
            clip.addEventListener('complete', my_complete);
		}

    function my_mouse_over(client) {

			clip.setText( $('#recom_url').val());

		}
    function my_complete(client) {
			alert("复制成功")
		}

    $(document).ready(function(){
         init()
    });

}(jQuery);