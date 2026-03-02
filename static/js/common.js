
$(document).ready(function() {
    let like_post = $('#like').data('like') === "True";
    if(like_post){
        $("#like").text("Like");
    }else{
       $("#like").text ("Unlike");
    }
    let follow_user = $("#follow").data("follow") === "True";
    if(follow_user){
        $("#follow").text("Follow");
    }else{
        $("#follow").text("Unfollow");
    }
    $('form').on('submit', function () {
        $('.submit').prop('disabled', true); // Disable the submit button
    });

  $("#like").click(function() {
      const post_id = $('#like').data('id');
      const url = '/api/posts/' + post_id + '/like';
      let like_post = $('#like').data('like') === "True";
      $("#like").prop("disabled", "true");
      $.ajax({
          url: url,
          type: "POST",
          contentType: "application/json; charset=utf-8", // Correct content type for JSON
          data: JSON.stringify({like: like_post}), // Stringify JSON data
          success: function (response) {
              like_post = !like_post;
              updateLikes(like_post);
              $("#like").prop("disabled", "");
          },
          error: function (xhr, status, error) {
              alert(error);
              $("#like").prop("disabled", "");
          }
      });
  });
    $("#follow").click(function() {
      const username = $('#follow').data('username');
      const url = '/api/users/' + username + '/follow';
      let follow_user = $("#follow").data("follow") === "True";
      $("#follow").prop("disabled", "true");
      $.ajax({
          url: url,
          type: "POST",
          contentType: "application/json; charset=utf-8", // Correct content type for JSON
          data: JSON.stringify({follow: follow_user}), // Stringify JSON data
          success: function (response) {
              follow_user = !follow_user;
              updateFollows(follow_user);
              $("#follow").prop("disabled", "");
          },
          error: function (xhr, status, error) {
              alert(error);
              $("#follow").prop("disabled", "");
          }
      });
  });
});

function updateLikes(like_post){
    $('#like').data('like', like_post ? "True" : "False");
    if(like_post){
        $("#like").text("Like");
    }else{
        $("#like").text("Unlike");
    }
    let likes = $("#like-count").text() | 0;
    likes += !like_post ? 1 : -1;
    $("#like-count").text(likes);
}

function updateFollows(follow_user){
    $('#follow').data('follow', follow_user ? "True" : "False");
    if(follow_user){
        $("#follow").text("Follow");
    }else{
        $("#follow").text("Unfollow");
    }
    let followers = $("#follower-count").text() | 0;
    followers += !follow_user ? 1 : -1;
    $("#follower-count").text(followers);
}

