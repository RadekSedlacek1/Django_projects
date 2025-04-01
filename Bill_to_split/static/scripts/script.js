document.addEventListener("DOMContentLoaded", function () {
    console.log("JavaScript is loaded successfully!");

    // dark / light mode switch
    document.getElementById("theme-toggle").addEventListener("click", function () {
        const html = document.documentElement;
        const currentTheme = html.getAttribute("data-theme") || "auto";
        const newTheme = currentTheme === "light" ? "dark" : "light";
        html.setAttribute("data-theme", newTheme);
        localStorage.setItem("theme", newTheme);
    });

    // color scheme switch
    document.querySelectorAll("#color-options button").forEach((btn) => {
        btn.addEventListener("click", function () {
            const selectedColor = this.getAttribute("data-color");
            document.getElementById("theme-stylesheet").setAttribute("href", selectedColor);
            localStorage.setItem("color-theme", selectedColor);
        });
    });
});
