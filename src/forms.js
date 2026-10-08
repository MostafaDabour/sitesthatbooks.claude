/* Sends SitesThatBook forms to a GHL inbound webhook. Files go to Cloudinary first, then their links go to GHL. */
var STB = {hook: "__HOOK__", cloud: "__CLOUD__", preset: "__PRESET__"};

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
      .then(function (j) { return j.secure_url || ""; });
  });
}

document.querySelectorAll("form[data-stb]").forEach(function (f) {
  f.addEventListener("submit", function (e) {
    e.preventDefault();
    if (f.querySelector('[name="company_website"]').value) { window.location.href = "/thanks"; return; }
    var btn = f.querySelector("button[type=submit]"), label = btn.textContent;
    var files = [].slice.call(f.querySelectorAll("input[type=file]")).filter(function (i) { return i.files.length; });
    btn.disabled = true;
    btn.textContent = files.length ? "Uploading your files..." : "Sending...";
    var data = new URLSearchParams();
    new FormData(f).forEach(function (val, key) {
      if (typeof val === "string" && key !== "company_website") { data.append(key, val); }
    });
    data.append("form_name", f.getAttribute("name"));
    data.append("page", location.pathname);
    var biz = (f.querySelector('[name="business"]') || {}).value || "lead";
    var folder = "onboarding/" + biz.toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 40);
    Promise.all(files.map(function (i) { return uploadFile(i.files[0], folder).then(function (u) { return [i.name, u]; }); }))
      .then(function (pairs) {
        var photos = [];
        pairs.forEach(function (p) {
          if (!p[1]) { return; }
          if (p[0] === "logo") { data.append("logo_url", p[1]); } else { photos.push(p[1]); }
        });
        if (photos.length) { data.append("photo_urls", photos.join("\n")); }
        return fetch(STB.hook, {method: "POST", mode: "no-cors", body: data});
      })
      .then(function () { window.location.href = "/thanks"; })
      .catch(function () {
        btn.disabled = false; btn.textContent = label;
        var m = f.querySelector(".form-err"); if (m) { m.hidden = false; }
      });
  });
});
