$(document).ready(function() {
    // punishment form
    if($("#punishment_form")){
        let punishment_input = $("#punishment");
        let expiration_input = $("#expiration");
        let reason_input = $("#reason");

        // thanks to https://api.jquery.com/change/
        // disable input fields that aren't needed
        punishment_input.on( "change", function() {
            let punishment_type = punishment_input.val();

            // there doesn't need to be a reason or expiration for a pardon
            if(punishment_type === "none"){
                reason_input.prop("disabled", "disabled");
                expiration_input.prop("disabled", "disabled");
            }else if(punishment_type === "permaban"){
                reason_input.prop("disabled", "");
                expiration_input.prop("disabled", "disabled");
            }else{
                reason_input.prop("disabled", "");
                expiration_input.prop("disabled", "");
            }
        } );
        punishment_input.trigger("change");

    }
});