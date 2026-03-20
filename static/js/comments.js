$(document).ready(function() {
    let comments = $("#comments");
    if(comments){
        $(window).on('hashchange', function() {
            $(".highlighted_comment").removeClass("highlighted_comment");

            if (window.location.hash) {
                let selected = $(window.location.hash);
                if (selected) {
                    selected.addClass("highlighted_comment");
                }
            }
        });
        $(window).trigger("hashchange");
    }
});