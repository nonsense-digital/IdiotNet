// validation and loading for image uploads
// thanks to https://api.jquery.com/jQuery.post/
// and also https://stackoverflow.com/questions/23911775/how-to-add-data-to-a-form-when-submitting-via-a-post-ajax-request
const IMAGE_LIMIT = 20;
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
const MAX_FILESIZE = 5000000;

let current_images = [];

$(document).ready(function() {
    let form = $("#post_form");
    if(form){
        let upload_input = $("#images_input");
        let upload_button = $("#add_images");
        let uploads_section = $("#post-images");
        let image_ids = $("#image_ids");
        let submit_button = $("#post_publish");
        let upload_message = $('#upload_message');

        // secret button hack for better styling
        upload_button.on("click", function(event){
            event.preventDefault();
            upload_input.click();
        });

        // upload input functionality
        upload_input.on("change", function(){
            let files = upload_input.prop('files');
            if(current_images.length + files.length <= IMAGE_LIMIT){
                submit_button.prop("disabled", true); // disable the submit button during upload
                upload_message.text('Uploading images...'); // add loading text
                for(let i = 0; i < files.length; i++){
                    // check for problems with the file
                    let error = null;

                    if(!ALLOWED_TYPES.includes(files[i].type)){ // is the filetype supported?
                        error = "its format not supported"
                    }

                    if(files[i].size > MAX_FILESIZE){ // is the file small enough?
                        error = "it is larger than 5MB"
                    }

                    if(error != null){ // error message
                        let error_msg = `Image file ${files[i].name} cannot be uploaded because ${error}.`;
                        console.Error(error_msg);
                        alert(error_msg)
                    }else{ // continue with uploading
                        console.log(`Uploading file ${files[i].name}`);

                        upload(uploads_section, submit_button, upload_message, files[i]);
                    }
                }
            }else{
                alert("Maximum image uploads is 20");
            }
            upload_input.val('');
        });

        // form submit functionality
        form.on('submit', function(event){
           image_ids.val(JSON.stringify(current_images)); // add image ids to form data
        });
    }
});

// display the image on the preview
function addToPreview(uploads_section, file){
    let reader = new FileReader();
    reader.onload = function(event){
        let image = $('<img>', {
            src: event.target.result
        });
        uploads_section.append(image);
    }
    reader.readAsDataURL(file);
}

// upload the file to the server and then add to the list
function upload(uploads_section, submit_button, upload_message, file){
    let formData = new FormData();
    formData.append('file', file);
    $.post({
        url: "/api/images/upload",
        type: "POST",
        data: formData,
        processData: false,
        contentType: false,
        success: function(data){
            current_images.push(data.id); // add to images list
            addToPreview(uploads_section, file); // add image to preview section
            console.log(`Uploaded file ${file.name} as image #${data.id}`);
            upload_message.text(''); // remove loading text
            submit_button.prop('disabled', false); // enable it once the upload is complete
        },
        error: function(jqXHR, textStatus, errorThrown){
            let error_msg = `File ${file.name} could not be uploaded due to a mute/ban or network issues.`;
            console.error(error_msg);
            alert(error_msg);
        }
    });
}