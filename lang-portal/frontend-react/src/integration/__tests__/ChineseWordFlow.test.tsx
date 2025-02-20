import { render, fireEvent } from '@testing-library/react';
import { PinyinInput } from '../../components/PinyinInput';
import { ChineseWord } from '../../components/ChineseWord';

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

  test('handles multiple words', () => {
    const { getByPlaceholderText, getAllByText } = render(
      <>
        <PinyinInput onChange={() => {}} />
        <ChineseWord jiantizi="你好" pinyin="nǐ hǎo" english="hello" />
        <ChineseWord jiantizi="学习" pinyin="xué xí" english="to study" />
      </>
    );

    const input = getByPlaceholderText('Enter pinyin with numbers (e.g., ni3 hao3)');
    fireEvent.change(input, { target: { value: 'ni3 hao3' } });

    expect(getAllByText(/[你好学习]/)).toHaveLength(2);
  });
}); 