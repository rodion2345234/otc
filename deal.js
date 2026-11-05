(function () {
  var params = new URLSearchParams(location.search);
  var card = document.getElementById("deal-card");
  var heading = card.querySelector("h1");
  var summary = card.querySelector(".sub");
  var details = document.getElementById("deal-details");
  var status = document.getElementById("deal-status");
  var dealId = params.get("deal_id") || "";
  var name = params.get("name") || "";
  var price = params.get("price") || "";
  var currency = params.get("currency") || "";
  var chain = params.get("chain") || "";
  var note = params.get("note") || "";
  var itemUrl = params.get("item_url") || "";
  var role = params.get("role");

  if (!/^[A-Za-z0-9_-]{1,48}$/.test(dealId) || !name || !price || !currency) {
    heading.textContent = "Сделка не найдена";
    summary.textContent = "Откройте ссылку из сообщения бота после того, как продавец отправит заявку.";
    status.textContent = "Если ссылка продолжает не работать, попросите продавца создать сделку заново.";
    return;
  }

  heading.textContent = name;
  summary.textContent = "Проверьте детали предложения и сначала согласуйте условия с администратором.";

  var rows = [
    ["Номер сделки", dealId],
    ["Тип предложения", role === "buy" ? "Покупка" : "Продажа"],
    ["Цена", price + " " + currency],
    ["Сеть", chain || "Не указана"]
  ];
  rows.forEach(function (row) {
    var item = document.createElement("div");
    item.className = "deal-detail";
    var label = document.createElement("span");
    label.textContent = row[0];
    var value = document.createElement("b");
    value.textContent = row[1];
    item.appendChild(label);
    item.appendChild(value);
    details.appendChild(item);
  });

  if (/^https:\/\//i.test(itemUrl)) {
    var linkRow = document.createElement("div");
    linkRow.className = "deal-detail";
    var label = document.createElement("span");
    label.textContent = "Ссылка на NFT";
    var link = document.createElement("a");
    link.href = itemUrl;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = "Открыть NFT";
    linkRow.appendChild(label);
    linkRow.appendChild(link);
    details.appendChild(linkRow);
  }

  if (note) {
    var noteRow = document.createElement("div");
    noteRow.className = "deal-detail";
    var noteLabel = document.createElement("span");
    noteLabel.textContent = "Комментарий";
    var noteValue = document.createElement("b");
    noteValue.textContent = note;
    noteRow.appendChild(noteLabel);
    noteRow.appendChild(noteValue);
    details.appendChild(noteRow);
  }

  details.hidden = false;

  if (window.Telegram && window.Telegram.WebApp) {
    document.getElementById("deal-admin").addEventListener("click", function (event) {
      event.preventDefault();
      window.Telegram.WebApp.openTelegramLink("https://t.me/NFT_Exchanger1");
    });
  }
})();
