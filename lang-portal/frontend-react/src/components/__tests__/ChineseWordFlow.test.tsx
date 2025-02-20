// Jiantizi adaption for Bootcamp Week 1:
// Test component flow

import { render, fireEvent } from '@testing-library/react';
import { PinyinInput } from '../PinyinInput';
import { ChineseWord } from '../ChineseWord';

describe('Chinese Word Flow', () => {
  test('complete workflow from input to display', () => {
    const { getByPlaceholderText, getByText } = render(
      <>
        <PinyinInput onChange={() => {}} />
        <ChineseWord 
          jiantizi="学习"
          pinyin="xué xí"
          english="to study"
        />
      </>
    );

    const input = getByPlaceholderText('Enter pinyin with numbers (e.g., ni3 hao3)');
    fireEvent.change(input, { target: { value: 'xue2 xi2' } });

    expect(getByText('学习')).toBeInTheDocument();
    expect(getByText('xué xí')).toBeInTheDocument();
    expect(getByText('to study')).toBeInTheDocument();
  });
}); 