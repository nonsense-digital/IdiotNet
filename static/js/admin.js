// form validation logic for the administration panels
$(document).ready(function() {
    // code that runs for the punishment form
    // for users: /admin/users/{username}/punish
    // for clients (IPs): /admin/clients/{ip}/punish
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

    // code that runs for the configuration form on /admin/config
    if($("#config_form")){
        // for config fields which have an enable/disable with a corresponding text input
        // if the checkbox isn't checked, disable to corresponding text input
        // if the checkbox is checked, enable the corresponding text input
        $(".optional_config").each(function(index, element){
            let name = $(element).attr("id");
            let require_input = $("#require_" + name);
            let input = $("#" + name);
            require_input.on( "change", function() {
                if(require_input.is(':checked')){
                    input.prop("disabled", "");
                }else{
                    input.prop("disabled", "disabled");
                }
            });
            require_input.trigger("change");
        });

        // similar functionality for require email and require email verification
        // they need a separate function because of naming conventions and the fact that they are both checkboxes
        let req_email_input = $("#require_email");
        let req_email_ver_input = $("#require_email_verification");
        req_email_input.on("change", function() {
            if(req_email_input.is(':checked')){
                req_email_ver_input.prop("disabled", "");
            }else{
                req_email_ver_input.prop("disabled", "disabled");
            }
        });
        req_email_input.trigger("change");
    }

    // code that runs on the approval form at /admin/posts/{id}/approval
    if($("#approve_form")){
        let verdict_input = $("#verdict");
        let submit_btn = $("#submit");

        // don't let the user submit until they have chosen one or the other
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