/**
 * Idle logout – 15 minuutin passiivisuus = automaattinen uloskirjaus.
 * Käyttäjän pitää kirjautua uudelleen.
 * Tekijänoikeudet S44Gaming. https://discord.gg/ujB4JHfgcg
 */
(function() {
    var IDLE_MS = 15 * 60 * 1000; // 15 minuuttia
    var timer = null;

    function resetTimer() {
        if (timer) clearTimeout(timer);
        timer = setTimeout(function() {
            // Ohjaa uloskirjautumiseen – session vanhenee ja käyttäjä ohjataan login-sivulle
            window.location.href = '/logout?reason=idle';
        }, IDLE_MS);
    }

    var events = ['mousedown', 'mousemove', 'keydown', 'scroll', 'touchstart', 'click'];
    events.forEach(function(ev) {
        document.addEventListener(ev, resetTimer, { passive: true });
    });
    resetTimer();
})();
