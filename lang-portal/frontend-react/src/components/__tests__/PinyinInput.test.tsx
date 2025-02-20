// Jiantizi adaption for Bootcamp Week 1:
// Test pinyin input component

import { render, fireEvent } from '@testing-library/react';
import { PinyinInput } from '../PinyinInput';

describe('PinyinInput', () => {
  test('converts numbered pinyin to tone marks', () => {
    const handleChange = jest.fn();
    const { getByPlaceholderText } = render(
      <PinyinInput onChange={handleChange} />
    );

    const input = getByPlaceholderText('Enter pinyin with numbers (e.g., ni3 hao3)');
    fireEvent.change(input, { target: { value: 'ni3 hao3' } });

    expect(handleChange).toHaveBeenCalledWith('nǐ hǎo');
  });

  test('handles multiple vowels correctly', () => {
    const handleChange = jest.fn();
    const { getByPlaceholderText } = render(
      <PinyinInput onChange={handleChange} />
    );

    const input = getByPlaceholderText('Enter pinyin with numbers (e.g., ni3 hao3)');
    fireEvent.change(input, { target: { value: 'xiao3' } });

    expect(handleChange).toHaveBeenCalledWith('xiǎo');
  });

  test('preserves input without tone numbers', () => {
    const handleChange = jest.fn();
    const { getByPlaceholderText } = render(
      <PinyinInput onChange={handleChange} />
    );

    const input = getByPlaceholderText('Enter pinyin with numbers (e.g., ni3 hao3)');
    fireEvent.change(input, { target: { value: 'de' } });

    expect(handleChange).toHaveBeenCalledWith('de');
  });
}); 