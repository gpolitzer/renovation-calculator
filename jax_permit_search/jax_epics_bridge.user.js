// ==UserScript==
// @name         JAX EPICS — BRRRR Calculator Bridge
// @namespace    https://jaxepics.coj.net/
// @version      1.1
// @description  Auto-fetches permits when BRRRR Calculator opens this page
// @author       BRRRR Calculator
// @match        https://jaxepics.coj.net/Search/AdvancedSearch*
// @grant        none
// @run-at       document-idle
// ==/UserScript==

(async function () {
    'use strict';

    /* ── Only activate when opened by BRRRR Calculator ── */
    const hash = window.location.hash || '';
    const m = hash.match(/[#&]brrrr-addr=([^&]*)/);
    if (!m) return;

    const addr = decodeURIComponent(m[1].replace(/\+/g, ' '));

    /* ── Loading overlay ── */
    const ov = document.createElement('div');
    ov.id = 'brrrr-overlay';
    ov.style.cssText = [
        'position:fixed;top:0;left:0;right:0;bottom:0',
        'background:rgba(0,0,20,.88)',
        'z-index:999999',
        'display:flex;align-items:center;justify-content:center',
        'font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif'
    ].join(';');
    ov.innerHTML = `
      <div id="brrrr-box" style="background:#12122a;border:1px solid rgba(233,69,96,.45);border-radius:14px;
        padding:32px 40px;max-width:660px;width:92%;color:#e8e8e8;box-shadow:0 8px 40px rgba(0,0,0,.6);">
        <div style="font-size:.85rem;color:#888;margin-bottom:6px;">🏠 BRRRR Calculator</div>
        <div style="font-size:1.3rem;font-weight:700;color:#ff6b35;margin-bottom:14px;">Fetching permits…</div>
        <div style="background:#0d0d1e;padding:8px 14px;border-radius:7px;font-family:monospace;font-size:.95rem;">${esc(addr)}</div>
        <div id="brrrr-status" style="margin-top:18px;color:#888;font-size:.9rem;">Connecting to JAX EPICS API…</div>
      </div>`;
    document.body.appendChild(ov);

    /* ── Call the API (CORS allowed because we are on jaxepics.coj.net) ── */
    const API = 'https://jaxepicsapi.coj.net/api/AdvancedSearches/Advanced'
        + '?page=1&pageSize=200&filter=&sortActive=FullPermitNumber&sortDirection=asc&forSpreadSheet=false';

    const now = new Date().toDateString();
    const body = {
        SavedSearchColumns: [1,2,3,4,5,6,7,8].map(id => ({ColumnId: id})),
        SavedSearchFilters: [{
            SavedSearchFilterId:0, SavedSearchId:0, ColumnId:8, OperatorId:2, Order:-1,
            Obj:{SearchString:addr}, groupedSectionControls:{}, Completed:true,
            DateEntered:now, DateUpdated:now,
            EvalValueString: JSON.stringify({SearchString:addr}),
            IsActive:true, SavedSearch:null, DisplayInWidget:true, PinnedInWidget:false, Sort:0
        }],
        UserSavedSearches:[], UserSavedSearchWidgets:[], TableId:82
    };

    let permits = [], errorMsg = null;

    try {
        const res = await fetch(API, {
            method: 'POST',
            headers: {
                'content-type': 'application/json',
                'accept': 'application/json, text/plain, */*',
                'ignoreloading': ''
            },
            body: JSON.stringify(body)
        });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        permits = data.values || data.data?.values || [];
    } catch (e) {
        errorMsg = e.toString();
    }

    /* ── Try to send results back to the BRRRR Calculator tab ── */
    let sentToOpener = false;
    try {
        if (window.opener && !window.opener.closed) {
            window.opener.postMessage(
                { type: 'jaxepics_results', address: addr, permits, error: errorMsg },
                '*'
            );
            sentToOpener = true;
            await new Promise(r => setTimeout(r, 600));
            window.close();
            return;
        }
    } catch (e) { /* COOP header blocked opener access — fall through to overlay */ }

    /* ── Fallback: show results in overlay on this page ── */
    const box = document.getElementById('brrrr-box');
    let content = '';

    if (errorMsg) {
        content = `<div style="margin-top:16px;color:#ff6b35;">⚠️ ${esc(errorMsg)}</div>`;
    } else if (permits.length === 0) {
        content = `<div style="margin-top:16px;color:#aaa;">ℹ️ No permits found for this address.</div>`;
    } else {
        const rows = permits.map(p => {
            const num   = p.FullPermitNumber  || '';
            const click = p.FullPermitNumber_Click || '';
            const type  = p.PermitTypeDescription  || '';
            const work  = p.WorkTypeDescription    || '';
            const stat  = p.StatusDescription      || '';
            const di    = p.DateIssued || '';
            let year = ''; const ym = di.match(/(\d{4})/); if (ym) year = ym[1];
            if (!year) { const pm = num.match(/-(\d{4})-/); if (pm) year = pm[1]; }
            const link = click
                ? `<a href="https://jaxepics.coj.net/${esc(click)}" target="_blank"
                     style="color:#ff6b35;text-decoration:none;font-family:monospace;">${esc(num)} ↗</a>`
                : `<span style="font-family:monospace;">${esc(num)}</span>`;
            return `<tr style="border-bottom:1px solid #1e1e3a;">
                <td style="padding:7px 10px;">${link}</td>
                <td style="padding:7px 10px;color:#ccc;">${esc(type)}</td>
                <td style="padding:7px 10px;color:#999;">${esc(work)}</td>
                <td style="padding:7px 10px;color:#999;">${esc(stat)}</td>
                <td style="padding:7px 10px;color:#888;text-align:center;">${esc(year)}</td>
            </tr>`;
        }).join('');

        content = `
          <div style="color:#4CAF50;margin-top:14px;margin-bottom:10px;">
            ✓ Found <strong>${permits.length}</strong> permit(s)
          </div>
          <div style="overflow-x:auto;max-height:380px;overflow-y:auto;">
            <table style="width:100%;border-collapse:collapse;font-size:.82rem;">
              <thead>
                <tr style="background:#0d0d1e;color:#ff6b35;position:sticky;top:0;">
                  <th style="padding:8px 10px;text-align:left;">Permit #</th>
                  <th style="padding:8px 10px;text-align:left;">Type</th>
                  <th style="padding:8px 10px;text-align:left;">Work</th>
                  <th style="padding:8px 10px;text-align:left;">Status</th>
                  <th style="padding:8px 10px;text-align:center;">Year</th>
                </tr>
              </thead>
              <tbody>${rows}</tbody>
            </table>
          </div>`;
    }

    box.innerHTML = `
      <div style="font-size:.85rem;color:#888;margin-bottom:6px;">🏠 BRRRR Calculator</div>
      <div style="font-size:1.1rem;font-weight:700;color:#ff6b35;margin-bottom:10px;">
        Permits — ${esc(addr)}
      </div>
      ${content}
      <button onclick="document.getElementById('brrrr-overlay').remove()"
        style="margin-top:20px;background:#ff6b35;border:none;color:#fff;
               padding:9px 22px;border-radius:7px;cursor:pointer;font-size:.9rem;font-weight:600;">
        Close
      </button>`;

    /* ── helpers ── */
    function esc(s) {
        return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    }
})();
