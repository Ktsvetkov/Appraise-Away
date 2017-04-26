function httpGetAsync(theUrl, callback) {
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.onreadystatechange = function() {
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
            callback(xmlHttp.responseText);
    }
    xmlHttp.open("GET", theUrl, true); // true for asynchronous
    xmlHttp.send(null);
}

function numberWithCommas(x) {
    var parts = x.toString().split(".");
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    return parts.join(".");
}

function reloadNewK(newK) {
    k_val = newK;
    getResults();
}

function loadInitialForm() {
    var contentArea  = document.getElementById("contentArea");
    var attributes = ["Bedrooms", "Bathrooms", "Zipcode", "Square-Feet", "Year-Built"];
    var htmlToSet = "";
    htmlToSet += "<form id=\"attributeForm\" action=\"javascript:retrieveAttributes();\"><h3>Property Info:</h3>";
    htmlToSet += "<input type=\"hidden\" name=\"k_val\" value=\"3\" id=\"k_val_id\">"
    attributes.forEach(function(attribute) {
        htmlToSet += attribute + ":<br><input id=\"" + attribute + "_id\" type=\"text\" name=" + attribute + "><br><br>";
    });
    htmlToSet += "<input id=\"actionButton\" type=\"submit\" value=\"Appraise Now!\"></form>";
    contentArea.innerHTML = htmlToSet;
}

function loadPic(responseText) {
    var contentArea  = document.getElementById("contentArea");
    var jsonObject = JSON.parse(responseText);
    if (jsonObject.image_url == "") {
        jsonObject.image_url = defaultHouseUrl;
    }
    console.log(jsonObject.image_url)
    var imageToAdd = "<img class=\"propertyImage\" src=" + jsonObject.image_url + " ></img>";
    imageToAdd = imageToAdd + "<a href=\"" + "http://www.zillow.com/homedetails/" + jsonObject.zpid + "_zpid/" + "\"><br>Click Here For More Information</a><br><br>"
    contentArea.innerHTML = contentArea.innerHTML + imageToAdd
}

function urlCallBack(responseText) {
    var contentArea  = document.getElementById("contentArea");
    var htmlToSet = "";
    var jsonObject = JSON.parse(responseText);
    htmlToSet += "<h3>Estimated Price:</h3><font size=\"6\" color=\"green\">$" + numberWithCommas(parseFloat(jsonObject.price_prediction).toFixed(2)) + "</font>";
    htmlToSet += "<br><br><button id=\"actionButton\" onclick=\"loadInitialForm()\">Try Again!</button>";
    htmlToSet += "<h3>Similar Houses:</h3>";

    htmlToSet += "Number of Houses: <select name=\"drop_down_k\" onchange=\"reloadNewK(this.value)\"><option value=\"" + k_val + "\">" + k_val + "</option>";
    for(var i = 0; i < 10; i++) {
        htmlToSet += "<option value=\"" + (i+1) + "\">" + (i+1) + "</option>";
    }
    htmlToSet += "</select><br><br>";
    contentArea.innerHTML = htmlToSet;
    var root_url = "http://" + window.location.hostname;
    if (window.location.hostname == "127.0.0.1") {
        root_url += ":8000"
    }
    var requestUrls = [];
    for (var key in jsonObject.neighbors) {
        if (jsonObject.neighbors.hasOwnProperty(key)) {
            requestUrls.push(root_url + "/appraiseaway/getZillowData/?zpid=" + jsonObject.neighbors[key].zpid)
            //htmlToSet = htmlToSet + jsonObject.neighbors[key].zpid + ", "
        }
    }
    requestUrls.forEach(function(requestUrl) {
        httpGetAsync(requestUrl, loadPic)
    });
}

function getResults() {
    var root_url = "http://" + window.location.hostname;
    if (window.location.hostname == "127.0.0.1") {
        root_url += ":8000"
    }
    var getUrl = root_url + "/appraiseaway/classifyInstance/?";
    getUrl += "k_val=" + k_val + "&";
    getUrl += "bedrooms=" + bedrooms + "&";
    getUrl += "bathrooms=" + bathrooms + "&";
    getUrl += "zip_code=" + zipcode + "&";
    getUrl += "home_size=" + sqft + "&";
    getUrl += "year_built=" + yearbuilt
    httpGetAsync(getUrl, urlCallBack);
}

function retrieveAttributes() {
    k_val = document.getElementById("k_val_id").value;
    bedrooms = document.getElementById("Bedrooms_id").value;
    bathrooms = document.getElementById("Bathrooms_id").value;
    zipcode = document.getElementById("Zipcode_id").value;
    sqft = document.getElementById("Square-Feet_id").value;
    yearbuilt = document.getElementById("Year-Built_id").value;
    getResults();
}