// Jiantizi adaption for Bootcamp Week 1:
// Add tests for pinyin tone mark handling

import { addToneMarks, removeToneMarks } from '../pinyinUtils';

describe('pinyinUtils', () => {
  describe('addToneMarks', () => {
    test('adds correct tone marks to single vowels', () => {
      expect(addToneMarks('ni', 3)).toBe('nǐ');
      expect(addToneMarks('ma', 1)).toBe('mā');
    });

    test('handles multiple vowels correctly', () => {
      expect(addToneMarks('xiao', 3)).toBe('xiǎo');
      expect(addToneMarks('jian', 4)).toBe('jiàn');
    });

    test('handles ü correctly', () => {
      expect(addToneMarks('nü', 3)).toBe('nǚ');
      expect(addToneMarks('lü', 4)).toBe('lǜ');
    });

    test('handles invalid tone numbers', () => {
      expect(addToneMarks('ni', 0)).toBe('ni');
      expect(addToneMarks('ni', 5)).toBe('ni');
    });
  });

  describe('removeToneMarks', () => {
    test('removes tone marks correctly', () => {
      expect(removeToneMarks('nǐ')).toBe('ni');
      expect(removeToneMarks('xiǎo')).toBe('xiao');
    });

    test('handles text without tone marks', () => {
      expect(removeToneMarks('ni')).toBe('ni');
      expect(removeToneMarks('xiao')).toBe('xiao');
    });

    test('handles ü', () => {
      expect(removeToneMarks('nǚ')).toBe('nü');
      expect(removeToneMarks('lǜ')).toBe('lü');
    });
  });
}); 