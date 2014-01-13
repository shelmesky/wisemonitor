/* Chinese initialisation for the jQuery UI date picker plugin. */
/* Written by Cloudream (cloudream@gmail.com). */
jQuery(function ($) {
    $.datepicker.regional['zh-CN'] = {
        closeText: '¹Ø±Õ',
        prevText: '&#x3c;ÉÏÔÂ',
        nextText: 'ÏÂÔÂ&#x3e;',
        currentText: '½ñÌì',
        monthNames: ['Ò»ÔÂ', '¶þÔÂ', 'ÈýÔÂ', 'ËÄÔÂ', 'ÎåÔÂ', 'ÁùÔÂ',
                'ÆßÔÂ', '°ËÔÂ', '¾ÅÔÂ', 'Ê®ÔÂ', 'Ê®Ò»ÔÂ', 'Ê®¶þÔÂ'],
        monthNamesShort: ['Ò»', '¶þ', 'Èý', 'ËÄ', 'Îå', 'Áù',
                'Æß', '°Ë', '¾Å', 'Ê®', 'Ê®Ò»', 'Ê®¶þ'],
        dayNames: ['ÐÇÆÚÈÕ', 'ÐÇÆÚÒ»', 'ÐÇÆÚ¶þ', 'ÐÇÆÚÈý', 'ÐÇÆÚËÄ', 'ÐÇÆÚÎå', 'ÐÇÆÚÁù'],
        dayNamesShort: ['ÖÜÈÕ', 'ÖÜÒ»', 'ÖÜ¶þ', 'ÖÜÈý', 'ÖÜËÄ', 'ÖÜÎå', 'ÖÜÁù'],
        dayNamesMin: ['ÈÕ', 'Ò»', '¶þ', 'Èý', 'ËÄ', 'Îå', 'Áù'],
        weekHeader: 'ÖÜ',
        dateFormat: 'yy-mm-dd',
        firstDay: 1,
        isRTL: false,
        showMonthAfterYear: true,
        yearSuffix: 'Äê'
    };
    $.datepicker.setDefaults($.datepicker.regional['zh-CN']);
});