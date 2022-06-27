// Initialize Variables
var closePopup = document.getElementById("popupclose");
var overlay = document.getElementById("overlay");
var popup = document.getElementById("popup");
var button = document.getElementById("button");
// Close Popup Event
closePopup.onclick = function () {
    overlay.style.opacity = '0';
    overlay.style.zIndex = '-1'
    popup.style.opacity = '0';
    popup.style.zIndex = '-1';
};
// Show Overlay and Popup
button.onclick = function () {
    overlay.style.opacity = '1';
    overlay.style.zIndex = '100'
    popup.style.opacity = '1';
    popup.style.zIndex = '200';
}