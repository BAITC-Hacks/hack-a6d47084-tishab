import test from "node:test";
import assert from "node:assert/strict";
import { formatDate, formatNumber, languages, messages, normalizeLanguage, translate } from "./messages.js";

test("all UI messages have Russian and Kazakh translations with matching placeholders", () => {
  const placeholders = (text) => [...text.matchAll(/\{(\w+)\}/g)].map((match) => match[1]).sort();
  for (const [key, entry] of Object.entries(messages)) {
    for (const language of ["ru", "kk"]) {
      assert.ok(entry[language]?.trim(), `${language}: ${key}`);
      assert.deepEqual(placeholders(entry[language]), placeholders(key), key);
    }
  }
});

test("all three languages translate titles, statuses and demo messages", () => {
  assert.equal(translate("en", "Wind power forecast"), "Wind power forecast");
  assert.equal(translate("ru", "Wind power forecast"), "Прогноз ветровой выработки");
  assert.equal(translate("kk", "Wind power forecast"), "Жел энергиясының болжамы");
  assert.equal(translate("ru", "BLOCKED"), "ЗАБЛОКИРОВАНО");
  assert.equal(translate("kk", "Demo forecast accepted."), "Демо болжам қабылданды.");
});

test("parameters are substituted without changing source API identifiers", () => {
  assert.equal(translate("kk", "{hours}-hour forecast", { hours: 48 }), "48 сағатқа болжам");
  assert.equal(translate("ru", "Request failed ({status})", { status: 503 }), "Ошибка запроса (503)");
  assert.equal(translate("ru", "F-6C0B032E95"), "F-6C0B032E95");
  assert.equal(translate("kk", "Unknown provider response"), "Unknown provider response");
  assert.equal(translate("ru", null), "");
});

test("only supported saved language codes are accepted", () => {
  for (const { code } of languages) assert.equal(normalizeLanguage(code), code);
  for (const value of [null, "", "fr", "__proto__"]) assert.equal(normalizeLanguage(value), "en");
});

test("dates and numbers respect locale and handle missing values", () => {
  assert.equal(formatNumber("en", 1.363), "1.363");
  assert.equal(formatNumber("ru", 1.363), "1,363");
  assert.equal(formatNumber("kk", 1.363), "1,363");
  assert.equal(formatNumber("ru", 0), "0");
  assert.equal(formatNumber("kk", null), "Деректер жоқ");
  const options = { day: "2-digit", month: "long", timeZone: "UTC" };
  assert.match(formatDate("ru", "2026-02-10T06:00:00Z", options), /феврал/);
  assert.match(formatDate("kk", "2026-02-10T06:00:00Z", options), /ақпан/);
  assert.equal(formatDate("ru", "invalid"), "Нет данных");
  assert.equal(formatDate("kk", null), "Деректер жоқ");
});
