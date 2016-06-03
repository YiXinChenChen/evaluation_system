+function ($) {
  'use strict';

  // LOADING PUBLIC CLASS DEFINITION
  // ==============================

    /* Loading Plugin */
    var Loading = function(target, options) {
        this.$target  = $(target);
        this.options = $.extend({}, Loading.DEFAULTS, options);
        this.loadingClass = this.options['class'] || 'loading';
        this.loaded = false;

        this.$element = $('<div/>').addClass(this.loadingClass).css({
                top: this.$target.offset().top,
                left: this.$target.offset().left
            });
        var outerThis = this;
        this.$target.load(function() {
            outerThis.loaded = true;
            outerThis.$target.css({opacity:1});
            //outerThis.$element.remove();
            outerThis.$element.fadeOut(500, function() { $(this).remove(); });
        });
        this.$target.css({opacity:0});
        this.$target.prop('src', this.$target.data('src'));

        setTimeout(function() {
            if (outerThis.loaded) {
                return;
            }

            var $target = outerThis.$target;
            var $element = outerThis.$element;
            var targetTop = $target.offset().top;
            var targetLeft = $target.offset().left;

            //var top = targetTop + ($target.height() - $element.height()) / 2;
            //var left = targetLeft + ($target.width() - $element.width()) / 2;
            $element.css({
                top: targetTop, //top,
                left: targetLeft, //left,
                width: $target.width(),
                height: $target.height(),
            });
            $element.appendTo($('body'));
        }, 100);
    };

    Loading.DEFAULTS = {
        class: 'loading'
    };
    Loading.VERSION = '1.0.0';

  // LOADING PLUGIN DEFINITION
  // ========================

  function Plugin(option) {
    return this.each(function () {
      var $this   = $(this);
      var data    = $this.data('medusa.loading');
      var options = typeof option == 'object' && option;

      if (!data) $this.data('medusa.loading', (data = new Loading(this, options)));
    })
  }

  var old = $.fn.loading;

  $.fn.loading             = Plugin;
  $.fn.loading.Constructor = Loading;


  // LOADING NO CONFLICT
  // ==================

  $.fn.loading.noConflict = function () {
    $.fn.button = old;
    return this;
  };


  // LOADING DATA-API
  // ===============

}(jQuery);

!function ($) {
    var clock = 5;
    var testObjNotLoaded = null;
    var testObjNotLoadedCheckTimer = 0;

    function timeCount() {
        $("#clock-text").text(clock + '秒');
        if (clock > 0) {
            clock = clock - 1;
            setTimeout(timeCount, 1000);
        } else {
            $('.btn-vote').removeClass('disabled');
            $('.btn-vote').removeProp('disabled');
        }
    }

    function checkTestObjNotLoaded() {
        if (testObjNotLoadedCheckTimer) {
            clearTimeout(testObjNotLoadedCheckTimer);
        }
        //console.log('checkTestObjNotLoaded');
        testObjNotLoadedCheckTimer = setTimeout(function() {
            //console.log('checkTestObjNotLoaded timer');
            if (testObjNotLoaded <= 0) {
                //console.log('checkTestObjNotLoaded testObjNotLoaded <= 0');
                setTimeout(timeCount, 100);
            }
        }, 100);
    }

    $(document).ready(function() {
        var $testObjs = $('.img-test-obj');
        testObjNotLoaded = $testObjs.length;

        $testObjs.each(function() {
            var $this = $(this);
            $this.load(function() {
                testObjNotLoaded--;
                checkTestObjNotLoaded();
            });
            $this.loading({'class':'loading-test-obj'});
        });

        // bootstrap buttons插件不支持disabled的判断,所以只能自己写
        //$('.btn-group-vote .btn').click(function(e) {
        //    var $this = $(this);
        //    var $input = $this.find('input');
        //    if ($this.is('.disabled') || $input.is(':disabled')) {
        //        e.preventDefault();
        //        return;
        //    }
        //
        //    var changed = true;
        //    var $parent = $this.closest('.btn-group-vote');
        //
        //    if ($input.is(':checked')) {
        //        changed = false;
        //    }
        //
        //    $parent.find('.active').removeClass('active');
        //    $this.addClass('active');
        //
        //    $input.prop('checked', $this.hasClass('active'));
        //
        //    if (changed) {
        //        $input.trigger('change');
        //    }
        //});

        //$('.btn-vote input[type="radio"]').change(function() {
        //    $('.btn-vote-submit').removeClass('disabled').prop('disabled', false);
        //});

        $('.btn-vote').click(function() {
            var $this = $(this);
            if ($this.is(':disabled')) {
                return;
            }
            $('#input-vote').val($this.data('value'));

            $('#form-vote').submit();
        });
    });
}(jQuery);