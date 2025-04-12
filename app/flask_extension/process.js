function connectServer(currentUrl){
    fetch("http://127.0.0.1:8000/extension",{
        method: "POST",
        headers: {"Content-type": "application/json"},
        body: JSON.stringify({url:currentUrl})
    }) // This will be changed to the actual server
    .then (response => response.json())
    .then (data => {
        if(data.redirect_url){
            window.open(`http://127.0.0.1:8000${data.redirect_url}`, "_blank")
        }
    }
    );
    
}

document.addEventListener("DOMContentLoaded", () => {
    var scrapeBtn = document.getElementById("scrapeBtn");
    scrapeBtn.addEventListener("click", () => {
        chrome.tabs.query({active:true,currentWindow:true}, function(tabs){
            const currentUrl = tabs[0].url;
            connectServer(currentUrl);
        })
    });
})
