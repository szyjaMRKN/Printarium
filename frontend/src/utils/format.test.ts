import { describe, expect, it } from 'vitest';
import { formatDate, formatMoney, formatPercent, parseAmountToGrosze } from './format';

describe('formatowanie kwot i dat', () => {
  it('formatuje grosze jako kwotę w złotych', () => {
    expect(formatMoney(1081350).replace(/ /g, ' ')).toBe('10 813,50 zł');
    expect(formatMoney(0).replace(/ /g, ' ')).toBe('0,00 zł');
  });

  it('zamienia tekst na grosze bez błędów zaokrągleń', () => {
    expect(parseAmountToGrosze('10 813,50')).toBe(1081350);
    expect(parseAmountToGrosze('0,1')).toBe(10);
    expect(parseAmountToGrosze('12.34')).toBe(1234);
    expect(parseAmountToGrosze('abc')).toBeNull();
    expect(parseAmountToGrosze('1,234')).toBeNull();
  });

  it('formatuje datę w układzie DD.MM.RRRR', () => {
    expect(formatDate('2026-09-18')).toBe('18.09.2026');
    expect(formatDate(null)).toBe('—');
  });

  it('formatuje procent wykorzystania limitu', () => {
    expect(formatPercent(72.59)).toBe('72,6%');
  });
});
