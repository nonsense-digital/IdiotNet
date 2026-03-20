function opensearch(){
    var x = document.getElementById("search-menu")
    if (x.style.display === "block"){
        x.style.display = "none";
    } else {
        x.style.display = "block";
        document.getElementById("burger").style.display = "none"
    }
}

function openburger(){
    var x = document.getElementById("burger")
    if (x.style.display === "block"){
        x.style.display = "none";
    } else {
        x.style.display = "block";
        document.getElementById("search-menu").style.display = "none"
    }
}