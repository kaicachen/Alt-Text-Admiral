function connectServer(){
    fetch("http://127.0.0.1:8000/message") // This will be changed to the actual server
    .then (response => response.json())
    .then (data => {
        document.getElementById("message").textContent = data.message;
        console.log(data);
    }
    );
    
}

document.addEventListener("DOMContentLoaded", () => {
    var scrapeBtn = document.getElementById("scrapeBtn");
    scrapeBtn.addEventListener("click",connectServer);
})
