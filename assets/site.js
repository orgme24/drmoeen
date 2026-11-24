/* DR.MOEEN AESTHETICS — site behaviour */
(function () {
  "use strict";

  /* -------- Mobile menu -------- */
  var toggle = document.querySelector(".menu-toggle");
  var nav = document.getElementById("primary-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    nav.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", function () {
        nav.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  /* -------- Hero clinic film -------- */
  var hero = document.querySelector(".hero");
  if (hero) {
    var video = hero.querySelector(".hero-video");
    var filmBtn = hero.querySelector(".film-btn");
    var start = function () {
      if (!video) return;
      hero.classList.add("playing");
      video.classList.add("ctrl");
      video.setAttribute("controls", "controls");
      var p = video.play();
      if (p && p.catch) p.catch(function () {});
      video.focus && video.focus();
    };
    if (filmBtn) filmBtn.addEventListener("click", start);
    if (video) {
      video.addEventListener("pause", function () {
        if (video.currentTime === 0) {
          hero.classList.remove("playing");
          video.classList.remove("ctrl");
          video.removeAttribute("controls");
        }
      });
      video.addEventListener("error", function () {
        var lbl = filmBtn && filmBtn.querySelector(".lbl");
        if (lbl) lbl.textContent = "לא ניתן לטעון את הסרטון כעת";
      });
    }
  }

  /* -------- Contact form --------
     Configure a real endpoint by setting window.DRMOEEN_FORM_ENDPOINT
     (e.g. a Formspree / Getform URL) in a small inline script, or via
     data-endpoint on the form. Until configured, the form does NOT fake a
     submission: it tells the visitor to call / WhatsApp instead. */
  var form = document.getElementById("contact-form");
  if (form) {
    var endpoint = form.getAttribute("data-endpoint") || window.DRMOEEN_FORM_ENDPOINT || "";
    var status = form.querySelector(".form-status");
    var submitBtn = form.querySelector('button[type="submit"]');

    var setStatus = function (type, msg) {
      if (!status) return;
      status.className = "form-status " + type;
      status.textContent = msg;
    };
    var markField = function (field, invalid) {
      var wrap = field.closest(".field") || field.closest(".consent");
      if (wrap) wrap.classList.toggle("invalid", invalid);
    };
    var validate = function () {
      var ok = true;
      form.querySelectorAll("[required]").forEach(function (f) {
        var bad = (f.type === "checkbox") ? !f.checked : !String(f.value).trim();
        if (!bad && f.type === "email") bad = !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.value);
        if (!bad && f.type === "tel") bad = String(f.value).replace(/\D/g, "").length < 7;
        markField(f, bad);
        if (bad && ok) { f.focus(); }
        if (bad) ok = false;
      });
      return ok;
    };

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!validate()) { setStatus("fail", "יש למלא את כל שדות החובה בצורה תקינה."); return; }

      if (!endpoint) {
        setStatus("fail",
          "טופס ההזמנה עדיין אינו מחובר לשרת בגרסת הדמו. " +
          "כדי לקבוע תור ניתן לחייג 072-394-5160 או לפנות בוואטסאפ. " +
          "(חיבור יעד הפנייה יוגדר לפני העלייה לאוויר.)");
        return;
      }

      if (submitBtn) { submitBtn.disabled = true; submitBtn.dataset.label = submitBtn.textContent; submitBtn.textContent = "שולח…"; }
      setStatus("", "");
      var data = new FormData(form);
      fetch(endpoint, { method: "POST", body: data, headers: { Accept: "application/json" } })
        .then(function (r) {
          if (r.ok) {
            form.reset();
            setStatus("ok", "הפנייה נשלחה בהצלחה. נחזור אליך בהקדם. זוהי בקשת תיאום בלבד ואינה אישור תור.");
          } else {
            setStatus("fail", "אירעה שגיאה בשליחה. ניתן לחייג 072-394-5160 או לנסות שוב מאוחר יותר.");
          }
        })
        .catch(function () {
          setStatus("fail", "אין חיבור כרגע. ניתן לחייג 072-394-5160 או לנסות שוב מאוחר יותר.");
        })
        .finally(function () {
          if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = submitBtn.dataset.label || "שלח/י"; }
        });
    });
  }

  /* -------- Current year -------- */
  var y = document.getElementById("year");
  if (y) y.textContent = new Date().getFullYear();
})();
