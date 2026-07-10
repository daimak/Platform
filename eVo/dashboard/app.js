console.log(
    "eVo Command Center v0.1 initialized"
);function updateLanguage() {

    const lang = LANG[currentLanguage];

    document.getElementById("command-center").textContent =
        lang.commandCenter;

    document.getElementById("operational").textContent =
        lang.operational;

    document.getElementById("current-state").textContent =
        lang.currentState;

    document.getElementById("current-title").textContent =
        lang.currentTitle;

    document.getElementById("current-text").textContent =
        lang.currentText;

}

document
    .getElementById("lang-ru")
    .onclick = () => {

        currentLanguage = "ru";

        updateLanguage();

    };

document
    .getElementById("lang-en")
    .onclick = () => {

        currentLanguage = "en";

        updateLanguage();

    };

updateLanguage();