// Small helper functions used across the ServiceFinder pages

function confirmAction(message) {
    return confirm(message);
}

function setRating(value) {
    document.getElementById("rating_input").value = value;
    var stars = document.getElementsByClassName("star");
    for (var i = 0; i < stars.length; i++) {
        if (i < value) {
            stars[i].style.color = "#f1c40f";
        } else {
            stars[i].style.color = "#ccc";
        }
    }
}
