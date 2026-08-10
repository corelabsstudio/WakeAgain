/**
 * Shared country list (ISO 3166-1 alpha-2) + flag emoji helper.
 * Used by signup/profile country picker and listing flag badges.
 */
(function (global) {
  var COUNTRIES = [
    ["KR", "South Korea"], ["US", "United States"], ["GB", "United Kingdom"],
    ["CA", "Canada"], ["AU", "Australia"], ["NZ", "New Zealand"],
    ["JP", "Japan"], ["CN", "China"], ["TW", "Taiwan"], ["HK", "Hong Kong"],
    ["SG", "Singapore"], ["IN", "India"], ["ID", "Indonesia"], ["MY", "Malaysia"],
    ["TH", "Thailand"], ["VN", "Vietnam"], ["PH", "Philippines"],
    ["DE", "Germany"], ["FR", "France"], ["ES", "Spain"], ["IT", "Italy"],
    ["NL", "Netherlands"], ["BE", "Belgium"], ["CH", "Switzerland"],
    ["AT", "Austria"], ["SE", "Sweden"], ["NO", "Norway"], ["DK", "Denmark"],
    ["FI", "Finland"], ["IE", "Ireland"], ["PL", "Poland"], ["PT", "Portugal"],
    ["CZ", "Czechia"], ["RO", "Romania"], ["GR", "Greece"], ["HU", "Hungary"],
    ["UA", "Ukraine"], ["RU", "Russia"], ["TR", "Turkey"], ["IL", "Israel"],
    ["AE", "United Arab Emirates"], ["SA", "Saudi Arabia"],
    ["BR", "Brazil"], ["MX", "Mexico"], ["AR", "Argentina"], ["CL", "Chile"],
    ["CO", "Colombia"], ["PE", "Peru"],
    ["ZA", "South Africa"], ["NG", "Nigeria"], ["EG", "Egypt"], ["KE", "Kenya"],
    ["PK", "Pakistan"], ["BD", "Bangladesh"],
  ];

  function flagEmoji(code) {
    var c = String(code || "").trim().toUpperCase();
    if (c.length !== 2 || !/^[A-Z]{2}$/.test(c)) return "";
    return c.replace(/./g, function (ch) {
      return String.fromCodePoint(127397 + ch.charCodeAt(0));
    });
  }

  function countryName(code) {
    var c = String(code || "").trim().toUpperCase();
    var hit = COUNTRIES.find(function (x) { return x[0] === c; });
    return hit ? hit[1] : c;
  }

  function populateSelect(selectEl, selected) {
    if (!selectEl) return;
    var frag = document.createDocumentFragment();
    var blank = document.createElement("option");
    blank.value = "";
    blank.textContent = "—";
    frag.appendChild(blank);
    COUNTRIES.forEach(function (row) {
      var opt = document.createElement("option");
      opt.value = row[0];
      opt.textContent = flagEmoji(row[0]) + " " + row[1];
      if (selected && selected === row[0]) opt.selected = true;
      frag.appendChild(opt);
    });
    selectEl.innerHTML = "";
    selectEl.appendChild(frag);
  }

  global.WakeAgainCountries = {
    list: COUNTRIES,
    flagEmoji: flagEmoji,
    countryName: countryName,
    populateSelect: populateSelect,
  };
})(window);
