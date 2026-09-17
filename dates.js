/* ISO-week dates for VLA Radar. Pure UTC arithmetic; never invent a day for month-only metadata. */
(function (root, factory) {
  'use strict';
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.RadarDates = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const DAY = 86400000;
  function exactDate(value) {
    if (typeof value !== 'string' || !/^[1-9]\d{3}-\d{2}-\d{2}$/.test(value)) return null;
    const [year, month, day] = value.split('-').map(Number);
    const date = new Date(Date.UTC(year, month - 1, day));
    return date.getUTCFullYear() === year && date.getUTCMonth() === month - 1 && date.getUTCDate() === day ? date : null;
  }
  const format = date => date.toISOString().split('T')[0];
  function isoWeek(value) {
    const date = exactDate(value);
    if (!date) return null;
    const weekday = date.getUTCDay() || 7;
    const start = new Date(date.getTime() - (weekday - 1) * DAY);
    const thursday = new Date(start.getTime() + 3 * DAY);
    const year = thursday.getUTCFullYear();
    const week = Math.ceil(((thursday.getTime() - Date.UTC(year, 0, 1)) / DAY + 1) / 7);
    return { year: String(year), week, key: `${year}-W${String(week).padStart(2, '0')}`, start: format(start), end: format(new Date(start.getTime() + 6 * DAY)) };
  }
  function fromKey(key) {
    if (typeof key !== 'string' || !/^[1-9]\d{3}-W(?:0[1-9]|[1-4]\d|5[0-3])$/.test(key)) return null;
    const year = Number(key.slice(0, 4)), week = Number(key.slice(6));
    const jan4 = new Date(Date.UTC(year, 0, 4));
    const firstMonday = jan4.getTime() - ((jan4.getUTCDay() || 7) - 1) * DAY;
    // Validate by the in-year Thursday, including boundary years such as 1000.
    const thursday = new Date(firstMonday + ((week - 1) * 7 + 3) * DAY);
    const result = isoWeek(format(thursday));
    return result && result.key === key ? result : null;
  }
  function yearOf(value) {
    const week = isoWeek(value);
    if (week) return week.year;
    if (typeof value === 'string' && /^[1-9]\d{3}-(0[1-9]|1[0-2])$/.test(value)) return value.slice(0, 4);
    return '';
  }
  function weeksInYear(year) {
    if (!/^[1-9]\d{3}$/.test(String(year))) return [];
    const count = isoWeek(`${year}-12-28`).week;
    return Array.from({ length: count }, (_, i) => fromKey(`${year}-W${String(i + 1).padStart(2, '0')}`));
  }
  function label(key, compact = false) {
    const info = fromKey(key);
    if (!info) return '日期未精确到日';
    const range = compact && info.start.slice(0, 4) === info.end.slice(0, 4) ? `${info.start.slice(5)}—${info.end.slice(5)}` : `${info.start}—${info.end}`;
    return `${info.key} · ${range}`;
  }
  return Object.freeze({ exactDate, isoWeek, fromKey, yearOf, weeksInYear, label });
});
