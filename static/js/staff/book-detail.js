
$(function () {

    // can't add event listener using element id. Must use css class
    $(".delete_copy_btn").on("click", function () {

        $("#delete_copy_modal_id").html(this.getAttribute("value"));
        $("#confirm_delete").val(this.getAttribute("value"));
        $("#delete_copy_modal").modal("show")

    });


     $(".switch_use_destination_btn").on("click", function () {

         $("#confirm_switch").val(this.getAttribute("value"));
         $("#switch_use_destination_modal_id").html(this.getAttribute("value"));
         $("#switch_use_destination_modal").modal("show")
    });


    $("#confirm_delete").on("click", function(){

        $("#action").val("delete");
        $("#copy_id").val(this.getAttribute("value"));

        $("#post_action_form").trigger("submit", function (event) {
            event.preventDefault();
            $("#delete_copy_modal").modal("hide")
        })
    });

    $("#confirm_switch").on("click", function(){

        $("#action").val("switch_use_destination");
        $("#copy_id").val(this.getAttribute("value"));

        $("#post_action_form").trigger("submit", function (event) {
            event.preventDefault();
            $("#switch_use_destination_modal").modal("hide")
        })
    })
});
