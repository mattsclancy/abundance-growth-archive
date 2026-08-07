(function () {
  var list = document.getElementById("blurb-list");
  if (!list) return;

  var cards = Array.prototype.slice.call(list.querySelectorAll(".blurb-card"));
  var searchBox = document.getElementById("search-box");
  var authorBoxes = Array.prototype.slice.call(document.querySelectorAll(".f-author"));
  var topicBoxes = Array.prototype.slice.call(document.querySelectorAll(".f-topic"));
  var clearBtn = document.getElementById("clear-filters");
  var resultCount = document.getElementById("result-count");
  var noResults = document.getElementById("no-results");

  function checkedValues(boxes) {
    return boxes.filter(function (b) { return b.checked; }).map(function (b) { return b.value; });
  }

  function applyFilters() {
    var query = (searchBox && searchBox.value || "").trim().toLowerCase();
    var authors = checkedValues(authorBoxes);
    var topics = checkedValues(topicBoxes);
    var visible = 0;

    cards.forEach(function (card) {
      var matchesSearch = !query || card.dataset.search.toLowerCase().indexOf(query) !== -1;
      var matchesAuthor = !authors.length || authors.indexOf(card.dataset.author) !== -1;
      var cardTopics = card.dataset.topics ? card.dataset.topics.split("|") : [];
      var matchesTopic = !topics.length || topics.some(function (t) { return cardTopics.indexOf(t) !== -1; });
      var show = matchesSearch && matchesAuthor && matchesTopic;
      card.hidden = !show;
      if (show) visible++;
    });

    if (resultCount) resultCount.textContent = visible + " of " + cards.length + " blurbs";
    if (noResults) noResults.hidden = visible !== 0;
  }

  if (searchBox) searchBox.addEventListener("input", applyFilters);
  authorBoxes.concat(topicBoxes).forEach(function (b) { b.addEventListener("change", applyFilters); });
  if (clearBtn) {
    clearBtn.addEventListener("click", function () {
      if (searchBox) searchBox.value = "";
      authorBoxes.concat(topicBoxes).forEach(function (b) { b.checked = false; });
      applyFilters();
    });
  }

  applyFilters();
})();
