var message, stopBlinking = false;
$(document).ready(function() {
    message = '{{ message }}';
    if(message) {
        $('html, body').animate({scrollTop: $('#status').offset().top}, 'slow');
    }
});

setTimeout(function() {stopBlinking = true;}, 3000);

function blink(selector) {
    $(selector).fadeOut('slow', function() {
        $(this).fadeIn('slow', function() {
            if (!stopBlinking) {
                blink(this);
            } else {
                $(this).hide();
            }
        });
    });
}
blink(".blink");