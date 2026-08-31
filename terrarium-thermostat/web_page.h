/*
 * web_page.h — strona sterująca (HTML + CSS + JS) trzymana we flashu.
 * Strona odpytuje /api/status i wysyła nastawy na /api/settings.
 */

#pragma once

#include <Arduino.h>

static const char INDEX_HTML[] PROGMEM = R"rawliteral(<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Terrarium — termostat</title>
<style>
  :root{
    --tlo:#07110D; --powierzchnia:#0D1913; --zielen:#829B2F;
    --tekst:#F3F4EF; --pomocniczy:#9CA59E; --blad:#D65C5C; --sukces:#6BAB6B;
    --linia:#1C2A22;
  }
  *{box-sizing:border-box}
  body{
    margin:0; padding:20px 16px 40px; background:var(--tlo); color:var(--tekst);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
    line-height:1.6;
  }
  main{max-width:520px;margin:0 auto}
  h1{font-size:1.25rem;letter-spacing:.08em;text-transform:uppercase;margin:0 0 18px}
  h2{font-size:.875rem;letter-spacing:.08em;text-transform:uppercase;color:var(--pomocniczy);margin:0 0 14px}
  .card{background:var(--powierzchnia);border:1px solid var(--linia);border-radius:14px;padding:20px;margin-bottom:16px}
  .badge{display:inline-block;font-size:.75rem;letter-spacing:.06em;text-transform:uppercase;
         padding:4px 12px;border-radius:999px;border:1px solid var(--linia);color:var(--pomocniczy)}
  .badge.heat{background:rgba(214,92,92,.15);border-color:var(--blad);color:var(--blad)}
  .badge.rest{background:rgba(130,155,47,.15);border-color:var(--zielen);color:var(--zielen)}
  .badge.idle{background:rgba(107,171,107,.12);border-color:var(--sukces);color:var(--sukces)}
  .badge.fault{background:rgba(214,92,92,.25);border-color:var(--blad);color:var(--blad)}
  .temp{font-size:4rem;line-height:1.1;font-weight:600;margin:10px 0 0}
  .temp .unit{font-size:1.5rem;color:var(--pomocniczy);margin-left:6px}
  .sub{color:var(--pomocniczy);font-size:.875rem;min-height:1.6em}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:18px;padding-top:16px;border-top:1px solid var(--linia)}
  .lbl{display:block;color:var(--pomocniczy);font-size:.75rem;text-transform:uppercase;letter-spacing:.06em}
  label{display:block;margin-bottom:16px;font-size:.875rem;color:var(--pomocniczy)}
  input[type=number]{
    width:100%;margin-top:6px;padding:10px 12px;font-size:1rem;color:var(--tekst);
    background:var(--tlo);border:1px solid var(--linia);border-radius:8px
  }
  input[type=number]:focus{outline:none;border-color:var(--zielen)}
  .stepper{display:flex;gap:8px;margin-top:6px;align-items:stretch}
  .stepper input{margin-top:0;text-align:center}
  .stepper button{
    width:52px;font-size:1.25rem;color:var(--tekst);background:var(--tlo);
    border:1px solid var(--linia);border-radius:8px;cursor:pointer
  }
  .stepper button:active{border-color:var(--zielen)}
  .switch{display:flex;align-items:center;gap:10px;color:var(--tekst);font-size:1rem}
  .switch input{width:20px;height:20px;accent-color:var(--zielen)}
  button.primary{
    width:100%;padding:12px;font-size:1rem;font-weight:600;cursor:pointer;
    background:var(--zielen);color:var(--tlo);border:0;border-radius:8px
  }
  #msg{min-height:1.4em;font-size:.875rem;margin:10px 0 0;color:var(--sukces)}
  #msg.err{color:var(--blad)}
  footer{color:var(--pomocniczy);font-size:.75rem;text-align:center;line-height:1.8}
</style>
</head>
<body>
<main>
  <h1>Terrarium — termostat</h1>

  <section class="card">
    <span class="badge" id="badge">łączenie…</span>
    <div class="temp"><span id="temp">--,-</span><span class="unit">&deg;C</span></div>
    <div class="sub" id="sub">&nbsp;</div>
    <div class="grid2">
      <div><span class="lbl">Zadana</span><b id="spOut">--</b></div>
      <div><span class="lbl">Mata grzewcza</span><b id="relOut">--</b></div>
    </div>
  </section>

  <section class="card">
    <h2>Nastawy</h2>
    <form id="form">
      <label>Temperatura zadana (&deg;C)
        <div class="stepper">
          <button type="button" data-step="-0.5">&minus;</button>
          <input id="setpoint" type="number" step="0.1" min="10" max="40" required>
          <button type="button" data-step="0.5">+</button>
        </div>
      </label>
      <label>Histereza &mdash; o ile stopni poni&#380;ej zadanej w&#322;&#261;czy&#263; grzanie (&deg;C)
        <input id="hysteresis" type="number" step="0.1" min="0.2" max="5" required>
      </label>
      <label>Przerwa po dogrzaniu &mdash; przed kolejnym pomiarem (min)
        <input id="rest" type="number" step="1" min="5" max="120" required>
      </label>
      <label class="switch"><input id="enabled" type="checkbox"> Termostat w&#322;&#261;czony</label>
      <button class="primary" type="submit">Zapisz nastawy</button>
      <p id="msg">&nbsp;</p>
    </form>
  </section>

  <footer id="foot">&nbsp;</footer>
</main>

<script>
const el = id => document.getElementById(id);
const form = el('form');
let dirty = false;      // użytkownik edytuje formularz — nie nadpisujemy pól
let msgTimer = null;

const num = (v, d) => (v === null || v === undefined || isNaN(v)) ? '--' : Number(v).toFixed(d);

function mmss(s){
  s = Math.max(0, Math.round(s));
  return Math.floor(s / 60) + ' min ' + String(s % 60).padStart(2, '0') + ' s';
}

function message(text, isError){
  const m = el('msg');
  m.textContent = text || ' ';
  m.className = isError ? 'err' : '';
  clearTimeout(msgTimer);
  if (text) msgTimer = setTimeout(() => { m.textContent = ' '; }, 4000);
}

function fillForm(d){
  el('setpoint').value = Number(d.setpoint).toFixed(1);
  el('hysteresis').value = Number(d.hysteresis).toFixed(1);
  el('rest').value = d.restMinutes;
  el('enabled').checked = !!d.enabled;
}

function render(d){
  el('temp').textContent = d.hasReading ? num(d.temp, 1).replace('.', ',') : '--,-';
  el('spOut').textContent = num(d.setpoint, 1).replace('.', ',') + ' °C';
  el('relOut').textContent = d.relay ? 'grzeje' : 'wyłączona';

  const badge = el('badge');
  badge.textContent = d.stateLabel;
  badge.className = 'badge ' + d.stateClass;

  let sub;
  if (d.fault) {
    sub = '⚠ ' + d.fault;
  } else if (d.state === 'REST') {
    sub = 'Przerwa po dogrzaniu — kolejny pomiar za ' + mmss(d.restRemaining) + '.';
  } else if (!d.enabled) {
    sub = 'Termostat wyłączony — pomiar bez sterowania matą.';
  } else if (d.hasReading) {
    sub = 'Pomiar ' + d.tempAge + ' s temu · kolejny za ' + Math.max(0, d.nextMeasure) + ' s.';
  } else {
    sub = 'Czekam na pierwszy odczyt czujnika…';
  }
  el('sub').textContent = sub;

  if (!dirty) fillForm(d);

  el('foot').innerHTML = 'IP ' + d.ip + ' · WiFi ' + d.rssi + ' dBm · działa ' +
    Math.floor(d.uptime / 3600) + ' h ' + Math.floor((d.uptime % 3600) / 60) + ' min';
}

async function refresh(){
  try {
    const r = await fetch('/api/status', {cache: 'no-store'});
    render(await r.json());
  } catch (e) {
    el('sub').textContent = 'Brak połączenia z modułem…';
  }
}

form.addEventListener('input', () => { dirty = true; });

document.querySelectorAll('.stepper button').forEach(b => {
  b.addEventListener('click', () => {
    const i = el('setpoint');
    const v = (parseFloat(i.value) || 0) + parseFloat(b.dataset.step);
    i.value = Math.min(40, Math.max(10, v)).toFixed(1);
    dirty = true;
  });
});

form.addEventListener('submit', async ev => {
  ev.preventDefault();
  const body = new URLSearchParams({
    setpoint: el('setpoint').value,
    hysteresis: el('hysteresis').value,
    rest: el('rest').value,
    enabled: el('enabled').checked ? '1' : '0'
  });
  try {
    const r = await fetch('/api/settings', {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body
    });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const d = await r.json();
    dirty = false;
    fillForm(d);
    render(d);
    message('Zapisano ✓', false);
  } catch (e) {
    message('Nie udało się zapisać nastaw', true);
  }
});

refresh();
setInterval(refresh, 2000);
</script>
</body>
</html>
)rawliteral";
