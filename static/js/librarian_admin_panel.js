$(function () {

    $(".loan_ready").on("click", function () {

        console.log(this.getAttribute("value"));
        $("#loan_id").val(this.getAttribute("value"));

        $("#loan_ready_form").trigger("submit", function (event) {
            event.preventDefault()
        });

        $(this.id).html('Pronto');
        $(this.id).attr('class','btn btn-info');
        $(this.id).prop('disabled', true)
    })
});
