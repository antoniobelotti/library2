/* document ready */
$(function () {


    $.ajax({
        url: window.location.href + '/days_this_book_is_not_available_for_cons',
        dataType: 'json',

        success: function(data) {
            setDatePicker(data)
        },
        failure: function(data) {
            alert('Can\'t set datepicker');
        }
    });

});


function setDatePicker(data) {
    dates=Array();
    for(let i=0; i<data.length; i++){
        dates.push(
            moment(data[i])
        )
    }

    $('#datetimepicker4').datetimepicker({
        format: 'DD/MM/YYYY',
        locale: 'it',
        useCurrent: false,
        minDate: new Date(),
        disabledDates: dates,    // disabele dates when book is not available
    });
}


