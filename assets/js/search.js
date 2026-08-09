(function () {
  "use strict";

  var list = document.getElementById("post-list");
  if (!list) { return; }

  var items = Array.prototype.slice.call(list.querySelectorAll(".post-list-item"));
  var statusEl = document.getElementById("search-status");
  var emptyEl = document.getElementById("search-empty");
  var searchInput = document.getElementById("blog-search");
  var clearBtn = document.getElementById("search-clear");
  var categoryWrap = document.getElementById("category-filters");
  var tagWrap = document.getElementById("tag-filters");

  var index = [];
  var indexScript = document.getElementById("search-index");
  if (indexScript) {
    try { index = JSON.parse(indexScript.textContent); } catch (e) { index = []; }
  }

  var state = { q: "", category: "", tag: "" };

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function norm(s) {
    return String(s || "").toLowerCase();
  }

  function tokenize(q) {
    return norm(q).split(/\s+/).filter(Boolean);
  }

  function postFor(item) {
    if (index.length) {
      var link = item.querySelector(".post-list-title a");
      var raw = link ? link.getAttribute("href") : "";
      var url = raw.replace(/^\.\.\//, "");
      var altUrl = url.replace(/^blog\//, "");
      for (var i = 0; i < index.length; i++) {
        if (index[i].url === url || index[i].url === altUrl) { return index[i]; }
      }
    }
    return {
      title: item.getAttribute("data-title") || "",
      excerpt: item.getAttribute("data-excerpt") || "",
      category: item.getAttribute("data-category") || "",
      tags: (item.getAttribute("data-tags") || "").split(",").filter(Boolean),
      content: ""
    };
  }

  function matches(post, terms) {
    if (state.category && post.category !== state.category) { return false; }
    if (state.tag && post.tags.indexOf(state.tag) === -1) { return false; }
    if (!terms.length) { return true; }
    var hay = [post.title, post.excerpt, post.category].concat(post.tags).join(" ");
    hay += " " + (post.content || "");
    hay = norm(hay);
    return terms.every(function (t) { return hay.indexOf(t) !== -1; });
  }

  function highlight(text, terms) {
    var lower = norm(text);
    var out = "";
    var i = 0;
    while (i < text.length) {
      var found = -1;
      var foundTerm = null;
      for (var k = 0; k < terms.length; k++) {
        var idx = lower.indexOf(terms[k], i);
        if (idx !== -1 && (found === -1 || idx < found)) {
          found = idx;
          foundTerm = terms[k];
        }
      }
      if (found === -1) {
        out += escapeHtml(text.slice(i));
        break;
      }
      out += escapeHtml(text.slice(i, found));
      out += "<mark>" + escapeHtml(text.slice(found, found + foundTerm.length)) + "</mark>";
      i = found + foundTerm.length;
    }
    return out;
  }

  function apply() {
    var terms = tokenize(state.q);
    var visible = 0;
    items.forEach(function (item) {
      var post = postFor(item);
      var show = matches(post, terms);
      item.hidden = !show;
      if (show) {
        visible += 1;
        var titleLink = item.querySelector(".post-list-title a");
        var excerpt = item.querySelector(".post-list-excerpt");
        if (titleLink) {
          titleLink.innerHTML = highlight(post.title, terms);
        }
        if (excerpt) {
          excerpt.innerHTML = highlight(post.excerpt, terms);
        }
      }
    });
    if (statusEl) {
      if (terms.length || state.category || state.tag) {
        statusEl.textContent = "找到 " + visible + " / " + items.length + " 篇文章";
      } else {
        statusEl.textContent = "";
      }
    }
    if (emptyEl) {
      emptyEl.hidden = visible !== 0;
    }
    if (searchInput) {
      var box = searchInput.closest(".search-box");
      if (box) { box.classList.toggle("has-text", !!state.q); }
    }
  }

  function setChip(group, value) {
    if (!group) { return; }
    group.querySelectorAll(".filter-chip").forEach(function (chip) {
      chip.classList.toggle("active", chip.getAttribute("data-value") === value);
    });
  }

  function syncUrl() {
    if (!window.history || !window.history.replaceState) { return; }
    var params = new URLSearchParams(window.location.search);
    if (state.q) {
      params.set("q", state.q);
    } else {
      params.delete("q");
    }
    var qs = params.toString();
    window.history.replaceState(null, "", window.location.pathname + (qs ? "?" + qs : ""));
  }

  function onSearchInput() {
    state.q = searchInput ? searchInput.value : "";
    apply();
    syncUrl();
  }

  if (searchInput) {
    searchInput.addEventListener("input", onSearchInput);
    searchInput.addEventListener("search", onSearchInput);
  }
  if (clearBtn) {
    clearBtn.addEventListener("click", function () {
      state.q = "";
      if (searchInput) { searchInput.value = ""; }
      apply();
      syncUrl();
      if (searchInput) { searchInput.focus(); }
    });
  }

  function bindFilters(wrap, key) {
    if (!wrap) { return; }
    wrap.addEventListener("click", function (e) {
      var chip = e.target.closest(".filter-chip");
      if (!chip) { return; }
      state[key] = chip.getAttribute("data-value") || "";
      setChip(wrap, state[key]);
      apply();
    });
  }
  bindFilters(categoryWrap, "category");
  bindFilters(tagWrap, "tag");

  // 从 URL 读取初始搜索词
  var params = new URLSearchParams(window.location.search);
  var q = params.get("q") || "";
  if (q && searchInput) {
    state.q = q;
    searchInput.value = q;
  }
  apply();
})();
