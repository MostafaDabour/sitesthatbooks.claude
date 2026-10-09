/* Sends SitesThatBook forms to a GHL inbound webhook. Files go to Cloudinary first, then their links go to GHL. */
var STB = {hook: "__HOOK__", cloud: "__CLOUD__", preset: "__PRESET__", errors: []};

document.querySelectorAll("[data-show-when]").forEach(function (box) {
  var n = box.getAttribute("data-show-when"), v = box.getAttribute("data-show-value");
  document.querySelectorAll('input[name="' + n + '"]').forEach(function (r) {
    r.addEventListener("change", function () { box.hidden = !(r.checked && r.value === v); });
  });
});

document.querySelectorAll(".drop input[type=file]").forEach(function (inp) {
  inp.addEventListener("change", function () {
    var s = inp.parentNode.querySelector(".drop-file");
    s.textContent = inp.files.length ? inp.files[0].name : "No file chosen";
    inp.parentNode.classList.toggle("has", !!inp.files.length);
  });
});

function shrink(file) {
  return new Promise(function (res) {
    if (!/^image\/(jpeg|png|webp)/i.test(file.type) || file.size < 600000) { return res(file); }
    var img = new Image(), url = URL.createObjectURL(file);
    img.onload = function () {
      var k = Math.min(1, 1800 / Math.max(img.width, img.height));
      var c = document.createElement("canvas");
      c.width = Math.round(img.width * k); c.height = Math.round(img.height * k);
      c.getContext("2d").drawImage(img, 0, 0, c.width, c.height);
      c.toBlob(function (b) {
        URL.revokeObjectURL(url);
        res(b ? new File([b], file.name.replace(/\.[^.]+$/, "") + ".jpg", {type: "image/jpeg"}) : file);
      }, "image/jpeg", 0.82);
    };
    img.onerror = function () { res(file); };
    img.src = url;
  });
}

function uploadFile(file, folder) {
  return shrink(file).then(function (f) {
    var fd = new FormData();
    fd.append("file", f);
    fd.append("upload_preset", STB.preset);
    fd.append("folder", folder);
    return fetch("https://api.cloudinary.com/v1_1/" + STB.cloud + "/auto/upload", {method: "POST", body: fd})
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (j.secure_url) { return j.secure_url; }
        STB.errors.push((j.error && j.error.message) || "no url returned");
        return "";
      })
      .catch(function (err) { STB.errors.push("network: " + (err && err.message)); return ""; });
  });
}

document.querySelectorAll("form[data-stb]").forEach(function (f) {
  f.addEventListener("submit", function (e) {
    e.preventDefault();
    if (f.querySelector('[name="company_website"]').value) { window.location.href = "/thanks"; return; }
    var btn = f.querySelector("button[type=submit]"), label = btn.textContent;
    var chosen = [].slice.call(f.querySelectorAll("input[type=file]")).filter(function (i) { return i.files.length; });
    var canUpload = STB.cloud.indexOf("PASTE") !== 0 && STB.preset.indexOf("PASTE") !== 0;
    var files = canUpload ? chosen : [];
    btn.disabled = true;
    btn.textContent = files.length ? "Uploading your files..." : "Sending...";
    var data = new URLSearchParams();
    new FormData(f).forEach(function (val, key) {
      if (typeof val === "string" && key !== "company_website") { data.append(key, val); }
    });
    data.append("form_name", f.getAttribute("name"));
    data.append("page", location.pathname);
    if (!canUpload && chosen.length) { data.append("files_note", "Client attached " + chosen.length + " file(s) but uploads are not connected yet. Ask them to text or email the logo and photos."); }
    var biz = (f.querySelector('[name="business"]') || {}).value || "lead";
    var folder = "onboarding/" + biz.toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 40);
    Promise.all(files.map(function (i) { return uploadFile(i.files[0], folder).then(function (u) { return [i.name, u]; }); }))
      .then(function (pairs) {
        var photos = [], failed = 0;
        pairs.forEach(function (p) {
          if (!p[1]) { failed++; return; }
          if (p[0] === "logo") { data.append("logo_url", p[1]); } else { photos.push(p[1]); }
        });
        if (photos.length) { data.append("photo_urls", photos.join("\n")); }
        if (failed) {
          data.append("files_note", failed + " file(s) failed to upload. Ask the client to text or email them.");
          data.append("upload_error", STB.errors.slice(0, 2).join(" | "));
        }
        return fetch(STB.hook, {method: "POST", mode: "no-cors", body: data});
      })
      .then(function () {
        var go = function () { window.location.href = "/thanks"; };
        if (window.fbq) {
          if (f.dataset.leadSent) { window.fbq("track", "CompleteRegistration", { content_name: "onboarding_details" }); }
          else { window.fbq("track", "Lead", { content_name: f.getAttribute("name") }); }
        }
        if (window.gtag) {
          var done = false, once = function () { if (!done) { done = true; go(); } };
          window.gtag("event", f.dataset.leadSent ? "onboarding_complete" : "generate_lead", { form_name: f.getAttribute("name"), event_callback: once });
          setTimeout(once, 800);
        } else { go(); }
      })
      .catch(function () {
        btn.disabled = false; btn.textContent = label;
        var m = f.querySelector(".form-err"); if (m) { m.hidden = false; }
      });
  });
});

// Two step onboarding: step 1 sends the lead right away, step 2 is optional detail
document.querySelectorAll("[data-step-next]").forEach(function (btn) {
  var f = btn.closest("form");
  btn.addEventListener("click", function () {
    var step1 = [].slice.call(f.querySelectorAll(":scope > .field input, :scope > .field select"));
    for (var i = 0; i < step1.length; i++) { if (!step1[i].reportValidity()) { return; } }
    btn.disabled = true; btn.textContent = "One sec...";
    var data = new URLSearchParams();
    step1.forEach(function (el) { data.append(el.name, el.value); });
    data.append("form_name", "onboarding_lead");
    data.append("page", location.pathname);
    var show = function () {
      f.querySelectorAll(":scope > .field, :scope > .form-step-head, :scope > .step1-actions").forEach(function (el) { el.hidden = true; });
      var s2 = f.querySelector(".step2"); s2.hidden = false;
      f.dataset.leadSent = "1";
      var first = (f.querySelector("[name=name]").value || "").split(" ")[0];
      var h = s2.querySelector("h3"); if (first) { h.textContent = "Thanks " + first + ". Step 2: tell us about your business"; }
      s2.scrollIntoView({ behavior: "smooth", block: "start" });
    };
    fetch(STB.hook, { method: "POST", mode: "no-cors", body: data }).catch(function () {}).then(function () {
      if (window.gtag) { window.gtag("event", "generate_lead", { form_name: "onboarding_lead" }); }
      if (window.fbq) { window.fbq("track", "Lead", { content_name: "onboarding_step1" }); }
      show();
    });
  });
});
