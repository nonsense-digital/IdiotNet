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

    if($("#config_form")){
        let require_join_code_input = $("#require_join_code");
        let join_code_input = $("#join_code");
        require_join_code_input.on( "change", function() {
            if(require_join_code_input.is(':checked')){
                join_code_input.prop("disabled", "");
            }else{
                join_code_input.prop("disabled", "disabled");
            }
        });
        require_join_code_input.trigger("change");
    }

    if($("#approve_form")){
        let verdict_input = $("#verdict");
        let submit_btn = $("#submit");
        verdict_input.on( "change", function() {
           if(verdict_input.val() === 'none' || verdict_input.val() === null){
               submit_btn.prop("disabled", "disabled");
           }else{
               submit_btn.prop("disabled", "");
           }
        });
        verdict_input.trigger("change");
    }
});