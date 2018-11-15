var active_loans, dead_loans,rent_reservations;

$(function () {

    /* initialize global ref */
    active_loans = $("#active_loans");
    dead_loans = $("#dead_loans");
    rent_reservations = $("#rent_reservations");
    cons_reservations = $("#cons_reservations");
    messages = $("#messages");

    title = $("#section_title");

    var sections = [
        "active_loans",
        "dead_loans",
        "rent_reservations",
        "cons_reservations",
        "messages"
    ];

    hide_all_except("messages");

    /* listeners */
    $("#active_loans_btn").on("click", function () {
        hide_all_except("active_loans");
        title.text("Prestiti in corso");
        active_loans.show()
    });

    $("#dead_loans_btn").on("click", function () {
        hide_all_except("dead_loans");
        title.text("Storico prestiti");
        dead_loans.show()
    });

    $("#rent_reservations_btn").on("click", function () {
        hide_all_except("rent_reservations");
        title.text("Prenotazioni prestiti");
        rent_reservations.show()
    });

    $("#cons_reservations_btn").on("click", function () {
        hide_all_except("cons_reservations");
        title.text("Prenotazioni libri in consultazione");
        cons_reservations.show()
    });


    function hide_all_except(id){
        for(var i=0; i<sections.length; i++){

            if(sections[i] == id){

            }else{
                $("#"+sections[i]).hide()
            }

        }
    }
});


