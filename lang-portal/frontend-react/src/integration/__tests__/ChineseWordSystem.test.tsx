// Jiantizi adaption for Bootcamp Week 1:
// Test system integration

import { render, fireEvent } from '@testing-library/react';
import { PinyinInput } from '../../components/PinyinInput';
import { ChineseWord } from '../../components/ChineseWord';
import { addToneMarks } from '../../utils/pinyinUtils';

describe('Chinese Word System', () => {
  test('complete workflow from input to display', () => {
    const handlePinyinChange = jest.fn();
    const { getByPlaceholderText, getByText } = render(
      <>
        <PinyinInput onChange={handlePinyinChange} />
        <ChineseWord 
          jiantizi="学习"
          pinyin="xué xí"
          english="to study"
        />
      </>
    );

    const input = getByPlaceholderText('Enter pinyin with numbers (e.g., ni3 hao3)');
    fireEvent.change(input, { target: { value: 'xue2 xi2' } });

    // Split the input and convert each syllable separately
    const syllables = 'xue2 xi2'.split(' ');
    const expectedPinyin = syllables
      .map(s => {
        const tone = parseInt(s.slice(-1));
        const base = s.slice(0, -1);
        return addToneMarks(base, tone);
      })
      .join(' ');

    expect(handlePinyinChange).toHaveBeenCalledWith(expectedPinyin);
    expect(getByText('学习')).toBeInTheDocument();
    expect(getByText('xué xí')).toBeInTheDocument();
    expect(getByText('to study')).toBeInTheDocument();
  });
}); 