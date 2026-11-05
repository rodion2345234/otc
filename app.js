var tg = window.Telegram && window.Telegram.WebApp;
if (tg) { tg.ready(); tg.expand(); }

function store(k, v) {
  try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; }
}
function num(k) { return parseInt(store(k), 10) || 0; }
function countOffer() { store("lolz_offers", String(num("lolz_offers") + 1)); }

function toast(msg) {
  var t = document.getElementById("toast");
  if (!t) { t = document.createElement("div"); t.id = "toast"; t.className = "toast"; document.body.appendChild(t); }
  t.textContent = msg; t.classList.add("show");
  setTimeout(function () { t.classList.remove("show"); }, 2600);
}

// the bot can open the page as index.html?deals=12 to show the real number of deals
(function () {
  var d = new URLSearchParams(location.search).get("deals");
  if (d !== null) store("lolz_deals", String(parseInt(d, 10) || 0));
})();

function el(tag, cls, text) {
  var n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text !== undefined) n.textContent = text;
  return n;
}

function makeAva(user, name) {
  var a = el("div", "ava", (name || "?").charAt(0).toUpperCase());
  if (user && user.photo_url) {
    var im = document.createElement("img");
    im.src = user.photo_url; im.alt = "";
    im.onerror = function () { im.remove(); };
    a.appendChild(im);
  }
  return a;
}

function renderTopbar() {
  var bar = document.getElementById("topbar");
  if (!bar) return;
  var user = tg && tg.initDataUnsafe && tg.initDataUnsafe.user;
  var name = user ? (user.first_name || user.username || "Профиль") : "Гость";
  var uname = user && user.username ? "@" + user.username : name;
  var deals = num("lolz_deals"), offers = num("lolz_offers");

  var brand = el("a", "brand"); brand.href = "index.html";
  var mark = el("span", "brand__mark");
  var logo = document.createElement("img");
  logo.src = "logo.webp"; logo.alt = ""; logo.setAttribute("aria-hidden", "true");
  logo.onerror = function () {
    logo.onerror = null;
    logo.src = "../logo.webp";
  };
  mark.appendChild(logo);
  brand.appendChild(mark); brand.appendChild(document.createTextNode("LolzMarket"));

  var box = el("div", "profile-box");
  var btn = el("button", "profile"); btn.type = "button"; btn.setAttribute("aria-expanded", "false");
  btn.appendChild(makeAva(user, name));
  var t = el("span", "profile__t");
  t.appendChild(el("b", "", uname)); t.appendChild(el("small", "", deals + " сделок"));
  btn.appendChild(t);

  var pop = el("div", "pop"); pop.hidden = true;
  var head = el("div", "pop__head"); head.appendChild(makeAva(user, name));
  var ht = el("div"); ht.appendChild(el("b", "", name)); ht.appendChild(el("span", "", uname));
  head.appendChild(ht); pop.appendChild(head);
  var st = el("div", "stats");
  [["Сделок", deals], ["Заявок", offers]].forEach(function (s) {
    var d = el("div"); d.appendChild(el("b", "", String(s[1]))); d.appendChild(el("span", "", s[0])); st.appendChild(d);
  });
  pop.appendChild(st);
  if (!user) pop.appendChild(el("p", "pop__note", "Открой приложение в Telegram, чтобы увидеть свой профиль."));

  btn.onclick = function (e) {
    e.stopPropagation();
    pop.hidden = !pop.hidden;
    btn.setAttribute("aria-expanded", String(!pop.hidden));
  };
  document.addEventListener("click", function (e) {
    if (!box.contains(e.target)) { pop.hidden = true; btn.setAttribute("aria-expanded", "false"); }
  });

  box.appendChild(btn); box.appendChild(pop);
  bar.appendChild(brand); bar.appendChild(box);
}
document.querySelectorAll("img[data-fallback]").forEach(function (image) {
  image.onerror = function () {
    image.onerror = null;
    image.src = image.getAttribute("data-fallback");
  };
});
renderTopbar();
