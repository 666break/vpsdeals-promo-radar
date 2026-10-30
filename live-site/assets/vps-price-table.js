/* Sort + filter for the 36-row price table on /vps-price.
   The table body is static HTML in the page. This file only reorders rows and
   hides them; it never creates a row and never fetches anything. */
(function () {
  'use strict';

  var root = document.getElementById('vps-price');
  if (!root) return;

  var table = root.querySelector('table.vpt-table');
  if (!table || !table.tHead || !table.tBodies.length) return;

  var tbody = table.tBodies[0];
  var rows = Array.prototype.slice.call(tbody.rows);
  var ths = Array.prototype.slice.call(table.tHead.rows[0].cells);
  var total = rows.length;

  var selProvider = document.getElementById('vpt-provider');
  var selRegion = document.getElementById('vpt-region');
  var selRam = document.getElementById('vpt-ram');
  var btnReset = document.getElementById('vpt-reset');
  var outCount = document.getElementById('vpt-count');

  var NA = '\u672a\u53d6\u5f97';

  function isNA(td) {
    return !td || td.textContent.indexOf(NA) !== -1;
  }

  function toNum(td) {
    if (isNA(td)) return null;
    var m = td.textContent.match(/(\d+(?:\.\d+)?)/);
    return m ? parseFloat(m[1]) : null;
  }

  function toSize(td) {
    if (isNA(td)) return null;
    var m = td.textContent.match(/(\d+(?:\.\d+)?)\s*(TiB|TB|GiB|GB|MiB|MB)/i);
    if (!m) return null;
    var n = parseFloat(m[1]);
    var u = m[2].toLowerCase();
    if (u === 'tb' || u === 'tib') n *= 1024;
    else if (u === 'mb' || u === 'mib') n /= 1024;
    return n;
  }

  function toText(td) {
    return isNA(td) ? null : td.textContent.trim().toLowerCase();
  }

  function toDate(td) {
    return isNA(td) ? null : td.textContent.trim();
  }

  var PARSERS = { text: toText, num: toNum, size: toSize, date: toDate };

  function sortRows(idx, kind, dir) {
    var read = PARSERS[kind] || toText;
    rows.sort(function (a, b) {
      var va = read(a.cells[idx]);
      var vb = read(b.cells[idx]);
      if (va === null && vb === null) return 0;
      if (va === null) return 1;
      if (vb === null) return -1;
      if (typeof va === 'number' && typeof vb === 'number') return (va - vb) * dir;
      return String(va).localeCompare(String(vb)) * dir;
    });
    var frag = document.createDocumentFragment();
    for (var i = 0; i < rows.length; i++) frag.appendChild(rows[i]);
    tbody.appendChild(frag);
  }

  function ramBand(td) {
    var gb = toSize(td);
    if (gb === null) return '';
    if (gb <= 1) return 'le1';
    if (gb <= 2) return '2';
    if (gb <= 4) return '4';
    return 'gt4';
  }

  function applyFilters() {
    var p = selProvider ? selProvider.value : '';
    var r = selRegion ? selRegion.value : '';
    var m = selRam ? selRam.value : '';
    var shown = 0;

    for (var i = 0; i < rows.length; i++) {
      var tr = rows[i];
      var okP = !p || toText(tr.cells[0]) === p;
      var okR = !r || toText(tr.cells[7]) === r;
      var okM = !m || ramBand(tr.cells[5]) === m;
      var ok = okP && okR && okM;
      tr.style.display = ok ? '' : 'none';
      if (ok) shown++;
    }

    if (outCount) outCount.textContent = 'Showing ' + shown + ' of ' + total + ' rows';
  }

  function bindSort(th, idx) {
    var kind = th.getAttribute('data-sort');
    th.classList.add('vpt-sortable');
    th.tabIndex = 0;
    th.setAttribute('role', 'button');

    function fire() {
      var dir = th.getAttribute('aria-sort') === 'ascending' ? -1 : 1;
      for (var i = 0; i < ths.length; i++) ths[i].removeAttribute('aria-sort');
      th.setAttribute('aria-sort', dir === 1 ? 'ascending' : 'descending');
      sortRows(idx, kind, dir);
      applyFilters();
    }

    th.addEventListener('click', fire);
    th.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        fire();
      }
    });
  }

  for (var i = 0; i < ths.length; i++) {
    if (ths[i].hasAttribute('data-sort')) bindSort(ths[i], i);
  }

  [selProvider, selRegion, selRam].forEach(function (s) {
    if (s) s.addEventListener('change', applyFilters);
  });

  if (btnReset) {
    btnReset.addEventListener('click', function () {
      [selProvider, selRegion, selRam].forEach(function (s) {
        if (s) s.value = '';
      });
      for (var i = 0; i < ths.length; i++) ths[i].removeAttribute('aria-sort');
      sortRows(0, 'text', 1);
      applyFilters();
    });
  }

  applyFilters();
})();
